"""Test a geographic-scope instruction on the four India-bearing receipts."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_climate_transfer as transfer

runner, digest, read = transfer.runner, transfer.digest, transfer.read
BASE = transfer.base.space.OUT / "climate2021-writer-transfer"
PLAN = BASE / "plan.json"
archived_capture = transfer.captured
GUIDE = (
    " When naming any narrower alternative, describe the geographic scope and policy scope separately. "
    "Do not imply a subject-matter limit from a geographic limit."
)


def requests():
    for row in transfer.requests():
        if row["id"].startswith("visible-") and "india-explanation" in row["evidence_ids"]:
            messages = row["messages"]
            yield {**row, "messages": [
                {"role": "system", "content": messages[0]["content"] + GUIDE},
                messages[1],
            ]}


def locks():
    return {**transfer.locks(PLAN), "scope_script": digest(Path(__file__)),
            "prior_trace": digest(BASE / "transcript.jsonl"), "prior_scores": digest(BASE / "scores.json")}


def run(directory):
    archived_capture(BASE, PLAN)

    def episode(generate):
        return [{"family": transfer.task()["id"], "final": generate(list(requests()))}]

    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(BASE / "launch.json")["model"]), directory)


def captured(directory, _plan_path=None):
    assert read(directory / "launch.json")["sha256"] == locks()
    complete = read(directory / "complete.json")
    trace, final = directory / "transcript.jsonl", directory / "final-records.json"
    assert digest(trace) == complete["transcript_sha256"] and digest(final) == complete["final_records_sha256"]
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == complete["records"] == 4
    for observed, planned in zip(rows, requests(), strict=True):
        assert all(observed[k] == v for k, v in planned.items())
    replacement = {row["id"]: row for row in rows}
    assert read(final)[transfer.task()["id"]] == {k: v["output"] for k, v in replacement.items()}
    return [replacement.get(row["id"], row) for row in archived_capture(BASE, PLAN)]


def score(directory, annotations):
    with patch.object(transfer, "captured", captured):
        return transfer.score(directory, PLAN, annotations)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score", "check"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--annotations", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        result = score(args.directory, args.annotations) if args.mode == "score" else list(requests())
        print(json.dumps(result, indent=2, ensure_ascii=False))
