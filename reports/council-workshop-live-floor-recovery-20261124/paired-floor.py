"""Compare the original floor prompt and an explicit queue reminder."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "council-workshop-gulf-cutoff-20261123"))

from paired import ARMS, ROOT, pretty, read, replay, replay_arm, run
from meeting import FLOOR


SOURCE = HERE.parent / "council-workshop-all-sol-matrix-20261123" / "iraq-uae-impasse"
SEARCH = HERE.parent / "council-workshop-exact-impasse-reachability-20261123" / "results.json"
REMINDER = (
    "Floor requests join the back of the existing queue and leave the order of already queued delegates intact. "
    "A delegate who is already queued is skipped in later floor polls. If joining now could save a later "
    "poll before the delegates ahead of you speak, you may request the floor for that reason as well."
)


def plan():
    settings = read(SOURCE / "settings.json")
    result = replay(SOURCE)
    assert result["status"] == "call_cap" and result["calls"] == 55 and len(result["history"]) == 15
    row, = [r for r in read(SEARCH)["meetings"] if r["path"] == SOURCE.relative_to(ROOT).as_posix()]
    witness = row["last_open_witness"]
    assert witness["reused_calls"] == 50 and witness["calls"] == 55
    changed, = [x for x in witness["new_decisions"] if x["call"] == 52]
    assert changed["seat"] == "FRA" and changed["answer"] == {"action": "request_floor"}
    events = [json.loads(line) for line in (SOURCE / "calls.jsonl").read_text().splitlines()]
    target, old = events[102:104]
    assert target["country"] == "FRA" and target["schema"] == FLOOR and old["answer"] == {"action": "pass"}
    return {"case_path": row["path"], "target_call": 52, "target_seat": "FRA", "reused_calls": 51,
            "target_speech": 15, "model": settings["model"], "turn_cap": settings["turn_cap"],
            "call_cap": settings["call_cap"], "archived_request": target, "archived_reply": old["answer"],
            "priority_suffix": REMINDER}


def score(design):
    rows = {}
    for arm in ARMS:
        result = replay_arm(arm, design, source=SOURCE, directory=HERE)
        request, reply = [json.loads(line) for line in (HERE / f"{arm}.jsonl").read_text().splitlines()[:2]]
        assert request["schema"] == FLOOR and request["country"] == "FRA"
        rows[arm] = {"first_fresh_reply": reply["answer"], **result}
    return rows


def budget_plan(design):
    call = design["target_call"]
    cap = design["call_cap"]
    cue = f" This floor request is call {call} of the {cap}-call budget. {cap - call} calls remain after your reply."
    return design | {"priority_suffix": design["priority_suffix"] + cue}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "run", "score", "budget-plan", "budget-run", "budget-replay"))
    parser.add_argument("arm", nargs="?", choices=ARMS)
    args = parser.parse_args()
    design = plan()
    if args.command == "plan":
        print(pretty(design))
    else:
        assert design == read(HERE / "plan.json")
        if args.command == "budget-plan":
            print(pretty(budget_plan(design)))
        elif args.command in ("budget-run", "budget-replay"):
            directory = HERE / "budget-cue"
            design = budget_plan(design)
            assert design == read(directory / "plan.json")
            action = run if args.command == "budget-run" else replay_arm
            print(pretty(action("priority", design, source=SOURCE, directory=directory)))
        elif args.command == "score":
            print(pretty(score(design)))
        elif args.arm is None:
            parser.error("Choose one arm")
        else:
            print(pretty(run(args.arm, design, source=SOURCE, directory=HERE)))
