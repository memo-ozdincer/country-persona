"""Export held workshop cases, audit their controls, and score saved meetings."""

import argparse
from collections import Counter
import json
from pathlib import Path

from mandates import Mandates
from meeting import FLOOR
from recording import verify_aborted_run
from replay import replay
from run import HERE, pretty, simulate
from train_mandates import candidates, scripted


FAMILIES = json.loads((HERE / "held-cases.json").read_text())
WORLDS = ("feasible", "impasse")
SOL = "gpt-6.1-sol"
ASTRA = "gpt-6-astra"


def case_for(family, world):
    data = FAMILIES[family]
    allowed = data["allowed"].copy()
    if world == "impasse":
        allowed[data["focus_seat"]] = data["changed_mandate"]
    return {
        "title": data["title"], "source": data["source"],
        "brief": (f'{data["topic"]} Choose a package every participant can accept, or establish an '
                  "impasse by recording a checked exclusion for every package. All packages and "
                  "private mandates are fictional and carry no official commitments."),
        "draft": data["options"][data["opening"]],
        "delegations": {seat: ["Use this seat's fictional mandate."] for seat in data["allowed"]},
        "mandate_game": {"options": data["options"], "allowed": allowed},
    }


def checked_exchange(seat, prompt, schema):
    if schema is FLOOR:
        return {"action": "request_floor"}
    packet, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
    public = packet["public"]
    allowed = set(packet["private_mandate"]["allowed_packages"])
    rows, selected = candidates(public, seat, allowed)
    action, target = scripted(rows, selected, public, seat)
    text = target if action in ("propose", "rule_out") else "Record the checked decision."
    return {"action": action, "version": public["version"], "text": text}


def metrics(result, case):
    game = case["mandate_game"]
    package = next(label for label, text in game["options"].items() if text == case["draft"])
    incompatible = []
    for speech in result["history"]:
        if speech["action"] == "propose":
            package = speech["text"].strip()
        elif speech["action"] == "accept" and package not in game["allowed"][speech["country"]]:
            incompatible.append({"seat": speech["country"], "package": package, "version": speech["version"]})
    return {
        **result["mandate_score"], "status": result["status"],
        "speeches": len(result["history"]), "calls": result["calls"],
        "signatures": result["accepted"], "exclusions": result["exclusions"],
        "queue": result["queue"], "incompatible_signatures": incompatible,
    }


def exclusion_trace(result, case, order):
    """Trace public disclosures back to the seats that could make them."""
    mandates = Mandates.from_case(case, order)
    current = next(package for package, text in mandates.options.items() if text == case["draft"])
    turns = {seat: [] for seat in order}
    disclosures = {}
    excluded_proposals = []
    for speech_number, speech in enumerate(result["history"], 1):
        seat, action, text = speech["country"], speech["action"], speech["text"]
        turns[seat].append((speech_number, current))
        if action == "rule_out":
            disclosures[text] = (speech_number, current)
        elif action == "propose":
            if text in disclosures:
                excluded_proposals.append({"speech": speech_number, "seat": seat, "package": text,
                                           "excluded_on_speech": disclosures[text][0]})
            current = text

    unique = {}
    for package in mandates.options:
        holders = [seat for seat in order if package not in mandates.allowed[seat]]
        if len(holders) != 1:
            continue
        holder, = holders
        disclosed, draft_at_disclosure = disclosures.get(package, (None, None))
        earlier = [(turn, draft) for turn, draft in turns[holder] if disclosed is None or turn < disclosed]
        unique[package] = {"holder": holder, "disclosed_on_speech": disclosed,
                           "current_package_at_disclosure": draft_at_disclosure,
                           "earlier_holder_speeches": [turn for turn, _ in earlier],
                           "earlier_speeches_with_package_current": [turn for turn, draft in earlier
                                                                    if draft == package]}
    return {"sole_holder_exclusions": unique, "proposals_after_exclusion": excluded_proposals}


