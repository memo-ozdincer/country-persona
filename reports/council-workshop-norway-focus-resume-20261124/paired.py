"""Verify the resumed Norway-opening focus swap and the paired opener comparisons."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from held_suite import ASTRA, SOL, identify, score
from meeting import FLOOR, PACKAGE_SPEECH
from recording import verify_aborted_run
from run import pretty, simulate


NORWAY = ROOT / "reports/council-workshop-norway-opening-20261123"
PREVIOUS = NORWAY / "sol-with-astra-norway-resumed"
GHANA = ROOT / "reports/council-workshop-held-pilot-20261123"
RESUMED = HERE / "mixed"
FOLLOWUP = HERE / "mixed-followup"
FINAL = HERE / "mixed-final"


def read(path):
    return json.loads(path.read_text())


def events(directory):
    return list(map(json.loads, (directory / "calls.jsonl").read_text().splitlines()))


def structured_decisions(log):
    decisions = []
    for event in log:
        if event["event"] != "response":
            continue
        reply = event["answer"]
        action = reply["action"]
        target = reply["text"] if action in ("propose", "rule_out") else None
        decisions.append((event["country"], action, reply.get("version"), target))
    return decisions


def plan(source, expected_calls, expected_speeches, schema=FLOOR):
    settings = read(source / "settings.json")
    family, world, _, order = identify(settings)
    assert (family, world, order) == ("guinea", "impasse", ["NOR", "GHA", "CHN"])
    assert settings["model"] == SOL and settings["seat_models"] == {"NOR": ASTRA}
    status, error, attempted, public = verify_aborted_run(source, settings, simulate)
    request = events(source)[-2]
    assert status == "call_error" and attempted == expected_calls and len(public["history"]) == expected_speeches
    assert request["schema"] == schema and request["country"] == "NOR" and "429" in error
    return {"source": source.relative_to(ROOT).as_posix(), "reusable_replies": attempted - 1,
            "retry": request, "turn_cap": settings["turn_cap"], "call_cap": settings["call_cap"]}


def summarize(design, target):
    source = ROOT / design["source"]
    previous = events(source)
    resumed = events(target)
    reused = design["reusable_replies"]
    assert resumed[2 * reused] == previous[2 * reused] == design["retry"]
    for index in range(0, 2 * reused, 2):
        assert resumed[index] == previous[index]
        assert resumed[index + 1] == previous[index + 1] | {"reused": True}
    replies = [event for event in resumed[2 * reused:] if event["event"] == "response"]
    assert all(not event["reused"] for event in replies)
    settings = read(target / "settings.json")
    assert settings["resumed_from"] == design["source"]
    original_settings = read(source / "settings.json")
    for key in ("case", "countries", "model", "seat_models", "call_cap", "turn_cap", "call_timeout", "vote", "mode"):
        assert settings[key] == original_settings[key]
    arms = [GHANA / "all-sol", GHANA / "sol-with-astra-norway", NORWAY / "all-sol", target]
    decisions = list(zip(structured_decisions(events(NORWAY / "all-sol")), structured_decisions(resumed)))
    matching = sum(reference == mixed for reference, mixed in decisions)
    summary = {"reused_replies": reused, "fresh_replies": len(replies), "matching_structured_decisions": matching,
               "comparison": score(arms, trace=True)}
    if target != RESUMED:
        summary["first_structured_difference"] = next(
            ({"call": index, "all_sol": reference, "mixed": mixed}
             for index, (reference, mixed) in enumerate(decisions, 1) if reference != mixed),
            None,
        )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "score"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--followup", action="store_true")
    stage.add_argument("--final", action="store_true")
    args = parser.parse_args()
    if args.final:
        design = plan(FOLLOWUP, 25, 9, PACKAGE_SPEECH)
        frozen_plan = HERE / "final-plan.json"
        target = FINAL
    elif args.followup:
        design = plan(RESUMED, 13, 4)
        frozen_plan = HERE / "followup-plan.json"
        target = FOLLOWUP
    else:
        design = plan(PREVIOUS, 6, 2)
        frozen_plan = HERE / "plan.json"
        target = RESUMED
    if args.command == "plan":
        print(pretty(design))
    else:
        assert design == read(frozen_plan)
        print(pretty(summarize(design, target)))
