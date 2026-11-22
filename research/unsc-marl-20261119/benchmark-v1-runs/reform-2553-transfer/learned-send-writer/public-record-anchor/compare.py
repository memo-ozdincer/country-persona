"""Compare native, verbatim, and authored relation records on identical branches."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from statistics import mean
from unittest.mock import patch

import anchor_writer as anchor

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
spec = spec_from_file_location("paired_2553_verbatim_grader", PARENT / "score.py")
score = module_from_spec(spec)
spec.loader.exec_module(score)


def run():
    locked = anchor.locked()
    verified = json.loads((HERE / "verified.json").read_text())
    public = locked["public_lead"]
    docs = {row["id"]: row["text"] for row in score.frozen.evidence(score.CASE)}
    literal, literals = {}, {}
    for id_, row in verified["packets"].items():
        ids = row["visible_sources"]
        assert row["reply"]["text"] == public + "\n\n" + verified["native_sections"][id_]["reply"]["text"]
        text = public + "\n\n" + " ".join(docs[key] for key in ids[3:])
        literal_packet = {"visible_sources": ids, "reply": {"text": text, "termination": "complete"}}
        marks = {"units": {key: ["met", docs[key], "The verified source clause is preserved verbatim."]
                           for key in ids},
                 "guard": ["clear", "", "All text is copied from the identified source blocks.", []]}
        result, _ = score.grade(literal_packet, marks)
        assert result["release"]
        literal[id_], literals[id_] = result["released_70"], text

    with patch.object(score, "HERE", HERE), patch.object(score.writer, "locked", return_value=locked):
        measured = score.run()

    comparisons = []
    for row in measured["branches"]:
        raw = [literal[key] for key in row["pair"]]
        assert all(x <= y for x,y in zip(raw, row["typed_scores"], strict=True))
        comparisons.append(row | {"verbatim_scores": raw})
    receipt_mass = sum(row["probability"] for row in comparisons)
    assert receipt_mass == .75
    arms = {
        "split_native": "writer_released", "split_native_lower_raw": "writer_raw_lower",
        "verbatim_delegation_notes": "verbatim_scores", "authored_comparisons": "typed_scores",
    }
    expected = {}
    for label, key in arms.items():
        endpoints = [sum(row["probability"] * row[key][i] for row in comparisons) for i in (0, 1)]
        expected[label] = {"conditional_means": [x / receipt_mass for x in endpoints],
                           "unconditional_paired_delta": endpoints[1] - endpoints[0]}

    previous = json.loads((PARENT / "authority-clarification/scores.json").read_text())
    return measured | {
        "branches": comparisons,
        "expected": expected,
        "native_release_count": sum(row["release"] for row in measured["grades"].values()),
        "prior_native_release_count": sum(row["release"] for row in previous["grades"].values()),
        "verbatim_mean_on_distinct_inputs": mean(literal.values()), "verbatim_records": literals,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
