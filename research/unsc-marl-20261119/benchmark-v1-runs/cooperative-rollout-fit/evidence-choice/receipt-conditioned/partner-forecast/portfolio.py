"""Measure whether a learned plan improves a fixed-plan portfolio."""
import json
from pathlib import Path
from statistics import mean
from unittest.mock import patch

import numpy as np

import forecast_response as trial

HERE, old = trial.HERE, trial.old


def capture(seed, size, shift):
    rows = []
    build = trial.case

    def save(counts, caps, local, edges, rates, truth, advertised, records=None):
        sample = build(counts, caps, local, edges, rates, truth, advertised, records)
        rows.append((sample, advertised))
        return sample

    with patch.object(trial, "case", save):
        trial.synthetic(seed, size, shift)
    return rows


def evaluate(sample, announced, fit, previous):
    truth_scores, arms = trial.policies(sample, fit, previous)
    scene, legacy, _, true_probability, _ = sample
    p = announced[:, None] * scene["mask_probabilities"][None, :]
    reward, obs = scene["returns"], scene["observe"]
    a, c = legacy
    arms["local"] = (np.argmax(a[..., 0], axis=1).tolist(), int(np.argmax(c[:, 0])))
    ceiling, table, third = trial.replay.optimal(reward, p, obs)
    arms["announced_exact"] = table, third

    def run(dist, name):
        left, independent = arms[name]
        return trial.replay.expected(reward, dist, obs, np.asarray(left), independent)

    reference = ("local", "legacy_fixed", "refreshed_fixed")
    candidates = {
        "fixed_only": reference, "including_older_fit": (*reference, "older_fit"),
        "including_refreshed_fit": (*reference, "refreshed_fit"),
        "including_both": (*reference, "older_fit", "refreshed_fit"),
    }
    selected = {name: max(choices, key=lambda arm: run(p, arm)) for name, choices in candidates.items()}
    selected["announced_exact"] = "announced_exact"
    results = {}
    for mode, name in selected.items():
        plan_return = run(p, name)
        assert plan_return <= ceiling + 1e-9
        results[mode] = {"true": run(true_probability, name), "announced": plan_return, "selection": name}
    results["oracle"] = {"true": truth_scores["oracle"], "selection": "oracle"}
    return results


def run():
    source = HERE / "results.json"
    parent = trial.ARCHIVED
    protocol = HERE / "portfolio-protocol.md"
    fit = np.asarray(json.loads(source.read_text())["training"][-1]["weights"])
    prev = np.asarray(json.loads(parent.read_text())["training"][-1]["weights"])
    summary, records = {}, {}
    for name, shifted in (("matched", False), ("misannounced", True)):
        rows = [evaluate(sample, announced, fit, prev)
                for sample, announced in capture(old.EVAL_SEED, old.EVAL_N, shifted)]
        floors = {}
        for arm in rows[0]:
            gains = [item[arm]["true"] - item["fixed_only"]["true"] for item in rows]
            scores = [item[arm]["true"] for item in rows]
            floors[arm] = {"mean_release": mean(scores), "gain_over_fixed": mean(gains),
                           "wins": sum(gain > 1e-9 for gain in gains),
                           "losses": sum(gain < -1e-9 for gain in gains),
                           "chosen_learned": sum(item[arm]["selection"] in {"older_fit", "refreshed_fit"} for item in rows)}
        summary[name] = floors
        records[name] = rows
    return {"summary": summary, "rows": records,
            "sha256": {str(p.relative_to(trial.RUNS)): old.DIGEST(p) for p in (Path(__file__), source, parent, protocol)}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
