"""Replay the Gaza writer bank with stricter evidence boundaries."""
import argparse
import json
from pathlib import Path
from runpy import run_path
from unittest.mock import patch

import writer

EVIDENCE = writer.HERE / "writer-evidence"
GUIDE = (
    "Write only the supplementary text for the focal item, in at most 85 words. "
    "First report just the focal slip. If there is an archival backup, add only its documented focal content. "
    "Use the public paragraph only to resolve references. It is already in the record. Do not repeat its tally or "
    "borrow its cause of failure for another document. Report each disposition only with its stated cause. "
    "For proposed language use explicit attribution such as 'the amendment would have' or 'the draft proposed'. "
    "For a national explanation, state only what the named representative said. Do not say an explanation was sole, "
    "exhaustive or absent. Follow the coverage list within the supplied evidence. Stop after covering it."
)
archived_requests = writer.requests
archived_locks = writer.locks


def requests():
    for row in archived_requests():
        yield {**row, "messages": [{"role": "system", "content": GUIDE}, row["messages"][1]]}


def locks():
    return {**archived_locks(), "scoped_writer.py": writer.digest(Path(__file__)),
            "original_trace": writer.digest(EVIDENCE / "transcript.jsonl")}


def run(directory):
    with patch.object(writer, "requests", requests), patch.object(writer, "locks", locks):
        writer.run(directory)


def verify(directory):
    with patch.object(writer, "requests", requests), patch.object(writer, "locks", locks):
        return writer.verify(directory)


def evaluate(directory):
    with patch.object(writer, "requests", requests), patch.object(writer, "locks", locks):
        score_bank = run_path(str(writer.HERE / "score.py"))["run"]
        return score_bank(directory, directory / "annotations.json")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    elif args.mode == "verify":
        print(json.dumps({key: row["output"] for key, row in verify(args.directory).items()}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(evaluate(args.directory), indent=2, ensure_ascii=False))
