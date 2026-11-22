"""Audit whether the existing action features can express the 2553 ceiling."""
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

import listener_fit as experiment

reform, receipt = experiment.reform, experiment.receipt
TOL = 1e-9
PLANS = tuple(product(range(2), repeat=4))


def private_third(scene, local, edges, share, rate):
    features = scene["open"][2].copy()
    prior = experiment.old.softmax(local[1] / 3)
    shares = (share, 1-share)
    for i, early, j, c, points in edges:
        if (i, j) == (1, 2):
            features[c, 1:] += points * rate * (shares[early] - np.array([.5, prior[early]])) / 7
    return features


def conditions():
    previous = json.loads((experiment.HERE / "results.json").read_text())
    references = {(x["order"], x["delivery"], x["private_prior"]): x for x in previous["transfer_rows"]}
    entries = []
    for order, indices in reform.ORDERS.items():
        _, local, edges, _, records = reform.setup(indices)
        for rate, share in product(reform.RATES, reform.SHARES):
            scene = receipt.features(reform.COUNTS, reform.CAPS, local, edges, (rate,) * 3, records)
            third = private_third(scene, local, edges, share, rate)
            views = np.concatenate((scene["adaptive"], third[None, ...]), axis=0)
            values = np.array([sum((share if card == 0 else 1-share) *
                                   rate ** mask.bit_count() * (1-rate) ** (3-mask.bit_count()) *
                                   records[plan[card+1 if mask & 2 else 0], card, plan[-1]][mask]
                                   for card, mask in product(range(2), range(8))) for plan in PLANS])
            ref = references[order, rate, share]
            assert abs(values.max() - ref["scores"]["content_ceiling"]) <= TOL
            for arm, (team, late, mode) in experiment.arms(
                    np.asarray(previous["control_trace"]["checkpoints"]["150"]["weights"]),
                    fitted(previous)).items():
                if mode == "open":
                    continue
                replayed = list(np.argmax(views[:3] @ late, axis=1)) + [int(np.argmax(third @ team))]
                assert replayed == ref["actions"][arm]["later"] + [ref["actions"][arm]["third"]]
            entries.append((order, rate, share, views, values))
    return entries


def fitted(previous):
    last = previous["fit_trace"]["checkpoints"]["150"]
    team = np.asarray(last["weights"])
    return team, team + last["listener_residual"]


def fit_margins(rows):
    from scipy.optimize import linprog

    if not rows:
        return {"weights": [0., 0., 0.], "margin": 1.}
    x = np.stack([np.append(delta, float(action == 1)) for delta, action in rows])
    result = linprog([0, 0, 0, -1], A_ub=x, b_ub=np.zeros(len(x)),
                     bounds=[(-1, 1)] * 3 + [(0, 1)], method="highs")
    assert result.success
    return {"weights": result.x[:3].tolist(), "margin": float(result.x[-1])}


def run():
    entries = conditions()
    constraints, independent = {"listener": [], "third": []}, {}
    ambiguous = 0
    for order, rate, share, menus, values in entries:
        ideal = np.asarray(PLANS)[values >= values.max()-TOL]
        for index, options in enumerate(ideal.T):
            if options.min() != options.max():
                ambiguous += 1
                continue
            desk = "third" if index == 3 else "listener"
            wanted = int(options[0])
            pair = (menus[index, 1-wanted]-menus[index, wanted], wanted)
            constraints[desk].append(pair)
            independent.setdefault(f"{order}_{desk}", []).append(pair)
    per_desk = {desk: fit_margins(rows) for desk, rows in constraints.items()}
    per_order = {key: fit_margins(rows) for key, rows in independent.items()}
    shared = fit_margins(constraints["listener"] + constraints["third"])
    outcomes = []
    for order, rate, share, menus, values in entries:
        row = {"order": order, "delivery": rate, "private_prior": share, "optimal_plans": [
            option for option, value in zip(PLANS, values, strict=True) if value >= values.max()-TOL]}
        weights = {
            "shared": np.tile(shared["weights"], (4, 1)),
            "desk": np.array([per_desk["listener"]["weights"]] * 3 + [per_desk["third"]["weights"]]),
            "order_desk": np.array([per_order[f"{order}_listener"]["weights"]] * 3 +
                                   [per_order[f"{order}_third"]["weights"]]),
        }
        row["deterministic_gap"] = {
            key: float(values.max() - values[PLANS.index(tuple(np.argmax(
                np.einsum("oaf,of->oa", menus, vectors), axis=1)))])
            for key, vectors in weights.items()}
        outcomes.append(row)
    previous = json.loads((experiment.HERE / "results.json").read_text())
    controls = {
        "2553_witness": np.asarray(shared["weights"]),
        "2553_witness_scaled": np.asarray(shared["weights"]) *
            previous["control_trace"]["checkpoints"]["150"]["weights"][0],
        "sampled_shared": np.asarray(previous["control_trace"]["checkpoints"]["150"]["weights"]),
        "fixed": experiment.FIXED,
    }
    synthetic = {}
    for label, seed, count in (
            ("train", experiment.old.TRAIN_SEED, experiment.old.TRAIN_N),
            ("fresh", experiment.FRESH_SEED, experiment.FRESH_COUNT)):
        cases = receipt.cases(seed, count)
        synthetic[label] = {
            key: {"greedy": float(np.mean([receipt.outcome(s, receipt.run_policy(s, w, "adaptive")) for s in cases])),
                  "stochastic": float(np.mean([receipt.expected(s, w)[0] for s in cases]))}
            for key, w in controls.items()
        }
    return {"ambiguous_decisions": ambiguous, "constraints": {key: len(rows) for key, rows in constraints.items()},
            "shared": shared, "desk": per_desk, "order_desk": per_order, "rows": outcomes, "synthetic": synthetic,
            "pins": {p.name: experiment.old.DIGEST(p) for p in (
                Path(__file__), experiment.HERE / "representation-protocol.md",
                experiment.HERE / "results.json", experiment.HERE / "plan.json")}}

if __name__ == "__main__":
    sys.path.append(sys.argv[1])
    print(json.dumps(run(), indent=2))
