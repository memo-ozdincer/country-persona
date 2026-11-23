"""Verify the exact-prefix one-call continuation of the UAE-opening Iraq impasse."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from held_suite import metrics
from replay import replay
from run import pretty


def read(path):
    return json.loads(path.read_text())


def calls(directory):
    return [json.loads(line) for line in (directory / "calls.jsonl").read_text().splitlines()]


if __name__ == "__main__":
    original = HERE / "iraq-uae-impasse"
    extended = HERE / "iraq-uae-impasse-one-more-call"
    baseline, continuation = (read(path / "settings.json") for path in (original, extended))
    exceptions = {"call_cap", "started", "extended_from"}
    assert {k: v for k, v in baseline.items() if k not in exceptions} == {
        k: v for k, v in continuation.items() if k not in exceptions
    }
    assert (baseline["call_cap"], continuation["call_cap"]) == (55, 56)
    initial, later = calls(original), calls(extended)
    prefix = [row | {"reused": True} if row["event"] == "response" else row for row in initial]
    assert later[:len(prefix)] == prefix
    extra, reply = later[len(prefix):]
    assert extra["event"] == "request" and reply["event"] == "response" and not reply["reused"]
    case = baseline["case"]
    print(pretty({"original": metrics(replay(original), case), "continuation": metrics(replay(extended), case),
                  "reused_calls": len(initial) // 2, "extra_call": {"seat": extra["country"], "reply": reply["answer"]}}))
