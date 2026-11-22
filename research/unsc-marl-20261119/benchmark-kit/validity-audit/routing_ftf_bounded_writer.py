"""Test a source-by-source writing instruction with the transfer plans frozen."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_ftf_independence as independence
import routing_ftf_record as original

runner = original.runner
digest, read = original.digest, original.read
BASE = original.base.space.OUT / "ftf2020-record-transfer"
PLAN = BASE / "plan.json"
SILENT = BASE / "independent-plan.json"
GUIDE = (
    "Write a plain-language supplement of at most 75 words. Use one sentence per delivered annex, in its "
    "given order. For the US, state why it vetoed and preserve every stated destination for return. For Russia, "
    "preserve the reason for supporting the draft and its reservation. For Indonesia, name the representative "
    "and distinguish the national remarks from the vote notification in the Council President capacity. "
    "If both the US and Russian annexes are delivered, add one sentence explicitly comparing their shared "
    "concern and opposite votes. If either annex is absent, make no statement about that delegation's rationale "
    "or a shared concern. Keep each explanation attributable to its owner. Use the public record only for "
    "procedural context. Avoid restating the public record, attaching legal status to the failed draft, or "
    "describing whether evidence was supplied. Output only the requested sentences."
)


def requests():
    for row in original.requests():
        yield {**row, "messages": [{"role": "system", "content": GUIDE}, row["messages"][1]]}


def locks():
    paths = {"writer_script": Path(__file__), "team_plan": PLAN, "independent_plan": SILENT,
             "original_transcript": BASE / "transcript.jsonl", "original_scoring": BASE / "scores.json",
             "runner": Path(runner.__file__)}
    return {**original.locks(), **{name: digest(path) for name, path in paths.items()}}


def episode(generate):
    return [{"family": original.task()["id"], "final": generate(list(requests()))}]


def run(directory):
    planned = read(PLAN)
    assert planned["locks"] == original.locks()
    old = original.captured(BASE, PLAN)
    for row, request in zip(old, requests(), strict=True):
        assert request["messages"][1:] == row["messages"][1:]
        assert all(request[key] == row[key] for key in ("id", "evidence_ids", "cap"))
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(BASE / "launch.json")["model"]), directory)


def captured(directory, _plan_path=None):
    meta = read(directory / "launch.json")
    assert meta["sha256"] == locks()
    complete = read(directory / "complete.json")
    trace = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    assert digest(trace) == complete["transcript_sha256"] and digest(final) == complete["final_records_sha256"]
    records = list(map(json.loads, trace.read_text().splitlines()))
    assert len(records) == complete["records"] == 7
    for row, request in zip(records, requests(), strict=True):
        assert all(row[key] == value for key, value in request.items())
    assert read(final)[original.task()["id"]] == {row["id"]: row["output"] for row in records}
    return records


def score(directory, annotations):
    with patch.object(original, "captured", captured):
        return original.score(directory, PLAN, annotations)


def compare(scored_path):
    newer = independence.score(scored_path, SILENT)
    older = independence.score(BASE / "scores.json", SILENT)
    changes = {}
    for name, rows in newer["outcomes"].items():
        changes[name] = {label: {
            "original": older["outcomes"][name][label]["team_minus_independent"],
            "bounded": row["team_minus_independent"],
        } for label, row in rows.items()}
    return {"scores_sha256": digest(scored_path), "comparison": changes,
            "team_and_independent_plans": {"team": digest(PLAN), "independent": digest(SILENT)}}


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
