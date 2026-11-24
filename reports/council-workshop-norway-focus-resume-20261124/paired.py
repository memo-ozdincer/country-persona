"""Verify the resumed Norway-opening focus swap and the paired opener comparisons."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from held_suite import ASTRA, SOL, identify, score
from meeting import FLOOR
from recording import verify_aborted_run
from run import pretty, simulate


NORWAY = ROOT / "reports/council-workshop-norway-opening-20261123"
PREVIOUS = NORWAY / "sol-with-astra-norway-resumed"
GHANA = ROOT / "reports/council-workshop-held-pilot-20261123"
RESUMED = HERE / "mixed"


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


def plan():
    settings = read(PREVIOUS / "settings.json")
    family, world, _, order = identify(settings)
    assert (family, world, order) == ("guinea", "impasse", ["NOR", "GHA", "CHN"])
    assert settings["model"] == SOL and settings["seat_models"] == {"NOR": ASTRA}
    status, error, attempted, public = verify_aborted_run(PREVIOUS, settings, simulate)
    request = events(PREVIOUS)[-2]
    assert status == "call_error" and attempted == 6 and len(public["history"]) == 2
    assert request["schema"] == FLOOR and request["country"] == "NOR" and "429" in error
    return {"source": PREVIOUS.relative_to(ROOT).as_posix(), "reusable_replies": attempted - 1,
            "retry": request, "turn_cap": settings["turn_cap"], "call_cap": settings["call_cap"]}


def summarize(design):
    previous = events(PREVIOUS)
    resumed = events(RESUMED)
    reused = design["reusable_replies"]
    assert resumed[2 * reused] == previous[2 * reused] == design["retry"]
    for index in range(0, 2 * reused, 2):
        assert resumed[index] == previous[index]
        assert resumed[index + 1] == previous[index + 1] | {"reused": True}
    replies = [event for event in resumed[2 * reused:] if event["event"] == "response"]
    assert all(not event["reused"] for event in replies)
    settings = read(RESUMED / "settings.json")
    assert settings["resumed_from"] == design["source"]
    original_settings = read(PREVIOUS / "settings.json")
    for key in ("case", "countries", "model", "seat_models", "call_cap", "turn_cap", "call_timeout", "vote", "mode"):
        assert settings[key] == original_settings[key]
    arms = [GHANA / "all-sol", GHANA / "sol-with-astra-norway", NORWAY / "all-sol", RESUMED]
    prefix = structured_decisions(resumed)
    matching = sum(pair[0] == pair[1] for pair in zip(prefix, structured_decisions(events(NORWAY / "all-sol"))))
    return {"reused_replies": reused, "fresh_replies": len(replies), "matching_structured_decisions": matching,
            "comparison": score(arms, trace=True)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "score"))
    args = parser.parse_args()
    design = plan()
    if args.command == "plan":
        print(pretty(design))
    else:
        assert design == read(HERE / "plan.json")
        print(pretty(summarize(design)))
