"""Enforce a whole-sentence note budget and rerun only affected chair receipts."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import routing_climate_language_channel as channel

read, digest, runner = channel.read, channel.digest, channel.runner
BASE = channel.transfer.base.space.OUT / "climate2021-language-channel"
LIMIT = 55
archived_capture = channel.capture


def prefix(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    retained = []
    total = 0
    for part in parts:
        words = len(part.split())
        if total + words > LIMIT or not part.endswith((".", "!", "?")):
            break
        retained.append(part)
        total += words
    result = " ".join(retained)
    assert result and text.startswith(result)
    return result


def inputs():
    notes, records = archived_capture(BASE)
    admitted = {key: {**row, "output": prefix(row["output"])} for key, row in notes.items()}
    old = {row["id"]: row for row in records}
    changed = [request for request in channel.writer_requests(admitted)
               if request["messages"] != old[request["id"]]["messages"]]
    assert len(changed) == 6
    for request in changed:
        assert all(request[key] == old[request["id"]][key] for key in ("id", "cap", "evidence_ids"))
        assert request["messages"][0] == old[request["id"]]["messages"][0]
    return admitted, records, changed


def locks():
    return {**channel.locks(), "budget_script": digest(Path(__file__)), "language_trace": digest(BASE / "transcript.jsonl"),
            "language_score": digest(BASE / "scores.json")}


def episode(generate):
    _, _, changed = inputs()
    return [{"family": channel.transfer.task()["id"], "final": generate(changed)}]


def run(directory):
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(BASE / "launch.json")["model"]), directory)


def capture(directory):
    assert read(directory / "launch.json")["sha256"] == locks()
    notes, prior_records, changed = inputs()
    done = read(directory / "complete.json")
    trace, finals = directory / "transcript.jsonl", directory / "final-records.json"
    assert digest(trace) == done["transcript_sha256"] and digest(finals) == done["final_records_sha256"]
    observed = list(map(json.loads, trace.read_text().splitlines()))
    assert len(observed) == done["records"] == len(changed)
    for row, request in zip(observed, changed, strict=True):
        assert all(row[key] == value for key, value in request.items())
    assert read(finals)[channel.transfer.task()["id"]] == {row["id"]: row["output"] for row in observed}
    replacements = {row["id"]: row for row in observed}
    return notes, [replacements.get(row["id"], row) for row in prior_records]


def score(directory, labels):
    with patch.object(channel, "capture", capture):
        return {**channel.score(directory, labels), "note_budget": LIMIT,
                "reused_raw_note_trace_sha256": digest(BASE / "transcript.jsonl")}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score"))
    cli.add_argument("path", type=Path, nargs="?")
    cli.add_argument("--annotations", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.path)
    elif args.mode == "score":
        print(json.dumps(score(args.path, args.annotations), indent=2, ensure_ascii=False))
    else:
        notes, _, changed = inputs()
        print(json.dumps({"admitted": {key: row["output"] for key, row in notes.items()},
                          "changed": [row["id"] for row in changed], "locks": locks()},
                         indent=2, ensure_ascii=False))
