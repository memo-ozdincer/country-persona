"""Fit an action-value calibration on three source states and audit held text."""
import json
import re

import numpy as np

from text_study import HERE, MAPPINGS, PRIOR, cases, read

SEED = 255332
KEYWORDS = re.compile(r"rush|negotiat|timetable|penhold|too little time|short window", re.I)


def outcome_table():
    archive = read(PRIOR / "scores.json")
    fit = read(PRIOR / "reply-fit.json")["exact_pair_gate"]["learned_receipt_values"]
    table = np.array(fit)
    fallback = archive["fallback_partials"]["public"]
    early = archive["views"]["uk-only"]["standalone"]
    assert (table[:, 0] == table[:, 1]).all()
    return table[:, 0] - np.array([fallback, early])[:, None]


def margin(key, archive):
    values = {}
    for suffix, labels in MAPPINGS.items():
        scores = archive[f"{key}/{suffix}"]["logits"]
        process = next(k for k in labels if labels[k] == "process")
        fund = next(k for k in labels if labels[k] == "fund")
        values[suffix] = scores[process] - scores[fund]
    return values | {"mean": sum(values.values()) / 2}


def run():
    archive = read(HERE / "verified.json")["outputs"]
    data = cases()
    scores = {key: margin(key, archive) for key in data}
    table = outcome_table()
    calibration = [key for key, row in data.items() if row["split"] == "calibration"]
    rng = np.random.default_rng(SEED)
    log = []
    for context, action, delivered in zip(rng.integers(len(calibration), size=64),
                                           rng.integers(2, size=64), rng.random(64) < .85, strict=True):
        key = calibration[context]
        target = int(data[key]["complements"])
        log.append({"context": key, "action": int(action), "german_reply_arrived": bool(delivered),
                    "score_above_fixed_record": int(table[target, action]) if delivered else 0})
    training = {}
    for key in calibration:
        observations = [
            [row["score_above_fixed_record"] for row in log if row["context"] == key
             and row["german_reply_arrived"] and row["action"] == action]
            for action in range(2)
        ]
        assert all(observations)
        training[key] = {"estimated_advantage": float(np.mean(observations[0]) - np.mean(observations[1])),
                         "margin": scores[key]["mean"], "observed_per_action": list(map(len, observations))}
    x = np.array([[1, row["margin"]] for row in training.values()])
    y = np.array([row["estimated_advantage"] for row in training.values()])
    coeff, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    assert rank == 2
    rows = {}
    pooled = table[[int(row["complements"]) for row in data.values() if row["split"] == "held"]]
    for key, row in data.items():
        values = table[int(row["complements"])]
        predicted = float(np.array([1, scores[key]["mean"]]) @ coeff)
        choices = {
            "ab": scores[key]["ab"] > 0, "ba": scores[key]["ba"] > 0, "mean": scores[key]["mean"] > 0,
            "reward_calibration": predicted > 0, "presence": bool(row["text"]),
            "keywords": bool(KEYWORDS.search(row["text"])),
            "always_process": True, "always_fund": False,
        }
        rows[key] = {"split": row["split"], "true_process_reply": row["complements"],
                     "margins": scores[key], "estimated_advantage": round(predicted, 8),
                     "choices": {method: "process" if choice else "fund" for method, choice in choices.items()},
                     "release_gain_above_first_record": {method: int(values[0 if choice else 1])
                                                         for method, choice in choices.items()}}
    held = [row for row in rows.values() if row["split"] == "held"]
    assert len(held) == len(pooled) == 12
    oracle = float(pooled.max(axis=1).mean())
    metrics = {}
    for method in held[0]["choices"]:
        gain = float(np.mean([row["release_gain_above_first_record"][method] for row in held]))
        metrics[method] = {
            "correct": sum((row["choices"][method] == "process") == row["true_process_reply"] for row in held),
            "mean_reply_gain": round(gain, 8), "mean_regret": round(oracle - gain, 8),
        }
    return {"calibration_rollouts": log, "calibration": training, "coefficients": coeff.round(8).tolist(),
            "held_oracle_mean_reply_gain": round(oracle, 8), "held_metrics": metrics, "cases": rows}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
