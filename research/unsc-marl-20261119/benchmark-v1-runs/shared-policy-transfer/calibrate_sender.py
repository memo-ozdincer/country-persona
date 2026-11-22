"""Fit sender delivery values on a small randomized target log."""
import argparse
from hashlib import sha256
import json

import numpy as np

from transfer_team import HERE, RUNS, base

EPISODES = 128
SEED = base.SEED + 43
DELIVERY = 0.75


def plan():
    paths = (HERE / "calibrate_sender.py", HERE / "calibration.md", HERE / "plan.json", HERE / "results.json")
    return {
        "episodes": EPISODES, "seed": SEED, "delivery": DELIVERY,
        "sha256": {str(p.relative_to(RUNS)): sha256(p.read_bytes()).hexdigest() for p in paths},
    }


def learn(table, target, reply, draws):
    public, first_only, last_only, both, observed = table
    view, send, first_transport, reply_delivery = draws
    first_delivery = send & first_transport
    chosen = reply[np.where(first_delivery, observed[target, view], 0)]
    release = np.where(first_delivery, np.where(reply_delivery, both[target, view, chosen], first_only[target, view]),
                       np.where(reply_delivery, last_only[target, chosen], public[target]))
    inputs = np.column_stack((first_only[target] - public[target], observed[target] == 2)).astype(int)
    log = [{"coverage": int(inputs[v, 0]), "supports": bool(inputs[v, 1]), "sent": bool(s),
            "first_arrived": bool(f), "reply_arrived": bool(r),
            "reply": int(a), "release": int(p)}
           for v, s, f, r, a, p in zip(view, send, first_delivery, reply_delivery, chosen, release, strict=True)]
    values = np.empty((3, 2))
    counts = []
    for j in range(2):
        missing = release[~first_delivery & (reply_delivery == j)]
        assert len(missing)
        for k, features in enumerate(inputs):
            same_input = (inputs[view] == features).all(axis=1)
            arrived = release[first_delivery & same_input & (reply_delivery == j)]
            # An unobserved cell leaves no evidence for a forwarding benefit.
            values[k, j] = arrived.mean() - missing.mean() if len(arrived) else 0
            counts.append({"features": features.tolist(), "reply_arrived": bool(j),
                           "arrived_n": len(arrived), "absent_n": len(missing)})
    return log, values, counts


def run():
    assert plan() == base.read(HERE / "calibration-plan.json")
    public, first_only, last_only, both, observed = table = base.tables()
    original = base.read(HERE / "results.json")
    rng = np.random.default_rng(SEED)
    draws = (rng.integers(3, size=EPISODES), rng.random(EPISODES) < 0.5,
             rng.random(EPISODES) < DELIVERY, rng.random(EPISODES) < DELIVERY)
    all_rows = {}
    for key, prior in original.items():
        target = int(key.endswith("_to_afghanistan"))
        reply = np.asarray(prior["receiver_choices"]["frozen"])
        log, values, counts = learn(table, target, reply, draws)
        rows = []
        for cell in prior["held"]:
            q0, q1, price = (cell[k] for k in ("q_first", "q_reply", "price"))
            send = q0 * (values @ [1 - q1, q1]) > price
            missing = (1 - q1) * public[target] + q1 * last_only[target, reply[0]]
            present = (1 - q1) * first_only[target] + q1 * both[target, np.arange(3), reply[observed[target]]]
            actual = missing + np.asarray(cell["private_prior"]) @ (send * (q0 * (present - missing) - price))
            oracle = cell["policies"]["best_sender_frozen_receiver"]["utility"]
            assert actual <= oracle + 1e-8
            rows.append({"q_first": q0, "q_reply": q1, "price": price, "private_prior": cell["private_prior"],
                         "send": send.astype(int).tolist(), "utility": round(float(actual), 8), "oracle": oracle})
        all_rows[key] = {"log": log, "cell_counts": counts, "fitted_arrival_gains": values.tolist(),
                         "held_mean_utility": round(float(np.mean([r["utility"] for r in rows])), 8),
                         "oracle_matches": sum(r["utility"] == r["oracle"] for r in rows), "held": rows}
    return all_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan() if args.plan else run(), indent=2))
