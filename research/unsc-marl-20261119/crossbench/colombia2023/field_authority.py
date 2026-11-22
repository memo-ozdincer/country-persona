"""Keep the institutional decision maker explicit in the final two fields."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import field_revision as revision

base = revision.base
runner = revision.runner
HERE = revision.HERE
REQUESTS = {
    "ADDITIONAL": ("Write two sentences in at most 57 words. Start the first with 'Resolution 2694 already authorized' and name "
                   "both monitoring and verification of the Government–ELN ceasefire. Start the second with 'The Council expressed "
                   "willingness to consider' and preserve the EMC scope, confirmation with appropriate verification protocols and "
                   "the 2694 implementation update the Council takes into account. Finish with [ADDITIONAL]."),
    "overlap": ("In at most 29 words, state that Brazil and the A3 support a possible conditional future EMC verification role "
                "and that resolution 2704 granted no EMC authority. Use ordinary diplomatic prose. "
                "Finish with [BRAZIL, A3, ADDITIONAL]."),
}


def plan():
    for row in revision.plans():
        if row["id"] not in REQUESTS:
            continue
        system, user = row["messages"]
        content = json.loads(user["content"])
        content["task"] = REQUESTS[row["id"]]
        yield {**row, "messages": [system, {**user, "content": json.dumps(content, ensure_ascii=False)}]}


def locks():
    return {**revision.locks(), Path(__file__).name: runner.digest(Path(__file__)),
            "previous_revision": runner.digest(HERE / "field-revision-evidence/transcript.jsonl")}


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
        with patch.multiple(base, plan=plan, locks=locks, TASKS=REQUESTS):
            print(json.dumps({"records": len(base.replay(args.directory)), "exact_replay": True}, indent=2))
