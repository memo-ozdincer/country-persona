"""Train an exact shared-return policy with receipt-conditioned evidence choices."""
import argparse
from itertools import combinations, product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT / "delivery-aware"))
import loss_aware as loss

old = loss.old


def plan():
    pins = (Path(__file__), HERE / "protocol.md", Path(loss.__file__),
            PARENT / "delivery-aware/results.json", Path(old.__file__))
    return {"training_cases": old.TRAIN_N, "held_cases": old.EVAL_N, "updates": old.UPDATES,
            "seeds": [old.TRAIN_SEED, old.EVAL_SEED], "rates": list(loss.RATES),
            "sha256": {p.name: old.DIGEST(p) for p in pins}}


def features(counts, caps, local, edges, rates, true_records=None):
    choices, actions, open_features, _ = loss.channel(counts, caps, local, edges, rates)
    a_count, b_count, c_count = map(len, choices)
    observes = np.where(np.arange(8)[None, :] & 2, np.arange(b_count)[:, None] + 1, 0)
    probs = np.array([np.prod([p if mask & 1 << i else 1 - p for i, p in enumerate(rates)])
                      for mask in range(8)])
    assert abs(probs.sum() - 1.0) < 1e-12
    adaptive = np.repeat(open_features[0][None, :, :], b_count + 1, axis=0)
    presence = adaptive.copy()
    uniform_b = 1 / b_count
    predicted_b = old.softmax(open_features[1][:, 0] * 7 / 3)
    for i, a, j, b, weight in edges:
        if (i, j) != (0, 1):
            continue
        present_a = np.array([a in picked for picked in choices[0]])
        present_b = np.array([b in picked for picked in choices[1]])
        forecast = np.array((uniform_b * present_b.sum(), predicted_b @ present_b))
        for view in range(b_count + 1):
            realized = int(present_b[view - 1]) if view else 0.
            adaptive[view, present_a, 1:] += weight * (realized - rates[1] * forecast) / 7
            presence[view, present_a, 1:] += weight * (float(bool(view)) - rates[1]) * forecast / 7
    returns = np.zeros((b_count, c_count, 8, a_count))
    for a, b, c in actions:
        picked = [choices[i][k] for i, k in enumerate((a, b, c))]
        totals = [sum(local[i][d] for d in group) for i, group in enumerate(picked)]
        for mask in range(8):
            computed = sum(points for i, points in enumerate(totals) if mask & 1 << i)
            computed += sum(w for i, u, j, v, w in edges
                            if mask & 1 << i and mask & 1 << j and u in picked[i] and v in picked[j])
            if true_records is not None:
                assert computed == true_records[(int(a), int(b), int(c))][mask] - true_records[(0, 0, 0)][0]
            returns[b, c, mask, a] = computed
    return {"choices": choices, "open": open_features, "adaptive": adaptive, "presence": presence,
            "observe": observes, "mask_probabilities": probs, "returns": returns}


def cases(seed, size):
    rng = np.random.default_rng(seed)
    noise = np.random.default_rng(seed + 8000)
    results = []
    for _ in range(size):
        local = [rng.integers(0, 8, n) for n in old.COUNTS]
        edges = [(i, int(rng.integers(old.COUNTS[i])), j, int(rng.integers(old.COUNTS[j])), int(rng.integers(0, 15)))
                 for i, j in combinations(range(3), 2)]
        results.append(features(old.COUNTS, old.CAPS, local, edges, noise.choice(loss.RATES, 3)))
    return results


def expected(sample, weights, observe=True):
    _, b, c = sample["open"]
    a = sample["adaptive"] if observe else np.broadcast_to(sample["open"][0], sample["adaptive"].shape)
    prob_b, prob_c = old.softmax(b @ weights), old.softmax(c @ weights)
    prob_a = np.asarray([old.softmax(x @ weights) for x in a])
    obs = sample["observe"]
    quadrature = (prob_b[:, None, None, None] * prob_c[None, :, None, None] *
                  sample["mask_probabilities"][None, None, :, None] * prob_a[obs][:, None, :, :])
    assert abs(quadrature.sum() - 1.0) < 1e-10
    value = float(np.sum(quadrature * sample["returns"]))
    centered = quadrature * (sample["returns"] - value)
    local_a = a - np.einsum("oa,oaf->of", prob_a, a)[:, None, :]
    grad = np.einsum("bcma,bmaf->f", centered, local_a[obs])
    grad += np.einsum("bcma,bf->f", centered, b - prob_b @ b)
    grad += np.einsum("bcma,cf->f", centered, c - prob_c @ c)
    return value, grad


def train(samples):
    weights = np.zeros(len(old.FEATURES))
    trace = []
    for step in range(old.UPDATES + 1):
        reads = [expected(sample, weights) for sample in samples]
        avg = mean(item[0] for item in reads)
        grad = np.mean([item[1] for item in reads], axis=0)
        if step == 0:
            eps = 1e-5
            delta = [(expected(samples[0], weights + axis * eps)[0] -
                      expected(samples[0], weights - axis * eps)[0]) / (2 * eps) for axis in np.eye(len(weights))]
            assert np.allclose(delta, reads[0][1], atol=1e-7, rtol=0)
        if step % 15 == 0:
            trace.append({"update": step, "mean_return": avg, "weights": weights.tolist()})
        if step < old.UPDATES:
            weights += old.RATE * grad
    assert trace[-1]["mean_return"] > trace[0]["mean_return"]
    return weights, trace


