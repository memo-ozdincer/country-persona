"""Normalize the assignment's source type before applying a desk's local rule."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import language_partner as text

GUIDE = (
    "Classify the material being requested in the assignment. DRAFT means wording that belongs to the draft "
    "instrument itself, such as an operative paragraph. STATEMENT means a national representative's account, "
    "reason for a vote or description of their country's views. Words like reconstruct or check do not change "
    "the kind of material requested. Return exactly DRAFT or STATEMENT."
)
POLICY = {"draft_desk": "DRAFT", "statement_desk": "STATEMENT"}


def requests():
    for phase in ("probe", "mission"):
        for focus in text.load()["focuses"]:
            yield text.replay.request(f"{phase}/{focus['id']}", 24, GUIDE, {"assignment": focus[phase]}, [])


def episode(generate):
    rows = {}
    for group in batched(requests(), 4):
        rows.update(generate(list(group)))
    return [{"family": text.load()["id"], "final": rows}]


def locks():
    return {**text.locks(), "factored_partner": text.digest(Path(__file__)),
            "mixed_actions": text.digest(text.HERE / "language-evidence/actions.json")}


def run(directory):
    with patch.object(text.runner, "episode", episode), patch.object(text.runner, "locks", locks):
        text.runner.run(Path(text.read(text.writer.MODEL)["model"]), directory)


def score(directory):
    with patch.object(text.replay, "episode", episode), patch.object(text.replay, "locks", locks):
        rows = text.replay.verify(directory)
    classes = {}
    for phase in ("probe", "mission"):
        classes[phase] = []
        for focus in text.load()["focuses"]:
            result = rows[f"{phase}/{focus['id']}"]
            valid = result["ended"] and result["output"] in ("DRAFT", "STATEMENT")
            classes[phase].append(result["output"] if valid else None)
    return {"scope": "The model returns an archival source category. The declared desk rule then deterministically "
                     "emits the exact permitted natural-language request or silence. A null is invalid model output.",
            "trace_sha256": text.digest(directory / "transcript.jsonl"), "classes": classes,
            "desks": {desk: {phase: [int(value == category) if value is not None else None for value in values]
                             for phase, values in classes.items()} for desk, category in POLICY.items()},
            "generated_tokens": sum(len(row["output_ids"]) for row in rows.values()),
            "input_tokens": sum(len(row["input_ids"]) for row in rows.values())}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
