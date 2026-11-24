"""Verify the registered Iraq focus-seat resume and its recorded comparison."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from held_suite import ASTRA, SOL, identify, score
from meeting import PACKAGE_SPEECH
from recording import verify_aborted_run
from run import pretty, simulate


PILOT = ROOT / "reports/council-workshop-iraq-pilot-20261123"
SOURCE = PILOT / "sol-with-astra-uae-resumed"
TARGET = HERE / "mixed"


def read(path):
    return json.loads(path.read_text())


def events(path):
    return list(map(json.loads, (path / "calls.jsonl").read_text().splitlines()))


def plan():
    settings = read(SOURCE / "settings.json")
    family, world, _, order = identify(settings)
    assert (family, world, order[0]) == ("iraq", "impasse", "FRA")
    assert settings["model"] == SOL and settings["seat_models"] == {"ARE": ASTRA}
    status, error, attempted, public = verify_aborted_run(SOURCE, settings, simulate)
    request = events(SOURCE)[-2]
    assert status == "call_error" and "429" in error and attempted == 26
    assert len(public["history"]) == 5 and request["schema"] == PACKAGE_SPEECH and request["country"] == "ARE"
    return {"source": SOURCE.relative_to(ROOT).as_posix(), "reused_replies": attempted - 1,
            "retry": request, "turn_cap": settings["turn_cap"], "call_cap": settings["call_cap"]}


def structured_decisions(log):
    for request, response in zip(log[::2], log[1::2], strict=True):
        if response["event"] != "response":
            break
        reply = response["answer"]
        action = reply["action"]
        yield {"seat": request["country"], "action": action, "version": reply.get("version"),
               "package": reply["text"] if action in ("rule_out", "propose") else None}


def summarize(design):
    old_settings, settings = (read(path / "settings.json") for path in (SOURCE, TARGET))
    ignored = {"started", "codex", "resumed_from"}
    assert {k: v for k, v in old_settings.items() if k not in ignored} == {
        k: v for k, v in settings.items() if k not in ignored
    }
    assert settings["resumed_from"] == design["source"]
    archived, current = events(SOURCE), events(TARGET)
    end = 2 * design["reused_replies"]
    expected = [event | {"reused": True} if event["event"] == "response" else event for event in archived[:end]]
    assert current[:end] == expected and current[end] == archived[end] == design["retry"]
    replies = [event for event in current[end:] if event["event"] == "response"]
    assert all(not event["reused"] for event in replies)
    choices = zip(structured_decisions(events(PILOT / "all-sol")), structured_decisions(current))
    first_difference = next(
        ({"call": index, "all_sol": baseline, "mixed": mixed}
         for index, (baseline, mixed) in enumerate(choices, 1) if baseline != mixed),
        None,
    )
    return {"reused_replies": design["reused_replies"], "fresh_replies": len(replies),
            "first_structured_difference": first_difference,
            "comparison": score([PILOT / "all-sol", TARGET], trace=True)}


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