def run_policy(sample, weights, mode):
    a, b, c = sample["open"]
    views = sample[mode] if mode != "open" else np.broadcast_to(a, sample["adaptive"].shape)
    return int(np.argmax(b @ weights)), int(np.argmax(c @ weights)), np.argmax(views @ weights, axis=1)


def outcome(sample, policy):
    b, c, a = policy
    rows = np.arange(8)
    return float(sample["mask_probabilities"] @ sample["returns"][b, c, rows, a[sample["observe"][b]]])


def oracle(sample, adaptive):
    rows = []
    probs = sample["mask_probabilities"]
    for b, c in product(range(len(sample["choices"][1])), range(len(sample["choices"][2]))):
        views = sample["observe"][b]
        payoffs = sample["returns"][b, c] * probs[:, None]
        if adaptive:
            actions = np.array([np.argmax(payoffs[views == o].sum(axis=0))
                                for o in range(sample["adaptive"].shape[0])])
        else:
            actions = np.full(sample["adaptive"].shape[0], np.argmax(payoffs.sum(axis=0)))
        policy = (b, c, actions)
        rows.append((outcome(sample, policy), policy))
    return max(rows, key=lambda row: row[0])


def compare(sample, learned, previous):
    fixed = np.array([1., 0., 1.])
    policy = {"learned_adaptive": run_policy(sample, learned, "adaptive"),
              "learned_without_receipt": run_policy(sample, learned, "open"),
              "earlier_open_loop": run_policy(sample, previous, "open"),
              "fixed_receipt_priority": run_policy(sample, fixed, "adaptive"),
              "fixed_presence_priority": run_policy(sample, fixed, "presence"),
              "fixed_open_priority": run_policy(sample, fixed, "open"),
              "local_only": run_policy(sample, np.array([1., 0., 0.]), "open")}
    names = ("adaptive_oracle", "static_oracle")
    for name, seen in zip(names, (True, False), strict=True):
        _, policy[name] = oracle(sample, seen)
    points = {name: outcome(sample, action) for name, action in policy.items()}
    assert max(points.values()) <= points["adaptive_oracle"] + 1e-9
    assert all(points[k] <= points["static_oracle"] + 1e-9
               for k in ("earlier_open_loop", "learned_without_receipt", "fixed_open_priority", "local_only"))
    return points, {name: [b, c, a.tolist()] for name, (b, c, a) in policy.items()}


def archive(learned, previous):
    output = {}
    for name, counts, caps, local, edges, score in old.un_cases():
        choices = old.options(counts, caps)
        identifiers = list(product(*(range(len(group)) for group in choices)))
        true = {row: [score([choices[i][idx] for i, idx in enumerate(row)], mask) for mask in range(8)]
                for row in identifiers}
        public = true[(0, 0, 0)][0]
        rows = []
        for rate in loss.RATES:
            sample = features(counts, caps, [np.asarray(row) for row in local], edges, (rate,) * 3, true)
            points, policies = compare(sample, learned, previous)
            rows.append({"rate": rate, "released": {key: val + public for key, val in points.items()},
                         "deployed": policies})
        output[name] = {"rows": rows, "distinct_rendered_records": len(true) * 8}
    return output


def run():
    assert plan() == json.loads((HERE / "plan.json").read_text())
    train_cases = cases(old.TRAIN_SEED, old.TRAIN_N)
    test = cases(old.EVAL_SEED, old.EVAL_N)
    archive_fit = json.loads((PARENT / "delivery-aware/results.json").read_text())
    previous = np.array(archive_fit["trace"][-1]["weights"])
    old_rows = [sample for sample, _ in loss.synthetic(old.EVAL_SEED, old.EVAL_N)]
    for sample, old_sample in zip(test, old_rows, strict=True):
        value, gradient = expected(sample, previous, observe=False)
        ref, reference_gradient = old.expected(old_sample, previous)
        assert abs(value - ref) < 1e-9 and np.allclose(gradient, reference_gradient, atol=1e-9, rtol=0)
    learned, trace = train(train_cases)
    outcomes = [compare(x, learned, previous)[0] for x in test]
    for orig, new in zip(archive_fit["held_rows"], outcomes, strict=True):
        assert abs(orig["learned"] - new["earlier_open_loop"]) < 1e-9
    summary = {key: {"mean": mean(row[key] for row in outcomes), "ties_with_adaptive_oracle":
                     sum(abs(row[key] - row["adaptive_oracle"]) <= 1e-9 for row in outcomes)} for key in outcomes[0]}
    return {"training": trace, "held": summary, "held_rows": outcomes, "archive": archive(learned, previous),
            "plan_sha256": old.DIGEST(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
