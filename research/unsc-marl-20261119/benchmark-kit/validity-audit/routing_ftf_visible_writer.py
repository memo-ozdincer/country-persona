"""Scope writing instructions to delivered annexes while preserving the routing plans."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_ftf_bounded_writer as bounded

original, runner, read, digest = bounded.original, bounded.runner, bounded.read, bounded.digest
PREVIOUS = original.base.space.OUT / "ftf2020-bounded-writer"

ROLE_GUIDES = {
    "us-explanation": "For the US, state why it vetoed and preserve every stated destination for return.",
    "russia-explanation": "For Russia, preserve the reason for supporting the draft and its reservation.",
    "indonesia-explanation": "For Indonesia, name the representative and distinguish the national remarks from the vote notification in the Council President capacity.",
}
BRIDGE = "If both the US and Russian annexes are delivered, add one sentence explicitly comparing their shared concern and opposite votes."
MISSING = "If either annex is absent, make no statement about that delegation's rationale or a shared concern."


def requests():
    for row in bounded.requests():
        ids = set(row["evidence_ids"])
        if len(ids) == len(ROLE_GUIDES):
            continue
        text = bounded.GUIDE
        for key, phrase in ROLE_GUIDES.items():
            assert text.count(phrase) == 1
            if key not in ids:
                text = text.replace(phrase + " ", "")
        if not {"us-explanation", "russia-explanation"} <= ids:
            assert BRIDGE in text and MISSING in text
            text = text.replace(BRIDGE + " " + MISSING, "Cover only the delivered annexes.")
        yield {**row, "messages": [{"role": "system", "content": text}, row["messages"][1]]}


def locks():
    return {**bounded.locks(), "visible_prompt_script": digest(Path(__file__)),
            "previous_trace_sha256": digest(PREVIOUS / "transcript.jsonl")}


def episode(generate):
    return [{"family": original.task()["id"], "final": generate(list(requests()))}]


def run(directory):
    before = {r["id"]: r for r in bounded.captured(PREVIOUS)}
    for request in requests():
        row = before[request["id"]]
        assert request["messages"][1:] == row["messages"][1:]
        assert all(request[key] == row[key] for key in ("id", "evidence_ids", "cap"))
        assert request["messages"][0] != row["messages"][0]
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(PREVIOUS / "launch.json")["model"]), directory)


def captured(directory, _plan_path=None):
    meta = read(directory / "launch.json")
    assert meta["sha256"] == locks()
    complete = read(directory / "complete.json")
    trace, final = directory / "transcript.jsonl", directory / "final-records.json"
    assert digest(trace) == complete["transcript_sha256"] and digest(final) == complete["final_records_sha256"]
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == complete["records"] == 6
    for row, request in zip(rows, requests(), strict=True):
        assert all(row[key] == value for key, value in request.items())
    assert read(final)[original.task()["id"]] == {row["id"]: row["output"] for row in rows}
    full = bounded.captured(PREVIOUS)[-1]
    assert full["id"] == "receipt-7" and all(full[k] == v for k, v in list(bounded.requests())[-1].items())
    return [*rows, full]


def score(directory, annotations):
    with patch.object(original, "captured", captured):
        return {**original.score(directory, bounded.PLAN, annotations),
                "reused_full_receipt_bank_sha256": digest(PREVIOUS / "transcript.jsonl")}


def compare(path):
    staged = {"original": bounded.BASE / "scores.json", "all_role_instructions": PREVIOUS / "scores.json",
              "delivered_role_instructions": path}
    comparisons = {name: bounded.independence.score(scores, bounded.SILENT)["outcomes"]
                   for name, scores in staged.items()}
    return {"reported_scores_hashes": {name: digest(path) for name, path in staged.items()},
            "comparisons": comparisons}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score", "compare"))
    cli.add_argument("path", type=Path, nargs="?")
    cli.add_argument("--annotations", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.path)
    else:
        if args.mode == "score":
            result = score(args.path, args.annotations)
        elif args.mode == "compare":
            result = compare(args.path)
        else:
            result = list(requests())
        print(json.dumps(result, indent=2, ensure_ascii=False))
