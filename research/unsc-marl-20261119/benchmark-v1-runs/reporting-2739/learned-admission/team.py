"""Fit two bounded policies using exact shared admission reward."""
import argparse
from collections import defaultdict
from itertools import product
from pathlib import Path
import hashlib
import json
from statistics import mean

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[2]
REL = STUDY / "benchmark-kit/reader-use"
ARCHIVE = REL / "facilitator-source-relation-evidence"
LABELS = ("supports", "contradicts", "unknown")
STEPS, RATE, PENALTY, COST = 160, .2, .02, .05


def read(path):
    return json.loads(path.read_text())


def pin(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapped(row):
    scores = np.zeros(3)
    scores[row["legal"]] = row["scores"]
    winners = np.flatnonzero(scores == scores.max())
    return scores, int(winners[0]) if len(winners) == 1 else 2


def observations(path, group=None):
    result = defaultdict(dict)
    for line in path.read_text().splitlines():
        row = json.loads(line)
        mode, key, index = row["observation"]
        if group is None or mode == group:
            assert index not in result[key]
            result[key][index] = mapped(row)
    assert all(set(views) == {0, 1} for views in result.values())
    return {key: [views[0], views[1]] for key, views in result.items()}


def training():
    raw = ARCHIVE / "actions.jsonl"
    assert pin(raw) == read(ARCHIVE / "complete.json")["sha256"]
    observed = observations(raw, "routed")
    audited = read(ARCHIVE / "results.json")["decisions"]
    rows = []
    for key, pair in observed.items():
        reference = audited["routed/" + key]
        assert [LABELS[label] if max(vals) == sorted(vals)[-1] and list(vals).count(max(vals)) == 1 else None
                for vals, label in pair] == reference["votes"]
        rows.append((key, key.split("/")[0], LABELS.index(reference["expected"]), pair))
    assert len(rows) == 19 and len({r[1] for r in rows}) == 4
    return rows


def features(first, second):
    a, sent = first
    b, local = second
    gap = a[sent] - max(a[i] for i in range(3) if i != sent)
    agreement = b[sent] - max(b[i] for i in range(3) if i != sent)
    return np.array((1., np.tanh(gap), float(sent == 1))), np.array(
        (1., np.tanh(agreement), float(local == sent), float(sent == 1)))


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def fit(records):
    counts = {row[1]: sum(r[1] == row[1] for r in records) for row in records}
    rows = []
    for _, family, truth, candidates in records:
        for first, second in (candidates, candidates[::-1]):
            a, b = features(first, second)
            eligible = first[1] != 2
            value = 1. if first[1] == truth else -2.
            rows.append((a, b, eligible, value, 1. / (2 * counts[family] * len(counts))))
    x, z, legal, values, weights = [np.asarray(v) for v in zip(*rows, strict=True)]
    p, q = np.zeros(3), np.zeros(4)

    def gradient(p, q):
        send, approve = sigmoid(x @ p) * legal, sigmoid(z @ q)
        target = approve * values - COST
        return float(weights @ (send * target)), (
            x.T @ (weights * send * (1 - send) * target) - PENALTY * p,
            z.T @ (weights * send * approve * (1 - approve) * values) - PENALTY * q,
        )

    before, deriv = gradient(p, q)
    for i, (original, g) in enumerate(zip((p, q), deriv, strict=True)):
        for j, axis in enumerate(np.eye(len(original)) * 1e-5):
            args = [p, q]
            args[i] = original + axis
            plus = gradient(*args)[0]
            args[i] = original - axis
            minus = gradient(*args)[0]
            assert abs((plus - minus) / 2e-5 - g[j]) < 1e-8
    for _ in range(STEPS):
        _, (dp, dq) = gradient(p, q)
        p += RATE * dp
        q += RATE * dq
    after, _ = gradient(p, q)
    assert after >= before - 1e-10
    return {"proposer": p.tolist(), "reviewer": q.tolist(), "training_families": sorted(counts),
            "training_rows": len(records), "expected_net": [before, after]}


def measure(record, frozen):
    key, family, truth, views = record
    rows = {}
    for index, (first, second) in enumerate((views, views[::-1])):
        a, b = features(first, second)
        p = float(sigmoid(a @ np.asarray(frozen["proposer"])))
        q = float(sigmoid(b @ np.asarray(frozen["reviewer"])))
        local, review = first[1], second[1]
        eligible = local != 2
        policies = {
            "fitted_greedy": (int(eligible and p >= .5), int(q >= .5), local),
            "fitted_sampled": (eligible * p, q, local),
            "fit_proposer_consensus": (int(eligible and p >= .5), int(review == local), local),
            "always_send_fit_reviewer": (int(eligible), int(q >= .5), local),
            "first_only": (int(eligible), 1, local),
            "consensus": (int(eligible), int(review == local), local),
            "no_opposing_actionable": (int(eligible), int(review in (local, 2)), local),
            "silent": (0, 0, local),
        }
        scores = (first[0] + second[0]) / 2
        _, pooled = mapped({"legal": [0, 1, 2], "scores": scores})
        policies["pooled_mean"] = (int(pooled != 2), 1, pooled)
        outcomes = {}
        for name, (send, approve, verdict) in policies.items():
            admit = send * approve
            correct = admit * (verdict == truth)
            wrong = admit * (verdict != truth)
            outcomes[name] = {"net": correct - 2 * wrong - COST * send, "true_admission": correct,
                              "wrong_admission": wrong, "accuracy": correct + (1 - admit) * (truth == 2),
                              "sent": send}
        rows[str(index)] = {"first": LABELS[local], "second": LABELS[review],
                            "send_probability": p, "approve_probability": q, "policies": outcomes}
    return {"key": key, "family": family, "truth": LABELS[truth], "orders": rows}


def summary(rows):
    families = defaultdict(list)
    for row in rows:
        families[row["family"]].extend(v["policies"] for v in row["orders"].values())
    groups = {}
    for key, group in families.items():
        groups[key] = {arm: {metric: mean(r[arm][metric] for r in group)
                             for metric in values} for arm, values in group[0].items()}
    macro = {arm: {metric: mean(r[arm][metric] for r in groups.values())
                   for metric in metrics} for arm, metrics in next(iter(groups.values())).items()}
    return {"families": groups, "macro": macro}


def prepare():
    train = training()
    folds, rows = {}, []
    for name in sorted({r[1] for r in train}):
        frozen = folds[name] = fit([r for r in train if r[1] != name])
        assert name not in frozen["training_families"]
        rows.extend(measure(r, frozen) for r in train if r[1] == name)
    inputs = [Path(__file__), HERE / "protocol.md", *(ARCHIVE / x for x in ("actions.jsonl", "results.json", "complete.json"))]
    return {"frozen": fit(train), "folds": folds, "archive_rows": rows, "archive_summary": summary(rows),
            "files": {str(f.relative_to(STUDY)): pin(f) for f in inputs}}


def evaluate():
    archived = read(HERE / "fit.json")
    assert archived == prepare()
    held = read(HERE / "held.json")
    calls = HERE / "evidence/calls.jsonl"
    assert pin(calls) == read(HERE / "verified.json")["evidence_sha256"]["calls.jsonl"]
    values = observations(calls, "held")
    assert set(values) == {row["id"] for row in held}
    rows = [measure((r["id"], "reporting-2739", LABELS.index(r["expected"]), values[r["id"]]), archived["frozen"])
            for r in held]
    return {"held_rows": rows, "held_summary": summary(rows),
            "files": {p: pin(HERE / p) for p in ("held.json", "verified.json", "fit.json")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fit", "evaluate"))
    print(json.dumps({"fit": prepare, "evaluate": evaluate}[parser.parse_args().mode](), indent=2))
