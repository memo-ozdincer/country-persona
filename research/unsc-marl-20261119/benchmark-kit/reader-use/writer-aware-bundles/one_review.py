"""Replay one additional writer review under frozen opening policies."""
from collections import Counter, defaultdict
import json
from statistics import mean

import numpy as np

import study as s


def plans(case, name, ridge, prior_label, forward):
    known = {m: release for m, (release, _) in s.reviewed(case).items()}
    public, _ = s.predicted(s.reviewed(case), np.zeros(7))
    opening_scores = np.array([public[m] for m in s.MASKS])
    original = s.previous.budget.read(s.previous.OLD)["training"]["budget_fit"]
    prior = s.R.TEST_PRIORS[prior_label]
    left, right = s.previous.opening(opening_scores, prior, original)
    opening_mass = s.joint.opening(left, right, prior)

    def run(estimates, actual=None):
        used = [s.choose(estimates, m, tuple(estimates)) for m in s.MASKS]
        scores = np.array([estimates[k] for k in used])
        tested = scores if actual is None else np.array([actual[k] for k in used])
        questions, actions = s.fit.exact(scores, opening_mass, s.fit.PERFECT)
        outcome = s.joint.metric((left, right, questions, actions), prior, tested, s.fit.PERFECT)
        return {"net": float(outcome["net"]), "requests": float(outcome["expected_requests"]),
                "selection": used}

    before = run(known)
    estimates = {m: run(known | {m: ridge[m]})["net"] - before["net"] for m in s.UNKNOWN}
    room = {m: run(known | {m: 70})["net"] - before["net"] for m in s.UNKNOWN}
    observed = {m: run(known | {m: case["release"][m]}) for m in s.UNKNOWN}
    chosen = {
        "ridge_value": max(s.UNKNOWN, key=lambda m: (estimates[m], room[m], -m)),
        "optimistic_value": max(s.UNKNOWN, key=lambda m: (room[m], -m)),
        "hindsight": max(s.UNKNOWN, key=lambda m: (observed[m]["net"], -m)),
    }
    ceiling = run(dict(enumerate(case["release"])))
    assert all(before["net"] <= row["net"] + 1e-9 <= ceiling["net"] + 2e-9 for row in observed.values()), name
    assert all(before["net"] <= before["net"] + gain + 1e-9 for gain in estimates.values()), name
    return {
        "before": before, "forward_all_net": forward, "all_reviewed": ceiling,
        "review_options": observed, "predicted_gain": estimates, "optimistic_gain": room,
        "chosen": chosen,
    }


def summary(rows):
    families = defaultdict(list)
    for key, row in rows.items():
        families[key.split("/")[0]].append(row)
    strategies = ("ridge_value", "optimistic_value", *(f"mask_{m}" for m in s.UNKNOWN), "hindsight")
    methods = {}
    for method in strategies:
        choices = Counter()
        gains = {}
        strictly_beats_forward = 0
        for family, versions in families.items():
            selected = []
            for row in versions:
                mask = int(method.split("_")[1]) if method.startswith("mask_") else row["chosen"][method]
                choices[mask] += 1
                selected.append(row["review_options"][mask]["net"])
            gains[family] = {
                "net": mean(selected),
                "gain_over_reviewed": mean(val - row["before"]["net"]
                                         for val, row in zip(selected, versions, strict=True)),
                "gain_over_forward_all": mean(val - row["forward_all_net"]
                                            for val, row in zip(selected, versions, strict=True)),
            }
            strictly_beats_forward += gains[family]["gain_over_forward_all"] > 1e-9
        methods[method] = {key: mean(r[key] for r in gains.values()) for key in next(iter(gains.values()))}
        methods[method].update(selected_masks=dict(choices), families_above_forward_all=strictly_beats_forward,
                               families=gains)
    return methods


def run():
    banks = s.banks()
    archived = json.loads((s.HERE / "results.json").read_text())
    assert banks == archived["banks"]
    assert s.sha(s.previous.OLD) == archived["sha256"][str(s.previous.OLD.relative_to(s.E))]
    outputs = {label: {} for label in s.fit.live.PRIORS}
    for case in banks:
        family = case["family"]
        key = family + "/" + case["mode"]
        training = [row for row in banks if row["family"] != family]
        parameters, _ = s.fit_labels(training)
        _, ridge = s.predicted(s.reviewed(case), parameters)
        for label in outputs:
            forward = archived["checks"][key]["routing"][label]["all_received"]["net"]
            outputs[label][key] = plans(case, key, ridge, label, forward)
    return {
        "sha256": {p.name: s.sha(p) for p in (
            s.HERE / "results.json", s.HERE / "one-review-protocol.md", s.HERE / "one_review.py",
        )},
        "summary": {label: summary(rows) for label, rows in outputs.items()},
        "rows": outputs,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