def audit():
    rows = []
    for family, data in FAMILIES.items():
        for world in WORLDS:
            case = case_for(family, world)
            for order in data["orders"]:
                assert len(set(order)) == len(order) and set(order) == set(data["allowed"])
                mandates = Mandates.from_case(case, order)
                expected = data["expected_feasible"] if world == "feasible" else []
                expected_vetoes = {option: [seat for seat in order if option not in mandates.allowed[seat]]
                                   for option in mandates.options}
                assert sorted(option for option, vetoes in expected_vetoes.items() if not vetoes) == expected
                result = simulate(case, order, "meeting", data["turn_cap"], False,
                                  checked_exchange, call_cap=data["call_cap"])
                assert result["mandate_score"]["feasible_packages"] == expected
                assert result["mandate_score"]["reward"] == 1
                rows.append({"family": family, "world": world, "order": order,
                             "veto_holders": expected_vetoes, **metrics(result, case)})
    return rows


def identify(settings):
    for family, data in FAMILIES.items():
        order = settings["countries"]
        if order not in data["orders"]:
            continue
        for world in WORLDS:
            case = settings["case"]
            if (case == case_for(family, world)
                    and list(case["mandate_game"]["options"]) == list(data["options"])):
                return family, world, data, order
    raise ValueError("Case and opening order do not match a registered cell")


def score(directories, trace=False):
    rows = {}
    completed = Counter()
    aborted = Counter()
    for directory in directories:
        settings = json.loads((directory / "settings.json").read_text())
        family, world, data, order = identify(settings)
        if (settings["mode"], settings["vote"], settings["turn_cap"], settings.get("call_cap")) != (
                "meeting", False, data["turn_cap"], data["call_cap"]):
            raise ValueError(f"Unregistered meeting budgets or mode in {directory}")
        default = settings["model"]
        other = {SOL: ASTRA, ASTRA: SOL}.get(default)
        overrides = settings.get("seat_models", {})
        if other is None or overrides not in ({}, {data["focus_seat"]: other}):
            raise ValueError(f"Unregistered model assignment in {directory}")
        assignment = "sol" if default == SOL else "astra"
        arm = f"{assignment}-with-focus-swap" if overrides else f"all-{assignment}"
        key = (family, world, order[0], arm)
        if key in rows:
            raise ValueError(f"Duplicate evaluation cell {key}")
        failure = {}
        if (directory / "result.json").is_file():
            result = replay(directory)
            completed[arm] += 1
        else:
            status, error, calls, public = verify_aborted_run(directory, settings, simulate)
            mandates = Mandates.from_case(settings["case"], order)
            terminal = mandates.score(status, public["draft"])
            terminal.update(outcome=status, reward=0 if status == "protocol_error" else None)
            result = dict(public, status=status, calls=calls, mandate_score=terminal)
            failure = {"recorded_error": error}
            aborted[arm] += 1
        rows[key] = {"family": family, "world": world, "order": order, "arm": arm,
                     "seat_models": {seat: overrides.get(seat, default) for seat in order},
                     **metrics(result, settings["case"]), **failure}
        if trace:
            rows[key]["exclusion_trace"] = exclusion_trace(result, settings["case"], order)

    pairs = []
    for family, world, opener, arm in sorted(rows):
        if not arm.endswith("-with-focus-swap"):
            continue
        baseline = (family, world, opener, f"all-{arm.split('-', 1)[0]}")
        if baseline in rows:
            swapped = rows[(family, world, opener, arm)]
            reference = rows[baseline]
            if swapped["reward"] is None or reference["reward"] is None:
                continue
            pairs.append({"family": family, "world": world, "opener": opener, "arm": arm,
                          "baseline": reference["arm"], "reward_delta": swapped["reward"] - reference["reward"],
                          "speech_delta": swapped["speeches"] - reference["speeches"],
                          "call_delta": swapped["calls"] - reference["calls"]})
    return {"registered_cells": sum(len(data["orders"]) for data in FAMILIES.values()) * len(WORLDS) * 4,
            "completed_by_arm": dict(sorted(completed.items())),
            **({"aborted_by_arm": dict(sorted(aborted.items()))} if aborted else {}),
            "meetings": [rows[key] for key in sorted(rows)], "matched_focus_swaps": pairs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("case")
    export.add_argument("family", choices=FAMILIES)
    export.add_argument("world", choices=WORLDS)
    commands.add_parser("audit")
    grading = commands.add_parser("score")
    grading.add_argument("directories", nargs="+", type=Path)
    grading.add_argument("--trace", action="store_true", help="Include exclusion and opportunity timing.")
    args = parser.parse_args()
    if args.command == "case":
        output = case_for(args.family, args.world)
    elif args.command == "audit":
        output = audit()
    else:
        output = score(args.directories, trace=args.trace)
    print(pretty(output))


if __name__ == "__main__":
    main()
