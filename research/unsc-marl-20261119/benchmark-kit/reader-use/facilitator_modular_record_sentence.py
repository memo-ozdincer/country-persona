"""Test accepting complete attributed sentences with the same source review."""
import argparse
import json
from hashlib import sha256
from pathlib import Path

import facilitator_modular_record_score as original

LIMIT = 36
RECORD_LIMIT = original.RECORD_WORDS


def assemble(case, rows, marks):
    public = "\n".join(f"[{sid}] {text}" for sid, text in case["public"].items())
    notes = {}
    for sid, row in rows.items():
        sentence = row["output"]
        guard = (row["ended"] and sentence.startswith(case["speakers"][sid] + " ")
                 and len(sentence.split()) <= LIMIT and not any(c in sentence for c in ("[", "]", "\n", "\r")))
        points = original.WEIGHT * sum(unit[0] == "met" for unit in marks[sid]["units"])
        notes[sid] = {"format_guard": guard, "admitted": guard and marks[sid]["support"] == "met",
                      "words": len(sentence.split()), "statement_points": points,
                      "text": f"[{sid}] {sentence}"}
    results = {}
    for mask in range(8):
        visible = [sid for i, sid in enumerate(notes) if mask & (1 << i)]
        use = [sid for sid in visible if notes[sid]["admitted"]]
        record = "\n".join([public, *(notes[sid]["text"] for sid in use)])
        # Any full record above its limit fails. No truncation and no
        # changes to the meaning of an already accepted statement.
        points = original.PUBLIC_POINTS + sum(notes[sid]["statement_points"] for sid in use)
        words = len(record.split())
        results[f"normalized/{mask}"] = {"record": record, "delivered": visible, "used": use,
                                         "points": points, "words": words, "guarded_points": points if words <= RECORD_LIMIT else 0,
                                         "strict": points == 70 and words <= RECORD_LIMIT}
    return notes, results


def run(directory):
    rows = original.study.verify(directory)
    marks = json.loads((directory / "marks.json").read_text())
    baseline = json.loads((directory / "results.json").read_text())
    outcomes = {}
    for name, case in original.study.cases().items():
        visible = {sid: rows[f"{name}/{sid}"] for sid in case["cards"]}
        same_review = {sid: marks[f"{name}/{sid}"] for sid in visible}
        old_notes, old_receipts = original.assemble(case, visible, same_review)
        assert old_receipts == baseline["results"][name]["records"]
        notes, banks = assemble(case, visible, same_review)
        outcomes[name] = {"notes": notes, "records": banks, "transfer": original.replay.evaluate(banks)}
    return {"scope": "Post hoc acceptance of complete sentences with verified speaker leads, same factual review, "
                     "36 words per note and 145 words per assembled record. No sentence edits or new generations.",
            "results": outcomes,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (
                Path(__file__), directory / "marks.json", directory / "results.json", directory / "transcript.jsonl")}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(run(p.parse_args().directory), indent=2, ensure_ascii=False))
