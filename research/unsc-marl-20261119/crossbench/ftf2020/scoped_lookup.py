"""Retrieve archive cards only after the independently measured scope gate."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import role_lookup as initial
import scope_gate

HERE = initial.HERE
partner = initial.partner
ORDERS = tuple(tuple(key for key in order if key != "ambiguous") for order in initial.ORDER)
GUIDE = (
    "Select the archive card that matches the action requested. A person's policy explanation and their act as "
    "Council President are different. Use the candidate descriptions to identify exactly one card. "
    "Return only its one-letter identifier."
)


def verdicts():
    return partner.read(HERE / "scope-evidence/results.json")["results"]


def requests():
    passed = verdicts()
    for name, (assignment, _) in initial.examples().items():
        if passed[name]["scoped"] is not True:
            continue
        for i, order in enumerate(ORDERS):
            offered = dict(zip("ABCD", (initial.CANDIDATES[key] for key in order), strict=True))
            yield partner.replay.request(f"{name}/{i}", 4, GUIDE,
                                         {"assignment": assignment, "archive_cards": offered}, [])


def episode(generate):
    rows = {}
    for group in batched(requests(), 6):
        rows.update(generate(list(group)))
    return [{"family": initial.old.corroboration.load()["id"], "final": rows}]


def locks():
    return {**scope_gate.locks(), "scoped_lookup": partner.digest(Path(__file__)),
            "scope_decisions": partner.digest(HERE / "scope-evidence/results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    scope = verdicts()
    results = {}
    for key, (_, truth) in initial.examples().items():
        accepted = scope[key]["scoped"] is True
        votes = []
        if accepted:
            for i, order in enumerate(ORDERS):
                row = rows[f"{key}/{i}"]
                votes.append(initial.decode(row, order) if row["output"] in tuple("ABCD") else None)
        selected = votes[0] if votes and votes[0] == votes[1] else None
        results[key] = {"scoped": accepted, "labels": votes, "chosen": selected, "reference": truth,
                        "safe_and_correct": selected == truth if truth != "ambiguous" else selected is None}
    return {"scope": "Check scope first. Then make two independent label-swapped choices over the four authenticated "
                     "archive cards. A failed scope check or unstable choice emits no focal selection.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "records": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
