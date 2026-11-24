"""Check the full matched prefix of the UAE-opening Iraq resume."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from meeting import FLOOR
from recording import verify_aborted_run
from run import pretty, simulate


def records(directory):
    return list(map(json.loads, (directory / "calls.jsonl").read_text().splitlines()))


def structured_replies(log):
    for row in log:
        if row["event"] == "response":
            answer = row["answer"]
            action = answer["action"]
            package = answer["text"] if action in ("propose", "rule_out") else None
            yield row["country"], action, answer.get("version"), package


def check():
    initial, resumed = HERE / "mixed", HERE / "resumed"
    old, new = (json.loads((path / "settings.json").read_text()) for path in (initial, resumed))
    ignored = {"started", "codex", "resumed_from"}
    assert {key: value for key, value in old.items() if key not in ignored} == {
        key: value for key, value in new.items() if key not in ignored
    }
    assert new["resumed_from"] == initial.relative_to(ROOT).as_posix()
    status, error, call, public = verify_aborted_run(initial, old, simulate)
    assert status == "call_error" and "429" in error and call == 9 and len(public["history"]) == 2
    before, after = records(initial), records(resumed)
    reused = before[:-2]
    expected = [row | {"reused": True} if row["event"] == "response" else row for row in reused]
    assert after[:len(expected)] == expected
    request = before[-2]
    assert request == after[len(expected)] and request["country"] == "ARE" and request["schema"] == FLOOR
    fresh = [row for row in after[len(expected):] if row["event"] == "response"]
    assert all(not row["reused"] for row in fresh)
    reference = ROOT / "reports/council-workshop-all-sol-matrix-20261123/iraq-uae-impasse"
    matches = sum(a == b for a, b in zip(structured_replies(after), structured_replies(records(reference))))
    return {"reused_replies": call - 1, "fresh_replies": len(fresh), "first_fresh_seat": request["country"],
            "matching_structured_decisions": matches}


if __name__ == "__main__":
    print(pretty(check()))
