"""Learn reply-conditional sender values and integrate new partner policies."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
PRIOR = RUNS / "shared-policy-transfer"
sys.path.insert(0, str(PRIOR))
import calibrate_sender as previous

base = previous.base
PROFILES = {
    "claim_reader": (0.0, 0.0, 1.0),
    "always_fund": (0.0, 0.0, 0.0),
    "always_process": (1.0, 1.0, 1.0),
    "reversed_reader": (1.0, 1.0, 0.0),
    "claim_reader_75_fund_25": (0.0, 0.0, 0.75),
    "claim_reader_25_reversed_75": (0.75, 0.75, 0.25),
}
PROBES = 8
SEED = previous.SEED


def plan():
    assert previous.plan() == base.read(PRIOR / "calibration-plan.json")
    paths = (Path(__file__), HERE / "protocol.md", PRIOR / "calibration.json", PRIOR / "calibration-plan.json")
    return {
        "episodes": previous.EPISODES, "seed": SEED, "delivery": previous.DELIVERY,
        "profiles": {k: list(v) for k, v in PROFILES.items()}, "probes_per_observation": PROBES,
        "sha256": {str(p.relative_to(RUNS)): sha256(p.read_bytes()).hexdigest() for p in paths},
    }


def collect(table, docket, draws):
    public, first_only, last_only, both, witnessed = table
    view, sent, f_transport, r_transport, process = draws
    first = sent & f_transport
    received = np.where(r_transport, 1 + process, 0)
    score = np.where(first, np.where(r_transport, both[docket, view, process], first_only[docket, view]),
                     np.where(r_transport, last_only[docket, process], public[docket]))
    keys = np.column_stack((first_only[docket] - public[docket], witnessed[docket] == 2)).astype(int)
    trace = [
        {"coverage": int(keys[v, 0]), "supports": bool(keys[v, 1]), "sent": bool(s), "first_arrived": bool(f),
         "received_reply": ("neither", "fund", "process")[r], "score": int(p)}
        for v, s, f, r, p in zip(view, sent, first, received, score, strict=True)
    ]
    return first, received, score, keys, view, trace


def fit(log, pooled):
    first, received, score, keys, view, _ = log
    state = np.minimum(received, 1) if pooled else received
    cols = 2 if pooled else 3
    absent = np.zeros(cols)
    gain = np.zeros((3, cols))
    support = []
    for wire in range(cols):
        baseline = score[~first & (state == wire)]
        assert len(baseline)
        absent[wire] = baseline.mean()
        for i, features in enumerate(keys):
            mask = (keys[view] == features).all(axis=1)
            present = score[first & mask & (state == wire)]
            if len(present):
                gain[i, wire] = present.mean() - absent[wire]
            support.append({"sender_features": features.tolist(), "reply_state": wire,
                            "available": len(present), "baseline": len(baseline)})
    return absent, gain + absent, support


def actual(table, docket):
    public, first_only, last_only, both, _ = table
    return np.r_[public[docket], last_only[docket]], np.column_stack([first_only[docket], both[docket]])


def marginal_gain(absent, present, obs, profile, q_reply):
    p = np.asarray(profile)
    missing = (1 - q_reply) * absent[0] + q_reply * ((1 - p[0]) * absent[1] + p[0] * absent[2])
    arrives = (1 - q_reply) * present[:, 0] + q_reply * (
        (1 - p[obs]) * present[:, 1] + p[obs] * present[:, 2]
    )
    return missing, arrives - missing


def evaluate(table, docket, fits, probe_uniforms):
    legacy, pooled, known = fits
    outputs = []
    baseline, both = actual(table, docket)
    obs = table[-1][docket]
    for name, profile in PROFILES.items():
        estimated = np.mean(probe_uniforms < np.asarray(profile)[:, None], axis=1)
        for q0, q1, price, prior in product(base.TEST_DELIVERY, base.TEST_DELIVERY, base.TEST_PRICES, base.TEST_PRIORS):
            absence, true_gain = marginal_gain(baseline, both, obs, profile, q1)
            _, known_gain = marginal_gain(known[0], known[1], obs, profile, q1)
            _, probe_gain = marginal_gain(known[0], known[1], obs, estimated, q1)
            mass = np.array(prior)
            values = {
                "legacy_fixed_reader": legacy @ [1 - q1, q1],
                "pooled_same_log": (pooled[1] - pooled[0]) @ [1 - q1, q1],
                "reply_conditioned_declared": known_gain,
                "reply_conditioned_with_probes": probe_gain,
                "oracle": true_gain,
            }
            row = {}
            for policy, gain in values.items():
                send = q0 * gain > price
                release = absence + mass @ (send * q0 * true_gain)
                cost = float(price * (mass @ send))
                row[policy] = {"utility": round(float(release - cost), 8), "release": round(float(release), 8),
                               "cost": round(cost, 8), "send": send.astype(int).tolist()}
            assert all(r["utility"] <= row["oracle"]["utility"] + 1e-8 for r in row.values())
            outputs.append({"partner": name, "true_profile": list(profile), "estimated_profile": estimated.tolist(),
                            "q_first": q0, "q_reply": q1, "price": price, "private_prior": prior, "policies": row})
    return outputs


def summarize(rows):
    return {policy: {
        **{field: round(float(np.mean([r["policies"][policy][field] for r in rows])), 8)
           for field in ("utility", "release", "cost")},
        "matches": sum(r["policies"][policy]["utility"] == r["policies"]["oracle"]["utility"] for r in rows),
        "mean_regret": round(float(np.mean([r["policies"]["oracle"]["utility"] -
                                           r["policies"][policy]["utility"] for r in rows])), 8),
        "n": len(rows),
    } for policy in rows[0]["policies"]}


def run():
    assert plan() == base.read(HERE / "plan.json")
    table = base.tables()
    n = previous.EPISODES
    rng = np.random.default_rng(SEED)
    draws = (rng.integers(3, size=n), rng.random(n) < 0.5,
             rng.random(n) < previous.DELIVERY, rng.random(n) < previous.DELIVERY,
             (rng.random(n) < 0.5).astype(int))
    probes = rng.random((3, PROBES))
    original = base.read(PRIOR / "calibration.json")
    results, complete_grid = {}, []
    for docket, family in enumerate(base.PRIVATE):
        log = collect(table, docket, draws)
        pooled, known = (fit(log, v) for v in (True, False))
        legacy_key = next(k for k in original if k.endswith("_to_" + family))
        legacy = np.array(original[legacy_key]["fitted_arrival_gains"])
        rows = evaluate(table, docket, (legacy, pooled, known), probes)
        complete_grid.extend(rows)
        results[family] = {"exploration": log[-1], "reply_conditioned_cells": known[2], "pooled_cells": pooled[2],
                           "estimated_absent": known[0].tolist(), "estimated_present": known[1].tolist(),
                           "summary": summarize(rows), "held": rows}
    return {"overall": summarize(complete_grid),
            "by_partner": {name: summarize([r for r in complete_grid if r["partner"] == name])
                           for name in PROFILES}, "dockets": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan() if args.plan else run(), indent=2))
