"""Give the implementation update a separate sentence and explicit owner."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import field_authority as parent

base = parent.base
runner = parent.runner
HERE = parent.HERE
TASK = (
    "Write exactly three short source-cited sentences. Begin sentence one with 'Resolution 2694 already authorized' "
    "and give Government–ELN monitoring and verification. Begin sentence two with 'The Council expressed willingness to consider' "
    "and give Government–EMC monitoring and verification if the Secretary-General confirms a ceasefire with appropriate "
    "verification protocols. Begin sentence three with 'The Council would take into account' and identify the "
    "Secretary-General's update on the implementation of resolution 2694. End with [ADDITIONAL]."
)


def plan():
    row, = [p for p in parent.plan() if p["id"] == "ADDITIONAL"]
    system, user = row["messages"]
    body = json.loads(user["content"])
    body["task"] = TASK
    yield {**row, "messages": [system, {**user, "content": json.dumps(body, ensure_ascii=False)}]}


def locks():
    return {**parent.locks(), Path(__file__).name: runner.digest(Path(__file__)),
            "authority_trial": runner.digest(HERE / "field-authority-evidence/transcript.jsonl")}


def episode(generate):
    return [{"family": "colombia-documentary-fields", "final": generate(list(plan()))}]


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        with patch.multiple(base, plan=plan, locks=locks, TASKS={"ADDITIONAL": TASK}):
            print(json.dumps({"records": len(base.replay(args.directory)), "exact_replay": True}, indent=2))
