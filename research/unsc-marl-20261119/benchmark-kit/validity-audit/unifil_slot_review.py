"""Map fact-by-fact proof extraction to the frozen UNIFIL reward bank."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import unifil_slot_extraction as extraction
import unifil_span_review as review

transport = extraction.transport


def assess(directory, exact):
    slots, bundles = extraction.replay(directory)
    _, old_relations, old_notes = transport.replay(transport.OUT)
    evidence = transport.get_sources()
    notes = {}
    for key, proof in bundles.items():
        field, view, order = key.split(".")
        if view == "intact" and proof["released"]:
            assert old_notes[field, order] == evidence[field]
            notes[field, order] = evidence[field]
    relations = {}
    for tag, past in old_relations.items():
        _, view, order = tag.split(".")
        receipts = [role for role in ("brazil", "china") if (role, order) in notes and
                    (view == "intact" or role == "brazil")]
        identical = receipts == past["receipt_ids"]
        relations[tag] = {"receipt_ids": receipts, "reused": identical,
                          "choice": past["choice"] if identical else None,
                          "accepted": identical and past["accepted"]}
    with patch.object(transport, "replay", return_value=(bundles, relations, notes)):
        replay = review.summarize(directory, exact)
    metrics = {}
    for condition in ("intact", "missing", "misattributed", "missing-first"):
        matched = [value for key, value in bundles.items() if key.split(".")[1] == condition]
        rows = [value for key, value in slots.items() if key.split(".")[1] == condition]
        metrics[condition] = {
            "fixtures": len(matched), "fully_correct": sum(k["correct"] for k in matched),
            "released": sum(k["released"] for k in matched),
            "unsafe_if_ungated": sum(k["unsafe_if_ungated"] for k in matched),
            "slot_calls": len(rows), "correct_slots": sum(k["correct"] for k in rows),
            "wrong_owner": sum(k["wrong_owner"] for k in rows),
            "absent_slots": sum(k["expected"] == "NONE" for k in rows),
            "correct_abstentions": sum(k["expected"] == "NONE" and k["correct"] for k in rows),
        }
        if condition != "intact":
            assert metrics[condition]["released"] == 0
    return {**replay, "scope": "Case-specific proof slots evaluated on the order flip and missingness controls. "
                               "A bundle requires both verified source spans. Prior relationship responses "
                               "are reused only on identical evidence. Link fees exclude proof-reading compute.",
            "slots": slots, "metrics": metrics,
            "comparison_replay_sha256": transport.runner.digest(transport.OUT / "transcript.jsonl")}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--directory", type=Path, default=extraction.OUT)
    cli.add_argument("--exact", action="store_true")
    args = cli.parse_args()
    print(json.dumps(assess(args.directory, args.exact), ensure_ascii=False, indent=2))
