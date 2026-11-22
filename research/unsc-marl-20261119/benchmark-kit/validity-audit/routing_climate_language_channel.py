"""Benchmark the frozen route when its delivered payloads are generated national notes."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_climate_transfer as transfer

runner, digest, read = transfer.runner, transfer.digest, transfer.read
BASE = transfer.base.space.OUT / "climate2021-writer-transfer"
PLAN = BASE / "plan.json"
WRITING_BASE = BASE / "scores.json"
NOTE_CAP = 88
GUIDE = (
    "Write one short note to the chair reporting this delegation's explanation of the vote. "
    "Use only this annex summary. Keep the reasons, institutional preferences and geographic and policy scope. "
    "Name the delegation and clearly distinguish what it said from a Council decision. "
    "Supply the explanation only, in at most 55 words."
)


def note_requests():
    for source in transfer.task()["optional_sources"]:
        payload = {"delegation": source["role"], "source": source["text"]}
        yield {"id": f"note-{source['id']}", "evidence_ids": [source["id"]], "cap": NOTE_CAP,
               "messages": [{"role": "system", "content": GUIDE},
                            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def writer_requests(notes):
    for row in transfer.requests():
        if not row["id"].startswith("visible-"):
            continue
        user = json.loads(row["messages"][1]["content"])
        user["annexes_delivered"] = {key: notes[f"note-{key}"]["output"] for key in row["evidence_ids"]}
        yield {**row, "messages": [row["messages"][0],
                                  {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]}


def episode(generate):
    notes = generate(list(note_requests()))
    records = generate(list(writer_requests(notes)))
    return [{"family": transfer.task()["id"], "final": {**notes, **records}}]


def locks():
    return {**transfer.locks(PLAN), "language_script": digest(Path(__file__)),
            "verified_source_baseline": digest(WRITING_BASE), "baseline_model": digest(BASE / "launch.json")}


def run(directory):
    assert read(PLAN) == transfer.per_case_plans()
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(BASE / "launch.json")["model"]), directory)


def capture(directory):
    assert read(directory / "launch.json")["sha256"] == locks()
    done = read(directory / "complete.json")
    trace = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    assert digest(trace) == done["transcript_sha256"] and digest(final) == done["final_records_sha256"]
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == done["records"] == 10
    notes = {row["id"]: row for row in rows[:3]}
    expected = [*note_requests(), *writer_requests(notes)]
    for row, plan in zip(rows, expected, strict=True):
        assert all(row[key] == value for key, value in plan.items())
    assert read(final)[transfer.task()["id"]] == {row["id"]: row["output"] for row in rows}
    return notes, rows[3:]


def check_transport(notes, reviewed):
    fixture = transfer.task()
    source_bank = {row["id"]: row for row in fixture["optional_sources"]}
    assert set(notes) == set(reviewed)
    for name, row in notes.items():
        labels = reviewed[name]
        source = source_bank[row["evidence_ids"][0]]
        assert labels["reason"]
        assert set(labels["spans"]) <= {"faithful", "incomplete", "incorrect"}
        for spans in labels["spans"].values():
            assert all(quote and quote in row["output"] for quote in spans)
        assert all(quote and quote in source["text"] for quote in labels["source_spans"])
    return {name: {**label, "ended": notes[name]["ended"], "words": len(notes[name]["output"].split()),
                   "tokens": len(notes[name]["output_ids"])} for name, label in reviewed.items()}


def score(directory, annotations):
    notes, records = capture(directory)
    labels = read(annotations)
    note_review = check_transport(notes, labels["notes"])
    assert set(labels["rows"]) == {row["id"] for row in records}
    proofs = {row["id"]: {key: notes[f"note-{key}"]["output"] for key in row["evidence_ids"]} for row in records}
    for label, marks in labels["rows"].items():
        assert marks["met"].keys() == marks["note_support"].keys()
        for evidence in marks["note_support"].values():
            assert evidence and all(quote and quote in proofs[label][block] for block, quote in evidence.items())
    # Score one original arm only. Receipt indexing and all policy replays use the transfer scorer.
    with patch.object(transfer, "captured", return_value=records), patch.object(transfer, "ARMS", ("visible",)):
        scored = transfer.score(directory, PLAN, annotations)
    return {**scored, "notes": note_review, "verified_source_baseline_sha256": digest(WRITING_BASE)}


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
        print(json.dumps({"requests": list(note_requests()), "locks": locks(), "frozen_plan": digest(PLAN)},
                         indent=2, ensure_ascii=False))
