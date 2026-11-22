"""Test one source-local extract per majority-confirmed attribution."""
import argparse
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_attribution_choices as first

HERE = first.HERE
ARCHIVE = HERE / "facilitator-attribution-choices-evidence"
FAMILY = "facilitator-attribution-extracts"
CAP = 100
runner = first.runner
TASK = (
    "Copy the shortest complete sentence from the source card that establishes the selected report. "
    "Keep the qualification, mechanism, duration or timing if it matters to the reported position. "
    "Use only contiguous source words with their original wording and punctuation. "
    "Output the copied sentence alone. If the selected report is not established by the card, return no witness."
)


def archived():
    trace = ARCHIVE / "transcript.jsonl"
    finished = json.loads((ARCHIVE / "complete.json").read_text())
    assert runner.digest(trace) == finished["transcript_sha256"]
    result = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    assert len(result) == finished["records"]
    return result


def majority():
    reads = first.readings(archived())
    return {key: next((rel for rel, count in Counter(row["observations"]).items()
                      if rel is not None and count >= 2), "unknown")
            for key, row in reads.items()}


def requests():
    choices = majority()
    for name, scenario in first.panels():
        for i, source in enumerate(scenario["sources"], 1):
            key = f"{name}/S{i}"
            status = choices[key]
            if status != "unknown":
                alternatives = first.alternatives(scenario, source["actor"])
                selected = alternatives[first.RELATIONS.index(status)]
                yield first.transfer.prompt(key, CAP, TASK, {"source_card": source["card"], "selected_report": selected})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def pins():
    result = first.pins()
    for file in (Path(__file__), ARCHIVE / "transcript.jsonl", ARCHIVE / "launch.json", ARCHIVE / "complete.json"):
        result[str(file.resolve().relative_to(HERE.parents[1]))] = runner.digest(file)
    return result


def verify(directory):
    locks = pins()
    module = first.transfer.chair
    with patch.multiple(module, pins=lambda: locks, requests=requests, CAP=CAP, FAMILY=FAMILY):
        return module.rows(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
