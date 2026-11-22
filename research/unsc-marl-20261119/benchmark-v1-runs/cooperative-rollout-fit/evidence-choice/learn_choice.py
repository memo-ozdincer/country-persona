"""Optimize shared decentralized evidence selection from exact team returns."""
import argparse
from itertools import combinations, product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[1]
SELECTOR = RUNS / "disability-2475-transfer/native-selection"
TRIB = RUNS / "tribunals-v14-transfer"
sys.path.insert(0, str(SELECTOR))
sys.path.insert(0, str(TRIB))
import compose_notes as disability
import tribunals_transfer as tribunals

DIGEST = tribunals.digest
COUNTS = (2, 3, 3)
CAPS = (1, 2, 2)
TRAIN_SEED = 247500
EVAL_SEED = 242200
TRAIN_N = 96
EVAL_N = 48
UPDATES = 150
RATE = 0.12
FEATURES = ["local", "uniform_joint", "priority_joint"]


def plan():
    pins = (Path(__file__), HERE / "protocol.md", SELECTOR / "scores.json",
            SELECTOR / "compose_notes.py", SELECTOR / "select_notes.py", TRIB / "tribunals_transfer.py",
            tribunals.RELEASE / "release.json")
    return {"seeds": [TRAIN_SEED, EVAL_SEED], "cases": [TRAIN_N, EVAL_N],
            "features": FEATURES, "updates": UPDATES, "rate": RATE, "initial_weights": [0.0] * len(FEATURES),
            "sha256": {str(p.relative_to(tribunals.STUDY)): DIGEST(p) for p in pins}}


def options(counts, caps):
    return tuple(list(combinations(range(n), k)) for n, k in zip(counts, caps, strict=True))


def softmax(values):
    exp = np.exp(values - np.max(values))
    return exp / exp.sum()


def scenario(counts, caps, scores, edges):
    choices = options(counts, caps)
    membership = [np.array([[i in row for i in range(n)] for row in group])
                  for group, n in zip(choices, counts, strict=True)]
    values = [matrix @ weights for matrix, weights in zip(membership, scores, strict=True)]
    uniform = [matrix.mean(0) for matrix in membership]
    advertised = [softmax(points / 3) @ table for points, table in zip(values, membership, strict=True)]
    hints = [np.zeros((len(group), 2)) for group in choices]
    for i, a, j, b, weight in edges:
        hints[i] += weight * membership[i][:, a, None] * (uniform[j][b], advertised[j][b])
        hints[j] += weight * membership[j][:, b, None] * (uniform[i][a], advertised[i][a])
    feature = [np.column_stack((local, edge)) / 7 for local, edge in zip(values, hints, strict=True)]
    indices = np.array(list(product(*(range(len(group)) for group in choices))))
    rewards = np.zeros(len(indices))
    for i, val in enumerate(values):
        rewards += val[indices[:, i]]
    for i, a, j, b, weight in edges:
        rewards += weight * (membership[i][indices[:, i], a] & membership[j][indices[:, j], b])
    return choices, indices, feature, rewards


def synthetic(seed, size):
    rng = np.random.default_rng(seed)
    cases = []
    for _ in range(size):
        local = [rng.integers(0, 8, n) for n in COUNTS]
        edges = [(i, int(rng.integers(COUNTS[i])), j, int(rng.integers(COUNTS[j])), int(rng.integers(0, 15)))
                 for i, j in combinations(range(3), 2)]
        cases.append(scenario(COUNTS, CAPS, local, edges))
    return cases


def expected(sample, weights):
    _, actions, local, reward = sample
    probs = [softmax(features @ weights) for features in local]
    joint = np.prod([dist[actions[:, i]] for i, dist in enumerate(probs)], axis=0)
    assert abs(joint.sum() - 1) < 1e-10
    objective = joint @ reward
    gradient = np.zeros_like(weights)
    for i, (dist, features) in enumerate(zip(probs, local, strict=True)):
        centered = features[actions[:, i]] - dist @ features
        gradient += (joint * (reward - objective)) @ centered
    return float(objective), gradient


def train(samples):
    weights = np.zeros(len(FEATURES))
    trace = []
    for step in range(UPDATES + 1):
        evaluations = [expected(sample, weights) for sample in samples]
        value = mean(v for v, _ in evaluations)
        grad = np.mean([g for _, g in evaluations], axis=0)
        if step % 15 == 0:
            trace.append({"update": step, "mean_return": value, "weights": weights.tolist(),
                          "gradient_norm": float(np.linalg.norm(grad))})
        if step == 0:
            delta = 1e-5
            numeric = [(expected(samples[0], weights + row * delta)[0] -
                        expected(samples[0], weights - row * delta)[0]) / (2 * delta)
                       for row in np.eye(len(FEATURES))]
            assert np.allclose(numeric, evaluations[0][1], rtol=0, atol=1e-7)
        if step != UPDATES:
            weights += RATE * grad
    assert trace[-1]["mean_return"] > trace[0]["mean_return"]
    return weights, trace


