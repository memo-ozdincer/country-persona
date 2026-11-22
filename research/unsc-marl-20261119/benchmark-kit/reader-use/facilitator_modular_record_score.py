"""Admit exact reviewed notes, compose all receipts, and replay frozen learned routing."""
import argparse
import json
from pathlib import Path
import re

import facilitator_emergency_session_score as replay
import facilitator_modular_record as study

WEIGHT = 4
PUBLIC_POINTS = 34
RECORD_WORDS = 145
# Predicates must start with a word. Strip no model text. Negation, entities
# and qualifiers remain exactly as generated for semantic review.
LEAD = re.compile(r"^[A-Za-z]")


def format_pass(row):
    body = row["output"]
    return (row["ended"] and bool(LEAD.match(body)) and 0 < len(body.split()) <= study.WORDS
            and not any(c in body for c in ("\n", "[", "]", "*", ":", "\r")))


def review_items(rows):
    return {
        f"{name}/{sid}": {
            "source": card["passage"], "criteria": card["fields"], "speaker": case["speakers"][sid],
            "body": rows[f"{name}/{sid}"]["output"], "format_pass": format_pass(rows[f"{name}/{sid}"]),
        }
        for name, case in study.cases().items() for sid, card in case["cards"].items()
    }


def assemble(case, rows, marks):
    fixed = "\n".join(f"[{sid}] {text}" for sid, text in case["public"].items())
    notes = {}
    for sid, row in rows.items():
        grade = marks[sid]
        assert set(grade) == {"support", "support_reason", "units"}
        assert grade["support"] in ("met", "unmet", "uncertain") and grade["support_reason"].strip()
        body = row["output"]
        assert len(grade["units"]) == 3
        for status, span in grade["units"]:
            assert status in ("met", "unmet", "uncertain")
            assert not span or span in body
            assert status != "met" or span
        ok = format_pass(row) and grade["support"] == "met"
        note = f"[{sid}] {case['speakers'][sid]} {body}"
        notes[sid] = {"admitted": ok, "note": note, "format_pass": format_pass(row),
                      "points": WEIGHT * sum(u[0] == "met" for u in grade["units"]),
                      "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
    outcome = {}
    for mask in range(8):
        received = [sid for i, sid in enumerate(notes) if mask & (1 << i)]
        admitted = [sid for sid in received if notes[sid]["admitted"]]
        text = "\n".join([fixed, *(notes[sid]["note"] for sid in admitted)])
        points = PUBLIC_POINTS + sum(notes[sid]["points"] for sid in admitted)
        guarded = len(text.split()) <= RECORD_WORDS
        outcome[f"normalized/{mask}"] = {
            "received": received, "admitted": admitted, "record": text, "words": len(text.split()),
            "points": points, "guarded": guarded, "guarded_points": points if guarded else 0,
            "strict": guarded and points == 70,
        }
    return notes, outcome


def evaluate(rows, grades):
    assert grades.keys() == rows.keys()
    results = {}
    for name, case in study.cases().items():
        cards = case["cards"]
        sources = {s: rows[f"{name}/{s}"] for s in cards}
        notes, records = assemble(case, sources, {s: grades[f"{name}/{s}"] for s in cards})
        results[name] = {"notes": notes, "records": records,
                         "transfer": replay.evaluate(records)}
    return {"scope": "Reuse the same independently generated notes for every delivery mask. Review "
                     "gates are source-local same-assistant annotations. Public fields are source-checked.",
            "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--marks", type=Path)
    args = parser.parse_args()
    recovered = study.verify(args.directory)
    result = (evaluate(recovered, json.loads(args.marks.read_text())) if args.marks else review_items(recovered))
    print(json.dumps(result, indent=2, ensure_ascii=False))
