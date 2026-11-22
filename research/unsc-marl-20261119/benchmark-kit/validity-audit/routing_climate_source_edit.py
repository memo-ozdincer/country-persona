"""Compare withholding an erroneous sentence with a cited source-bound scope correction."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import routing_climate_transfer as transfer

read, digest = transfer.read, transfer.digest
BASE = transfer.base.space.OUT / "climate2021-writer-transfer"
PLAN = BASE / "plan.json"
RECEIPT = "visible-2"
WRONG = "limited specifically to climate pressures exacerbating conflicts in the Sahel region"
SOURCE_SCOPE = "limited to that region"
EDITED_SCOPE = "limited to the Sahel region"


def evaluate():
    before = transfer.captured(BASE, PLAN)
    original = next(row for row in before if row["id"] == RECEIPT)
    assert original["evidence_ids"] == ["india-explanation"]
    text = original["output"]
    assert text.count(WRONG) == 1 and text.endswith(WRONG + ".")
    source = next(row for row in transfer.task()["optional_sources"] if row["id"] == "india-explanation")
    assert SOURCE_SCOPE in source["text"] and "Sahel" in source["text"]

    source_labels = read(BASE / "annotations.json")
    assert source_labels["rows"][RECEIPT]["issues"]["guard"] == WRONG
    sentences = text.split(". ")
    assert len(sentences) == 2
    controls = {
        "withhold_wrong_sentence": (sentences[0] + ".", {}, "Retains the forum rationale. The required Sahel alternative is absent."),
        "verified_scope_replacement": (text.replace(WRONG, EDITED_SCOPE), {"india": text.replace(WRONG, EDITED_SCOPE)},
                                       "The edit retains the forum rationale and states the alternative's documented geographic scope."),
    }
    result = {}
    for name, (edited, credit, reason) in controls.items():
        replacement = [{**r, "output": edited} if r["id"] == RECEIPT else r for r in before]
        marks = deepcopy(source_labels)
        marks["scope"] = "Hand-specified post-generation source intervention on one archived receipt. No new model calls."
        marks["rows"][RECEIPT] = {"met": credit, "guard": "clear", "issues": {}, "reason": reason}
        with TemporaryDirectory() as tmp:
            annotations = Path(tmp) / "annotations.json"
            annotations.write_text(json.dumps(marks, ensure_ascii=False))
            with patch.object(transfer, "captured", return_value=replacement):
                replay = transfer.score(BASE, PLAN, annotations)
        chosen = replay["arms"]["visible"]
        result[name] = {"edited_supplement": edited, "edited_annotation": marks["rows"][RECEIPT],
                        "raw": chosen["raw"], "release": chosen["release"],
                        "release_results": chosen["results"]["release"]}
    return {
        "scope": "Explicitly reviewed one-receipt edit. The model outputs and all routing policies are untouched. "
                 "The correction demonstrates the endpoint impact of admitting a source-faithful record.",
        "source": {"id": source["id"], "pages": source["pages"], "reference": transfer.task()["sources"]["meeting"],
                   "summary": source["text"]},
        "before_sha256": digest(BASE / "transcript.jsonl"), "task_sha256": digest(transfer.TASK),
        "before": text, "alternatives": result,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.parse_args()
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