def policies(sample, weights, reverse=False):
    choices, indices, local, rewards = sample
    rules = {"learned": weights, "local": np.array([1., 0., 0.]),
             "uniform_partner": np.array([1., 1., 0.]), "priority_forecast": np.array([1., 0., 1.])}
    results = {}
    for mode, vector in rules.items():
        selected = tuple(int(np.argmax(x @ vector)) for x in local)
        results[mode] = selected
    results["first"] = tuple(len(x) - 1 if reverse else 0 for x in choices)
    results["joint_oracle"] = tuple(int(i) for i in indices[int(rewards.argmax())])
    return results


def evaluate_synthetic(test, weights):
    rows = []
    for sample in test:
        _, indices, _, rewards = sample
        values = {tuple(key): float(y) for key, y in zip(indices, rewards, strict=True)}
        arms = {name: values[choice] for name, choice in policies(sample, weights).items()}
        arms["random"] = float(rewards.mean())
        rows.append(arms)
    return {"summary": {key: {"mean": mean(r[key] for r in rows),
                              "oracle_ties": sum(r[key] == r["joint_oracle"] for r in rows)}
                        for key in rows[0]}, "rows": rows}


def un_cases():
    def disability_score(selection, mask):
        return disability.render([[str(i + 1) for i in row] for row in selection], mask)["score"]["released_70"]

    def tribunals_score(selection, mask):
        ids = {owner: [str(i + 1) for i in row] if mask & (1 << desk) else []
               for desk, (owner, row) in enumerate(zip(tribunals.CARDS, selection, strict=True))}
        return tribunals.grade(ids)["score"]["released_70"]

    # Two UK criteria share the same obligations claim. Both are already in the rubric.
    yield "disability", COUNTS, CAPS, [[7, 0], [7, 7, 0], [7, 14, 0]], [(0, 0, 1, 0, 7)], disability_score
    # Recover the archived release scorer's exact prerequisites and case weights.
    locations = {source: (desk, int(id_) - 1) for desk, menu in enumerate(tribunals.CARDS.values())
                 for id_, (source, _) in menu.items()}
    local = [[0, 0] for _ in range(3)]
    relations = []
    for rule in tribunals.CASE["rubric"]:
        key = rule["id"]
        sources = tribunals.EXTRA_SOURCES.get(key, (key,))
        private = [locations[item] for item in sources if item not in {"vote", "action"}]
        if len(private) == 1:
            (desk, action), = private
            local[desk][action] += rule["weight"]
        elif private:
            (desk1, action1), (desk2, action2) = private
            relations.append((desk1, action1, desk2, action2, rule["weight"]))
    yield "tribunals", (2, 2, 2), (1, 1, 1), local, relations, tribunals_score


def evaluate_un(weights):
    rows = {}
    for case, counts, caps, local, edges, score in un_cases():
        sample = scenario(counts, caps, [np.asarray(x) for x in local], edges)
        choices, exact, _, estimated = sample
        true = {tuple(ids): score([choices[i][code] for i, code in enumerate(ids)], 7) for ids in exact}
        # Local tags give increments over a shared public lead; verify all combinations.
        offsets = set(round(true[tuple(ids)] - predicted, 9) for ids, predicted in zip(exact, estimated, strict=True))
        assert len(offsets) == 1
        results = {}
        for order in ("normal", "reversed"):
            actions = policies(sample, weights, reverse=order == "reversed")
            groups = {arm: [list(choices[i][code]) for i, code in enumerate(selected)]
                      for arm, selected in actions.items()}
            banks = {arm: [score(selection, mask) for mask in range(8)] for arm, selection in groups.items()}
            if case == "disability":
                prior = json.loads((SELECTOR / "scores.json").read_text())["banks"][f"{order}/native"]
                banks["frozen_language"] = prior
            assert all(bank[-1] <= max(true.values()) for bank in banks.values())
            results[order] = {"banks": banks, "selections_zero_based": groups}
        rows[case] = {"orders": results, "verified_exact_reward_combinations": len(exact),
                      "shared_public_points": offsets.pop()}
    return rows


def run():
    assert plan() == json.loads((HERE / "plan.json").read_text())
    training, held = synthetic(TRAIN_SEED, TRAIN_N), synthetic(EVAL_SEED, EVAL_N)
    signature = lambda case: tuple(np.r_[*(x.ravel() for x in case[2]), case[3]])
    assert not set(map(signature, training)) & set(map(signature, held))
    weights, trace = train(training)
    return {"train": {"trace": trace, "exact_joint_evaluations": TRAIN_N * 18 * (UPDATES + 1)},
            "synthetic_evaluation": evaluate_synthetic(held, weights), "archived_un": evaluate_un(weights),
            "plan_sha256": DIGEST(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
