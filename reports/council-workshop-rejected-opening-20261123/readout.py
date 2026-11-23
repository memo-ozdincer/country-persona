"""Replay a feasible replacement case after an opening-draft rejection."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from held_suite import checked_exchange, metrics
from mandates import Mandates
from meeting import FLOOR
from replay import replay
from run import pretty, simulate


def scripted_policy(repair_first, seat, prompt, schema):
    if schema is FLOOR:
        return {"action": "request_floor"}
    packet, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
    public = packet["public"]
    if public["exclusions"] and not repair_first:
        return checked_exchange(seat, prompt, schema)
    allowed = set(packet["private_mandate"]["allowed_packages"])
    current = next(key for key, text in public["options"].items() if text == public["draft"])
    if current in public["exclusions"]:
        action, text = "propose", min(allowed - public["exclusions"].keys())
    elif current not in allowed:
        action, text = "rule_out", current
    else:
        action, text = "accept", "Accept the current draft."
    return {"action": action, "version": public["version"], "text": text}


def summary(result, case):
    return {**metrics(result, case), "speech_actions": [
        {"seat": row["country"], "action": row["action"], "version": row["resulting_version"], "text": row["text"]}
        for row in result["history"]
    ]}


def readout():
    case = json.loads((HERE / "case.json").read_text())
    previous = HERE.parent / "council-workshop-opening-agreement-20261123" / "case.json"
    reference = json.loads(previous.read_text())
    assert reference["draft"] == case["mandate_game"]["options"]["briefing"]
    assert case == reference | {"draft": reference["mandate_game"]["options"]["review"]}
    order = ["GHA", "CHN", "NOR"]
    mandates = Mandates.from_case(case, order)
    feasible = set(mandates.options).intersection(*mandates.allowed.values())
    assert feasible == {"briefing"}
    exclusions = {seat: mandates.options.keys() - mandates.allowed[seat] for seat in order}
    assert exclusions == {"GHA": {"review"}, "CHN": {"coastal"}, "NOR": {"regional"}}
    result = {"opening": "review", "feasible_packages": sorted(feasible), "turn_cap": 5, "call_cap": 24,
              "repair_after_one_exclusion_minimum_speeches": 1 + 1 + len(order),
              "exclusions_first_minimum_speeches": len(exclusions) + 1 + len(order), "scripted": {}, "live": {}}
    for repair_first, name in ((True, "repair_first"), (False, "after_rejection")):
        def decide(seat, prompt, schema):
            return scripted_policy(repair_first, seat, prompt, schema)

        simulated = simulate(case, order, "meeting", 5, False, decide, call_cap=24)
        result["scripted"][name] = summary(simulated, case)
    baseline = None
    for name in ("standard", "after-rejection"):
        directory = HERE / name
        settings = json.loads((directory / "settings.json").read_text())
        assert settings["case"] == case and settings["countries"] == order
        assert (settings["turn_cap"], settings["call_cap"]) == (5, 24)
        assert settings.get("prioritize_exclusions_after_rejection", False) is (name == "after-rejection")
        comparable = {k: v for k, v in settings.items() if k not in {"started", "prioritize_exclusions_after_rejection"}}
        if baseline is None:
            baseline = comparable
        assert comparable == baseline
        result["live"][name] = summary(replay(directory), case)
    return result


if __name__ == "__main__":
    print(pretty(readout()))
