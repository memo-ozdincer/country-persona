"""Train source selection using documentary returns averaged over receipt masks."""
import argparse
from itertools import combinations, product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import learn_choice as old

RATES = (.35, .55, .75, .95)
SCALES = (0., .5, 1., 1.5, 2., 3.)


def plan():
    pins = (Path(__file__), HERE / "protocol.md", PARENT / "learn_choice.py",
            PARENT / "plan.json", PARENT / "results.json")
    return {"receipt_rates": list(RATES), "common_scale_grid": list(SCALES),
            "sha256": {p.name: old.DIGEST(p) for p in pins}}


def channel(counts, caps, local, edges, delivery):
    choices, actions, _, _ = old.scenario(counts, caps, local, edges)
    membership = [np.array([[card in subset for card in range(n)] for subset in group])
                  for group, n in zip(choices, counts, strict=True)]
    values = [table @ points for table, points in zip(membership, local, strict=True)]
    uniform = [table.mean(0) for table in membership]
    priority = [old.softmax(points / 3) @ table for points, table in zip(values, membership, strict=True)]
    signals = [np.zeros((len(rows), 2)) for rows in choices]
    returns = sum(p * y[actions[:, i]] for i, (p, y) in enumerate(zip(delivery, values, strict=True)))
    for i, a, j, b, w in edges:
        signals[i] += w * delivery[j] * membership[i][:, a, None] * (uniform[j][b], priority[j][b])
        signals[j] += w * delivery[i] * membership[j][:, b, None] * (uniform[i][a], priority[i][a])
        returns += w * delivery[i] * delivery[j] * (membership[i][actions[:, i], a] & membership[j][actions[:, j], b])
    feature = [np.column_stack((local_score, joint)) / 7 for local_score, joint in zip(values, signals, strict=True)]
    return choices, actions, feature, returns


def synthetic(seed, size):
    rng = np.random.default_rng(seed)
    noise = np.random.default_rng(seed + 8000)
    rows = []
    for _ in range(size):
        local = [rng.integers(0, 8, n) for n in old.COUNTS]
        edges = [(i, int(rng.integers(old.COUNTS[i])), j, int(rng.integers(old.COUNTS[j])), int(rng.integers(0, 15)))
                 for i, j in combinations(range(3), 2)]
        args = (old.COUNTS, old.CAPS, local, edges)
        rows.append((channel(*args, noise.choice(RATES, 3)), old.scenario(*args)))
    return rows


def select(sample, weights):
    return tuple(int(np.argmax(features @ weights)) for features in sample[2])


def reward(sample, action):
    i, = np.flatnonzero(np.all(sample[1] == action, axis=1))
    return float(sample[3][i])


def tune(samples):
    scores = []
    for scale in SCALES:
        row = np.array([1., 0., scale])
        scores.append((mean(reward(sample, select(sample, row)) for sample, _ in samples), scale))
    score, scale = max(scores, key=lambda pair: (pair[0], -pair[1]))
    return scale, {str(w): v for v, w in scores}


def compare(sample, full, learned, frozen, scale):
    actions = old.policies(sample, learned)
    actions["old_unadjusted"] = select(full, frozen)
    actions["old_adjusted"] = select(sample, frozen)
    actions["selected_scalar"] = select(sample, np.array([1., 0., scale]))
    return actions


def check_un(learned, frozen, scale):
    results = {}
    for case, counts, caps, local, edges, score in old.un_cases():
        typed = [np.asarray(row) for row in local]
        full = old.scenario(counts, caps, typed, edges)
        choices, actions, _, _ = full
        public = score([rows[0] for rows in choices], 0)
        true = {tuple(ids): [score([choices[i][idx] for i, idx in enumerate(ids)], mask) for mask in range(8)]
                for ids in actions}
        cases = []
        for rate in RATES:
            receipt = [rate ** mask.bit_count() * (1 - rate) ** (3 - mask.bit_count()) for mask in range(8)]
            sample = channel(counts, caps, typed, edges, (rate,) * 3)
            values = {action: sum(y * p for y, p in zip(bank, receipt, strict=True)) for action, bank in true.items()}
            assert all(abs(values[tuple(ids)] - predicted - public) < 1e-9
                       for ids, predicted in zip(sample[1], sample[3], strict=True))
            policies = compare(sample, full, learned, frozen, scale)
            cases.append({"delivery": rate, "expected_released": {name: values[action] for name, action in policies.items()},
                          "selected_passages": {name: [list(choices[i][action[i]]) for i in range(3)]
                                                for name, action in policies.items()}})
        results[case] = {"rows": cases, "rendered_joint_receipt_checks": len(true) * 8}
    return results


def run():
    assert plan() == json.loads((HERE / "plan.json").read_text())
    training = synthetic(old.TRAIN_SEED, old.TRAIN_N)
    test = synthetic(old.EVAL_SEED, old.EVAL_N)
    frozen = np.array(json.loads((PARENT / "results.json").read_text())["train"]["trace"][-1]["weights"])
    learned, trace = old.train([sample for sample, _ in training])
    scale, objective = tune(training)
    rows = []
    for sample, full in test:
        actions = compare(sample, full, learned, frozen, scale)
        rows.append({arm: reward(sample, selected) for arm, selected in actions.items()})
    held = {name: {"mean": mean(row[name] for row in rows),
                   "oracle_ties": sum(abs(row[name] - row["joint_oracle"]) <= 1e-9 for row in rows)}
            for name in rows[0]}
    return {"trace": trace, "selected_scalar": scale, "scalar_training_objective": objective,
            "held": held, "held_rows": rows, "archive": check_un(learned, frozen, scale),
            "plan_sha256": old.DIGEST(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
