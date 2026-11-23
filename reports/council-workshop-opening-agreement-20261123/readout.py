"""Compare live instructions and scripted controls under a tight speech budget."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from held_suite import case_for, checked_exchange, metrics
from mandates import Mandates
from meeting import FLOOR
from replay import replay
from run import pretty, simulate


def sign_opening(seat, prompt, schema):
    if schema is FLOOR:
        return {"action": "request_floor"}
    packet, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
    return {"action": "accept", "version": packet["public"]["version"], "text": "Accept the opening draft."}


def summarize(result, case):
    return {**metrics(result, case), "speech_actions": [
        {"seat": row["country"], "action": row["action"], "version": row["version"], "text": row["text"]}
        for row in result["history"]
    ]}


def readout():
    case = json.loads((HERE / "case.json").read_text())
    reference = case_for("guinea", "feasible")
    reference["title"] = "Gulf of Guinea briefing under a speaking deadline (fictional)"
    reference["brief"] += " The meeting has at most five speaking turns."
    reference["draft"] = reference["mandate_game"]["options"]["briefing"]
    allowed = reference["mandate_game"]["allowed"]
    allowed["NOR"] = [package for package in allowed["NOR"] if package != "regional"]
    assert case == reference
    order = ["GHA", "CHN", "NOR"]
    mandates = Mandates.from_case(case, order)
    feasible = set(mandates.options).intersection(*mandates.allowed.values())
    assert feasible == {"briefing"}
    exclusions_by_seat = {seat: mandates.options.keys() - mandates.allowed[seat] for seat in order}
    # Each seat must sign, and a policy that requires every available exclusion first
    # gives three different packages exclusively to those same seats to rule out.
    assert all(len(options) == 1 for options in exclusions_by_seat.values())
    assert set.union(*exclusions_by_seat.values()) == mandates.options.keys() - feasible
    output = {
        "sole_feasible_opening": "briefing", "exclusions_by_seat": {k: sorted(v) for k, v in exclusions_by_seat.items()},
        "turn_cap": 5, "call_cap": 24, "minimum_speeches_for_agreement": len(order),
        "minimum_speeches_if_all_follow_exclusions_first": len(order) + len(mandates.options) - len(feasible),
        "scripted": {}, "live": {},
    }
    for name, policy in (("sign_opening", sign_opening), ("exclusions_first", checked_exchange)):
        result = simulate(case, order, "meeting", 5, False, policy, call_cap=24)
        output["scripted"][name] = summarize(result, case)
    match = None
    for name in ("standard", "priority"):
        trace = HERE / name
        settings = json.loads((trace / "settings.json").read_text())
        assert settings["case"] == case and settings["countries"] == order
        assert (settings["turn_cap"], settings["call_cap"]) == (5, 24)
        assert settings.get("prioritize_exclusions", False) is (name == "priority")
        comparable = {k: v for k, v in settings.items() if k not in {"started", "prioritize_exclusions"}}
        if match is None:
            match = comparable
        else:
            assert comparable == match
        output["live"][name] = summarize(replay(trace), case)
    return output


if __name__ == "__main__":
    print(pretty(readout()))
