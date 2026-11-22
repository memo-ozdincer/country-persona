"""Replay decisions with target labels removed and check label-order effects."""
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

c = SimpleNamespace(**runpy.run_path(str(Path(__file__).with_name("calibrate.py"))))

HERE = Path(__file__).resolve().parent


def run():
    fit = c.read(HERE/"fit.json")
    spec = c.read(HERE/"fit-plan.json")
    prior = c.prior
    target_source = c.previous.PATHS["2417"]
    target_family = target_source.parent
    read = c.previous.read

    def redact(path):
        if path == target_source:
            return {key: value for key, value in read(path).items() if key != "comparisons"}
        if path == c.previous.PATHS["stress"]:
            return {key: value for key, value in read(path).items() if key != "registered"}
        assert path != c.EARLIER and not path.is_relative_to(target_family)
        return read(path)

    with patch.object(c.previous,"read",redact), patch.object(prior,"read",redact):
        assert json.loads(json.dumps(c.fitted(spec))) == fit
    answers = {ident: record["answer"] for donor in fit["trajectory_log"].values()
               for ident, record in donor["marks"].items()}
    groups = {
        "donors": answers,
        "original": {f"2417/{i}": i for i in range(3)},
        "paraphrase": {f"paraphrased/{i}": i for i in range(3)},
        "fiction": {f"fiction/{i}": 2 for i in range(4)},
    }
    ratings = {}
    for name, truth in groups.items():
        per_order = [0, 0, 0]
        mean_good = 0
        for ident, label in truth.items():
            row = fit["logits"][ident]
            mean_good += int(np.argmax(row["mean"])) == label
            for j, order in enumerate(row["orders"]):
                per_order[j] += max(order, key=order.get) == c.OPTIONS[label]
        ratings[name] = {"n": len(truth), "per_order_correct": per_order, "averaged_correct": mean_good}
    data = c.read(HERE/"results.json")
    verified = 0
    for panel in data["evaluations"].values():
        rows = panel["scores"]
        assert len(rows) == 96
        for row in rows:
            assert row["values"]["fixed_hard/peer"] == row["values"]["oracle/peer"]
            assert row["values"]["calibrated/peer"] == row["values"]["fixed_probabilities/peer"]
            verified += 1
    inputs = c.guard.historical.report.load(HERE/"evidence/labels.jsonl")
    return {"withheld_target_answer_keys": True, "target_settings_verified": verified,
            "label_order_accuracy": ratings, "input_tokens": sum(len(row["input_ids"]) for row in inputs)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
