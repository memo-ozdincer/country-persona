"""Validate exact witnesses for the generated reporter's focus shift."""
import json
from pathlib import Path

import deliberation_control as control

ROOT = Path(__file__).resolve().parent / "deliberation-control-evidence"
CLAUSES = {
    (False, False): ("peer_independent_report", "reporting",
                     "Midterm report to the Council by 30 Dec 2023; final report to the Council by 15 June 2024."),
    (False, True): ("ordinary_with_note", "mandate",
                    "intending to review and act on a possible further extension by 1 July 2024."),
    (True, False): ("reply_instruction_no_note", "reporting",
                    "Midterm report to the Council by 30 Dec 2023; final report to the Council by 15 June 2024."),
    (True, True): ("peer_interactive_report", "mandate",
                   "intending to review and act on a possible further extension by 1 July 2024"),
}


def run():
    source = control.baseline() | control.replay(ROOT)
    rows = []
    for (reply, visible), (name, focus, witness) in CLAUSES.items():
        row = source[name]
        payload = json.loads(row["messages"][1]["content"])
        assert bool(payload["working_notes"]) == bool(row["seen"]) == visible
        assert ("respond to the other desk" in payload["task"]) == reply
        assert witness in row["output"] and row["ended"]
        rows.append({"reply_instruction": reply, "peer_note_visible": visible, "id": name,
                     "focus": focus, "exact_witness": witness, "output": row["output"],
                     "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])})
    return {"scope": "Same-assistant exact-span labels on reporter focus. Original conditions share the first "
                     "generation batch with the solo reviewer. The two follow-up conditions use a new batch. "
                     "The intervention has no generated chair follow-up.",
            "cells": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
