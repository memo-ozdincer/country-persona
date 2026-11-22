"""Measure how the independent operator check changes fulfillment and false completion."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import scoped_relay as relay

HERE = relay.HERE


def run():
    path = HERE / "operator-evidence/results.json"
    examples = relay.archive.read(path)["records"]
    setup = relay.binary.decoder.transfer.Calibration()
    evaluations = {}
    for name, example in examples.items():
        data = {}
        for method, interpreters in example["decoders"].items():
            scores = {}
            for arm, decision in interpreters.items():
                rows = [(q, r, relay.named(decision, focus, roster, q, r))
                        for focus, roster, q, r in product(range(4), relay.archive.PAIRS, (0, 1), (0, 1))]
                scores[arm] = relay.total(example["reference"], rows, setup.question_loss, setup.reply_loss)
            data[method] = scores
        evaluations[name] = {"reference": example["reference"], "evaluations": data}
    summary = {}
    for method in ("letters", "semantic_ids"):
        summary[method] = {}
        for scope in ("one", "all", "any", "unspecified"):
            measured = [entry["evaluations"][method] for entry in evaluations.values()
                        if entry["reference"][0] == scope and method in entry["evaluations"]]
            summary[method][scope] = {
                "cases": len(measured),
                **{arm: {key: sum(row[arm][key] for row in measured) / len(measured) for key in measured[0][arm]}
                   for arm in ("ungated", "gated")},
            }
    return {"scope": "Replay the measured operator decisions on the same uniform authenticated inventory and loss "
                     "branches. A withheld dispatch asks for clarification. Missing determinate requests still "
                     "receive no completion credit.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "operator_sha256": sha256(path.read_bytes()).hexdigest(),
            "summary": summary, "evaluations": evaluations}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
