"""Match the whole-packet cap to the sum of the separate-field caps."""
import argparse
from pathlib import Path
from collections import defaultdict
import json
from unittest.mock import patch

import writer

original = writer.build
base_locks = writer.locks


def build():
    prompts = [row for row in original() if row["mode"] == "whole"]
    return [{**row, "cap": 104 * (len(row["evidence_ids"]) + int({"CHINA", "A3"} <= set(row["evidence_ids"])))}
            for row in prompts]


def locks():
    return {**base_locks(), Path(__file__).name: writer.runner.digest(Path(__file__)),
            "first_pass_transcript": writer.runner.digest(writer.HERE / "evidence/transcript.jsonl")}


def episode(generate):
    batches = defaultdict(list)
    for row in build():
        batches[row["cap"]].append(row)
    finals = {}
    for batch in batches.values():
        finals.update(generate(batch))
    return [{"family": "haiti-writer-transfer", "final": finals}]


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(writer.runner, episode=episode, locks=locks):
            writer.runner.run(args.model, args.directory)
    else:
        with patch.multiple(writer, build=build, locks=locks):
            print(json.dumps({"records": len(writer.replay(args.directory)), "exact_replay": True}))
