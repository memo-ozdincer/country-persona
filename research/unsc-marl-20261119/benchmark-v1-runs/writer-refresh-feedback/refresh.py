"""Refresh passage values using screened single-trajectory feedback."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
PARENT = RUNS / "terminal-feedback-routing"
fit = SimpleNamespace(**runpy.run_path(str(PARENT / "fit.py")))
CONTEXTS = ("compact", "topic")
ARCHIVES = {
    "compact": RUNS / "delisting-witness-render/compact-results.json",
    "topic": RUNS / "delisting-focused-writer/results.json",
}
CALIBRATION = RUNS / "writer-change-calibration/results.json"
PHASES = {"compact": (1., 0.), "topic": (0., 1.), "mixed": (.5, .5)}
CHECKPOINTS = (0, 8, 16, 32, 64, 128)


def read(path):
    return json.loads(path.read_text())


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def plan():
    paths = (
        Path(__file__), HERE / "protocol.md", PARENT / "fit.py", PARENT / "plan.json",
        PARENT / "results.json", CALIBRATION, *ARCHIVES.values(),
    )
    baseline = fit.plan()
    return {
        "pins": {str(p.relative_to(RUNS)): sha256(p.read_bytes()).hexdigest() for p in paths},
        "seed": baseline["seed"], "training": baseline["train"], "held": baseline["held"],
        "exploration": baseline["exploration"], "phases": list(PHASES.items()),
        "checkpoints": list(CHECKPOINTS), "review_fees": [0, 1, 5],
        "exploration_windows": {"continuous": 128, "bounded": 32},
    }


def prepare():
    data, joined = fit.prior.environment()
    base = fit.receipt_bank(data, np.full((3, 2), 52))
    keys = [f"{early}/{late}" for early, late in product(data["views"], data["docs"])]
    approved = read(CALIBRATION)["prior"]["licensed"]
    assert len(approved) == 2 and set(approved) <= set(keys)
    records = {}
    for writer, path in ARCHIVES.items():
        current = []
        for key in keys:
            record = read(path)["compiled"][key]
            assert record["scores"]["standalone"] == 52
            current.append({
                "id": digest([key, record["prefix"], record["ungated_record"]]),
                "pair": key,
                "score": record["scores"]["ungated"],
            } if key in approved and record["candidate"] else None)
        records[writer] = current
    assert len({r["id"] for rows in records.values() for r in rows if r}) == 4
    assert sum(joined["compact_ungated"].ravel() == 70) == 2
    return data, base, records


def bank(base, records, probabilities, cache):
    outcomes = []
    for writer in CONTEXTS:
        values = base.copy()
        for key, candidate in enumerate(records[writer], 6):
            if candidate and candidate["id"] in cache:
                values[key] = cache[candidate["id"]]
        outcomes.append(values)
    return probabilities @ np.array(outcomes)


def stale_bank(base, records, probabilities):
    return bank(base, records, probabilities, {
        row["id"]: row["score"] for candidates in records.values() for row in candidates if row
    })


def evaluate(spec, base, records, probabilities, observed, estimate, cache, frozen):
    released = bank(base, records, probabilities, cache)
    ideal_cache = {r["id"]: max(52, r["score"]) for rows in records.values() for r in rows if r}
    ideal = bank(base, records, probabilities, ideal_cache)
    stale = stale_bank(base, records, probabilities)
    failures = np.array(probabilities) @ np.array([
        [False] * 6 + [bool(r and r["score"] == 0) for r in records[w]] for w in CONTEXTS
    ])
    held = spec["held"]
    values = []
    for q0, q1, price, mass in product(held["delivery"], held["delivery"], held["prices"], held["priors"]):
        setting = q0, q1, price, np.array(mass)
        routes = {
            "refresh": (released, fit.best_route(estimate, observed, setting)),
            "reviewed_oracle": (ideal, fit.best_route(ideal, observed, setting)),
            "source_only": (base, fit.best_route(base, observed, setting)),
            "stale_pair_approval": (stale, fit.frozen_route(frozen, observed, setting)),
        }
        row = {}
        for name, (table, (sender, reply)) in routes.items():
            utility, release, cost, *_ = fit.pay(table, observed, setting, sender, reply)
            selected = 6 + 2 * np.arange(3) + reply[observed]
            zero_release = (mass * sender * q0 * q1) @ failures[selected] if name == "stale_pair_approval" else 0.
            row[name] = [float(utility), float(release), float(cost), float(zero_release)]
        assert row["refresh"][0] <= row["reviewed_oracle"][0] + 1e-9
        values.append(row)
    return {key: dict(zip(("utility", "release", "send_cost", "zero_release_pair"),
                          np.mean([row[key] for row in values], axis=0).round(8), strict=True))
            for key in values[0]}


def train(spec, data, base, records, peer, explore_until):
    rng = np.random.default_rng(spec["seed"])
    observed = fit.view_observations(data, peer)
    arm = "peer" if peer else "independent"
    old = read(PARENT / "results.json")["fits"][f"receipt_value/{arm}"]["checkpoints"]["256"]
    cache = {}
    phases = {}
    for name, weights in spec["phases"]:
        probabilities = np.array(weights)
        estimate = base.copy()
        exploration_value = base.copy()
        for key, candidates in enumerate(zip(*records.values(), strict=True), 6):
            if any(candidates):
                exploration_value[key] = 70
        totals = np.zeros_like(base)
        counts = np.zeros(len(base), dtype=int)
        checkpoints = {}
        trace = []
        for step in range(1 + max(spec["checkpoints"])):
            if step in spec["checkpoints"]:
                online = sum(row["released"] - row["send_fee"] for row in trace)
                source_only = sum(row["matched_source_net"] for row in trace)
                review_count = sum(row["reviewed_now"] for row in trace)
                checkpoints[step] = {
                    "counts": counts.tolist(), "estimates": estimate.tolist(),
                    "review_count": review_count,
                    "source_only_matched_net_per_episode": round(source_only / step, 8) if step else None,
                    "online_difference_by_review_fee": {
                        str(fee): round((online - source_only - fee * review_count) / step, 8) if step else None
                        for fee in spec["review_fees"]
                    },
                    "online_net_per_episode_by_review_fee": {
                        str(fee): round((online - fee * review_count) / step, 8) if step else None
                        for fee in spec["review_fees"]
                    },
                    "held": evaluate(spec, base, records, probabilities, observed, estimate, cache, old),
                }
            if step == max(spec["checkpoints"]):
                break
            q0, q1 = rng.choice(spec["training"]["delivery"], size=2)
            price = int(rng.choice(spec["training"]["prices"]))
            view = int(rng.integers(3))
            send_draw, reply_draw, first_draw, last_draw, explore_draw, writer_draw = rng.random(6)
            writer = CONTEXTS[0] if writer_draw < probabilities[0] else CONTEXTS[1]
            exploring = step < explore_until
            explore = exploring and explore_draw < 0.5
            policy_score = np.where(counts == 0, exploration_value, estimate) if explore else estimate
            setting = q0, q1, price, np.full(3, 1 / 3)
            s, r = fit.best_route(policy_score, observed, setting)
            half = spec["exploration"] / 2 if exploring else 0.
            send = send_draw < (1 - half if s[view] else half)
            first = send and first_draw < q0
            state = observed[view] if first else 0
            reply = int(reply_draw < (1 - half if r[state] else half))
            _, key = fit.rollout(base, view, q0, q1, (first_draw, last_draw), send, reply)
            candidate = records[writer][key - 6] if key >= 6 else None
            released = float(base[key])
            reviewed_now = False
            if candidate:
                ident = candidate["id"]
                if ident in cache:
                    released = cache[ident]
                else:
                    cache[ident] = max(released, candidate["score"])
                    reviewed_now = True
            # Rejected or withheld drafts always have their source-only record available.
            signal = cache[candidate["id"]] if candidate else released
            fallback_send, fallback_reply = fit.best_route(base, observed, setting)
            fallback_state = observed[view] if fallback_send[view] and first_draw < q0 else 0
            fallback_score, _ = fit.rollout(base, view, q0, q1, (first_draw, last_draw),
                                            fallback_send[view], fallback_reply[fallback_state])
            matched_source_net = float(fallback_score - price * fallback_send[view])
            counts[key] += 1
            totals[key] += signal
            estimate[key] = totals[key] / counts[key]
            trace.append({
                "q": [float(q0), float(q1)], "price": price, "view": view,
                "send": bool(send), "reply": reply, "writer": writer,
                "first_received": bool(first), "reply_received": bool(last_draw < q1),
                "receipt": int(key), "released": released,
                "score_signal": signal, "send_fee": price if send else 0,
                "matched_source_net": matched_source_net,
                "delivery_draws": [float(first_draw), float(last_draw)],
                "candidate_id": candidate["id"] if candidate else None,
                "reviewed_now": reviewed_now,
            })
        phases[name] = {"checkpoints": checkpoints, "trace": trace}
    return phases


def run(spec):
    data, base, records = prepare()
    return {"candidates": records, "base": base.tolist(),
            "variants": {name: {arm: train(spec, data, base, records, peer, budget)
                                for arm, peer in fit.CONTENT.items()}
                         for name, budget in spec["exploration_windows"].items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    spec = plan()
    if not args.plan:
        assert json.loads(json.dumps(spec)) == read(HERE / "plan.json")
    print(json.dumps(spec if args.plan else run(spec), indent=2))


if __name__ == "__main__":
    main()
