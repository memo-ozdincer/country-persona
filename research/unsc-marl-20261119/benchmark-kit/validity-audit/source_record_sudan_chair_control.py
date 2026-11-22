"""Replay the Sudan chair with paired draft and dossier-order controls."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as runner

ARCHIVE = Path(__file__).resolve().parent.parent / "evidence" / "source-record-sudan"
ARMS = ("independent_drafts", "interactive", "draft_free")
ORDERS = ("original", "reversed")


def archived_rows():
    path = ARCHIVE / "transcript.jsonl"
    complete = json.loads((ARCHIVE / "complete.json").read_text())
    assert runner.digest(path) == complete["transcript_sha256"]
    rows = {row["id"].split("/", 1)[1]: row for row in map(json.loads, path.read_text().splitlines())}
    assert len(rows) == complete["records"]
    return rows


def requests():
    archived = archived_rows()
    chair = {arm: archived[f"{arm}/chair"] for arm in ARMS[:2]}
    system = chair["independent_drafts"]["messages"][0]
    bodies = {arm: json.loads(row["messages"][1]["content"]) for arm, row in chair.items()}
    reference = bodies["independent_drafts"]
    assert chair["interactive"]["messages"][0] == system
    assert reference["evidence"] == bodies["interactive"]["evidence"]
    assert reference["task"] == bodies["interactive"]["task"]
    assert reference["working_text"][1] == bodies["interactive"]["working_text"][1]
    assert reference["working_text"][0] != bodies["interactive"]["working_text"][0]
    assert chair["independent_drafts"]["cap"] == chair["interactive"]["cap"]
    bodies["draft_free"] = {**reference, "working_text": []}
    plans = []
    for order in ORDERS:
        for arm in ARMS:
            body = bodies[arm]
            seed = chair.get(arm, chair["independent_drafts"])
            if order == "reversed":
                body = {**body, "evidence": dict(reversed(tuple(body["evidence"].items())))}
            messages = [system, {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]
            if order == "original" and arm != "draft_free":
                assert messages == seed["messages"]
            plans.append({
                "id": f"sudan-chair-control/{order}/{arm}", "messages": messages, "cap": seed["cap"],
                "evidence_ids": list(body["evidence"]),
                "seen": [] if arm == "draft_free" else seed["seen"],
            })
    return plans


def episode(generate):
    return [{"family": "sudan-chair-control", "final": generate(requests())}]


def locks():
    paths = [Path(__file__), Path(runner.__file__), ARCHIVE / "transcript.jsonl", ARCHIVE / "launch.json"]
    return {p.name: runner.digest(p) for p in paths}


def replay(directory):
    complete = json.loads((directory / "complete.json").read_text())
    trace = directory / "transcript.jsonl"
    finals = directory / "final-records.json"
    assert runner.digest(trace) == complete["transcript_sha256"]
    assert runner.digest(finals) == complete["final_records_sha256"]
    assert json.loads((directory / "launch.json").read_text())["sha256"] == locks()
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == complete["records"] == 6
    for observed, planned in zip(rows, requests(), strict=True):
        assert all(observed[k] == v for k, v in planned.items())
        assert 0 < len(observed["output_ids"]) <= observed["cap"]
    original = archived_rows()
    same_output = {
        arm: row["output_ids"] == original[f"{arm}/chair"]["output_ids"]
        for arm, row in zip(ARMS[:2], rows[:2], strict=True)
    }
    assert json.loads(finals.read_text()) == {"sudan-chair-control": {r["id"]: r["output"] for r in rows}}
    return {
        "same_output_as_archived": same_output,
        "arm_order": [r["id"] for r in rows],
        "stats": {r["id"]: {"input_tokens": len(r["input_ids"]), "output_tokens": len(r["output_ids"]),
                            "ended": r["ended"]} for r in rows},
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay", "check"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps([{"id": r["id"], "evidence": r["evidence_ids"], "cap": r["cap"]} for r in requests()]))
    elif args.mode == "replay":
        print(json.dumps(replay(args.directory), indent=2))
    else:
        model = Path(json.loads((ARCHIVE / "launch.json").read_text())["model"])
        with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
            runner.run(model, args.directory)
