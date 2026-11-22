"""Fit a review policy directly from downstream cooperative returns."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import one_review as before
import study as s

MASKS = s.UNKNOWN
STEPS, RATE, PENALTY = 160, .2, .02
HISTORY = s.HERE / "one-review.json"
EPS = 1e-9


def plan():
    files = (Path(__file__), HERE / "protocol.md", HISTORY, Path(s.__file__),
             Path(before.__file__), s.HERE / "results.json", s.previous.OLD)
    return {"masks": MASKS, "updates": STEPS, "step_size": RATE, "penalty": PENALTY,
            "sha256": {str(p.relative_to(s.E)): s.sha(p) for p in files}}


def public_inputs(anchors, law):
    known = {m: r for m, (r, _) in anchors.items()}
    prior = s.R.TEST_PRIORS[law]
    opening_forecast = np.array([known[m] if m in known else s.additive(anchors, m)
                                 for m in s.MASKS])
    init = s.previous.budget.read(s.previous.OLD)["training"]["budget_fit"]
    left, right = s.previous.opening(opening_forecast, prior, init)
    mass = s.joint.opening(left, right, prior)

    def optimize(grades):
        chosen = [s.choose(grades, m, tuple(grades)) for m in s.MASKS]
        points = np.array([grades[m] for m in chosen])
        q, a = s.fit.exact(points, mass, s.fit.PERFECT)
        result = s.joint.metric((left, right, q, a), prior, points, s.fit.PERFECT)
        return float(result["net"])

    initial = optimize(known)
    additive = np.array([optimize(known | {m: s.additive(anchors, m)}) - initial for m in MASKS])
    optimistic = np.array([optimize(known | {m: 70}) - initial for m in MASKS])
    severity = np.array([max(known[k] for k in s.subsets(m, s.KNOWN)) for m in MASKS])
    x = np.column_stack((additive / 10, optimistic / 10, severity / 10,
                         [int(m.bit_count() == 3) for m in MASKS]))
    assert np.all(additive >= -EPS) and np.all(optimistic >= additive - EPS)
    return x, initial


def policy(x, w):
    z = x @ w
    exp = np.exp(z - z.max(axis=-1, keepdims=True))
    return exp / exp.sum(axis=-1, keepdims=True)


def learn(rows, mode):
    x = np.stack([row["x"][mode] for row in rows])
    y = np.stack([row["gain"] for row in rows])
    counts = {r["family"]: sum(t["family"] == r["family"] for t in rows) for r in rows}
    family_weights = np.array([1 / counts[r["family"]] for r in rows])
    family_weights /= family_weights.sum()
    w = np.zeros(x.shape[-1])

    def response(w):
        p = policy(x, w)
        expected = (p * y).sum(axis=-1)
        grad = np.einsum("i,ij,ijk->k", family_weights, p * (y - expected[:, None]), x)
        return float(family_weights @ expected), grad - PENALTY * w

    value, gradient = response(w)
    numerical = [(response(w + axis * 1e-5)[0] - response(w - axis * 1e-5)[0]) / 2e-5
                 for axis in np.eye(len(w))]
    assert np.allclose(numerical, gradient, atol=1e-8, rtol=0)
    trace = [value]
    for step in range(1, STEPS + 1):
        w += RATE * gradient
        value, gradient = response(w)
        if step % 40 == 0:
            trace.append(value)
    assert trace[-1] >= trace[0] - EPS
    fixed_value = family_weights @ y
    return w, trace, fixed_value


def load():
    archived = json.loads(HISTORY.read_text())
    rows = []
    for case in s.banks():
        family, version = case["family"], case["mode"]
        key = family + "/" + version
        # The policy-facing function gets only these four values and the announced law.
        anchors = s.reviewed(case)
        assert tuple(anchors) == s.KNOWN
        for law, previous in archived["rows"].items():
            old = previous[key]
            x, initial = public_inputs(anchors, law)
            assert abs(initial - old["before"]["net"]) < EPS
            for i, mask in enumerate(MASKS):
                assert abs(10 * x[i, 1] - old["optimistic_gain"][str(mask)]) < EPS
            net = np.array([old["review_options"][str(m)]["net"] for m in MASKS])
            assert np.all(net >= initial - EPS) and net.max() <= old["all_reviewed"]["net"] + EPS
            rows.append({"family": family, "version": version, "law": law,
                         "x": {"public": x, "identity": np.eye(len(MASKS))}, "gain": net - initial,
                         "net": net, "no_review": initial, "forward_all": old["forward_all_net"],
                         "ridge": old["chosen"]["ridge_value"], "hindsight": old["chosen"]["hindsight"],
                         "optimistic": old["chosen"]["optimistic_value"]})
    assert len(rows) == 20
    return rows


def fold(train, test):
    fitted = {mode: learn(train, mode) for mode in ("public", "identity")}
    fixed = int(np.argmax(fitted["public"][2]))
    runs = []
    for row in test:
        x, net = row["x"], row["net"]
        p = {mode: policy(x[mode], fitted[mode][0]) for mode in fitted}
        def index(p):
            return int(np.flatnonzero(p >= p.max() - 1e-12)[0])
        chosen = {"public_greedy": index(p["public"]), "identity_greedy": index(p["identity"]),
                  "training_fixed": fixed, "additive": index(x["public"][:, 0])}
        chosen |= {arm: MASKS.index(row[arm]) for arm in ("ridge", "optimistic", "hindsight")}
        arms = {arm: float(net[i]) for arm, i in chosen.items()}
        arms |= {f"mask_{mask}": float(value) for mask, value in zip(MASKS, net, strict=True)}
        arms |= {f"{mode}_sampled": float(probabilities @ net) for mode, probabilities in p.items()}
        arms |= {"no_review": row["no_review"], "forward_all": row["forward_all"],
                 "uniform_review": float(net.mean())}
        runs.append({"law": row["law"], "family": row["family"], "version": row["version"],
                     "net": arms, "mask": {arm: MASKS[i] for arm, i in chosen.items()},
                     "action_features": x["public"].tolist(),
                     "probabilities": {mode: probs.tolist() for mode, probs in p.items()}})
    return {"training_families": sorted({r["family"] for r in train}),
            "training_fixed_returns_above_reviewed": fitted["public"][2].tolist(),
            "fits": {mode: {"weights": w.tolist(), "objective_trace": trace}
                     for mode, (w, trace, _) in fitted.items()}, "rows": runs}


def summarize(folds):
    groups = defaultdict(lambda: defaultdict(list))
    for fold in folds.values():
        for row in fold["rows"]:
            groups[row["law"]][row["family"]].append(row["net"])
    output = {}
    for law, families in groups.items():
        by_family = {family: {arm: mean(row[arm] for row in versions) for arm in versions[0]}
                     for family, versions in families.items()}
        means = {arm: mean(row[arm] for row in by_family.values())
                 for arm in next(iter(by_family.values()))}
        best_fixed = max((f"mask_{m}" for m in MASKS), key=means.__getitem__)
        contrasts = {}
        for name in ("public_greedy", "public_sampled"):
            contrasts[name] = {}
            for baseline in ("training_fixed", best_fixed, "forward_all", "no_review"):
                values = {fam: row[name] - row[baseline] for fam, row in by_family.items()}
                omission = {omit: mean(v for fam, v in values.items() if fam != omit) for omit in values}
                contrasts[name][baseline] = {"mean": mean(values.values()),
                                             "wins": sum(v > EPS for v in values.values()),
                                             "losses": sum(v < -EPS for v in values.values()),
                                             "leave_one_family_out": omission}
        output[law] = {"family_means": by_family, "means": means,
                       "strongest_fixed": best_fixed, "contrasts": contrasts}
    return output


def run():
    lock = json.loads((HERE / "plan.json").read_text())
    assert lock == json.loads(json.dumps(plan()))
    rows = load()
    folds = {}
    for family in sorted({r["family"] for r in rows}):
        train = [r for r in rows if r["family"] != family]
        test = [r for r in rows if r["family"] == family]
        folds[family] = fold(train, test)
        assert family not in folds[family]["training_families"]
    return {"folds": folds, "summary": summarize(folds), "plan_sha256": s.sha(HERE / "plan.json")}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[p.parse_args().mode](), indent=2))
