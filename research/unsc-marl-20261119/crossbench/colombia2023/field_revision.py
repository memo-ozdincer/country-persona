"""Repair observed omissions and project the comparison to claims the sources share."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import field_writer as base

original_plan = base.plan
original_locks = base.locks
runner = base.parent.runner
HERE = base.HERE
REVISION = {
    "ADDITIONAL": ("Write two short sentences, ending with [ADDITIONAL]. First explicitly state that Resolution 2694 already "
                   "authorized both monitoring and verification of the Government–ELN ceasefire. Second record willingness to "
                   "consider Government–EMC verification upon the Secretary-General's confirmation of a ceasefire with "
                   "appropriate verification protocols, taking into account his update on implementation of Resolution 2694. End."),
    "BRAZIL": ("Write two short sentences, ending with [BRAZIL]. Identify the presiding representative speaking nationally "
               "for Brazil and say that the Council should follow the priorities expressed by Colombia's Government. Preserve "
               "Brazil's hope that the Council could authorize EMC verification later when sufficiently mature. End."),
    "overlap": "Write the shared position and actual legal status in two short sentences. Cite [BRAZIL, A3, ADDITIONAL]. End.",
}


def plans():
    for row in original_plan():
        label = row["id"]
        if label not in REVISION:
            continue
        role, user = row["messages"]
        body = json.loads(user["content"])
        if label == "overlap":
            fields = body["documentary_fields"]
            assert "hopes" in fields["BRAZIL"]["future position"]
            assert "contingent" in fields["A3"]["future position"]
            assert "no verification granted here" in fields["ADDITIONAL"]["Government–EMC legal stage"]
            body = {"authorized_comparison_fields": {
                "BRAZIL": {"position": "supports a possible future Government–EMC verification role subject to a condition"},
                "A3": {"position": "supports a possible future Government–EMC verification role subject to a condition"},
                "ADDITIONAL": {"resolution 2704 (2023)": "willingness to consider that role, with no EMC verification authority granted"},
            }}
        body["task"] = "Write an archival record field using the supplied evidence. " + REVISION[label]
        yield {**row, "seen": [] if label == "overlap" else row["seen"],
               "messages": [role, {**user, "content": json.dumps(body, ensure_ascii=False)}]}


def locks():
    return {**original_locks(), Path(__file__).name: runner.digest(Path(__file__)),
            "initial_field_trace": runner.digest(HERE / "field-evidence/transcript.jsonl")}


def episode(generate):
    return [{"family": "colombia-documentary-fields", "final": generate(list(plans()))}]


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
        with patch.multiple(base, plan=plans, locks=locks, TASKS=REVISION):
            print(json.dumps({"records": len(base.replay(args.directory)), "exact_replay": True}, indent=2))
