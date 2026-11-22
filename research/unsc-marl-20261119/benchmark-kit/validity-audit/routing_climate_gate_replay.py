"""Replay sentence withholding behind a calibrated scope gate on model records."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import routing_climate_scope_gate as gate

transfer, read, digest = gate.transfer, gate.read, gate.digest
MAIN = gate.MAIN
PLAN = MAIN / "plan.json"


def apply_gate(rows, labels, by_case, method):
    out = []
    edited = []
    applicable = {"visible-2": "actual-offending", "visible-3": "actual-two-source"}
    for row in rows:
        case = applicable.get(row["id"])
        if case is None:
            out.append(row)
            continue
        item = by_case[case]
        sentence = gate.candidate_scope_sentence(row["output"])
        assert sentence == item["claim"] and row["output"].count(sentence) == 1
        assert "india-explanation" in row["evidence_ids"]
        block = item["model_blocks_by_method"][method]
        if block is False:
            out.append(row)
            edited.append({"id": row["id"], "gate": "clear", "changed": False,
                           "gold_scope_error_retained": item["unsupported_restriction"]})
            continue
        # Remove only the candidate sentence. Verify credit and the rated guard against the remainder.
        remainder = " ".join(row["output"].replace(sentence, "", 1).split())
        assert remainder
        annotation = labels["rows"][row["id"]]
        annotation["met"] = {key: quote for key, quote in annotation["met"].items() if quote in remainder}
        if "guard" in annotation["issues"] and annotation["issues"]["guard"] in sentence:
            del annotation["issues"]["guard"]
            annotation["guard"] = "clear"
            annotation["reason"] = "The one reviewed scope failure was contained in the removed sentence."
        out.append({**row, "output": remainder})
        edited.append({"id": row["id"], "gate": "blocked" if block else "abstained", "changed": True,
                       "removed_sentence": sentence, "unmodified_remainder": remainder})
    return out, edited


def evaluate(score):
    judged = read(score)
    by_case = {row["key"]: row for row in judged["items"]}
    rows = transfer.captured(MAIN, PLAN)
    original_labels = read(MAIN / "annotations.json")
    outcomes = {}
    for method in ("support", "restriction"):
        labels = deepcopy(original_labels)
        edits, trace = apply_gate(rows, labels, by_case, method)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.json"
            path.write_text(json.dumps(labels, ensure_ascii=False))
            with patch.object(transfer, "captured", return_value=edits):
                result = transfer.score(MAIN, PLAN, path)["arms"]["visible"]
        outcomes[method] = {"decisions": trace, "release": result["release"],
                            "results": result["results"]["release"]}
    return {
        "scope": "The gate handles two in-scope archived records, an offending India-only record and a correct "
                 "two-source control. Remove one sentence when the gate blocks or abstains. Keep the unrelated "
                 "guards and scoring under the prior human annotation. No sentence is rewritten or generated.",
        "score_sha256": digest(score), "source_trace_sha256": digest(MAIN / "transcript.jsonl"), "outcomes": outcomes,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scores", type=Path)
    print(json.dumps(evaluate(cli.parse_args().scores), indent=2, ensure_ascii=False))
