"""Verify the eight Gulf meetings in the all-Sol and focus-swap comparison."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from held_suite import ASTRA, SOL, case_for, identify, score
from mandates import Mandates
from run import pretty


REPORTS = ROOT / "reports"
GHANA = REPORTS / "council-workshop-held-pilot-20261123"
NORWAY_FEASIBLE = REPORTS / "council-workshop-all-sol-matrix-20261123" / "guinea-norway-feasible"
NORWAY_IMPASSE = REPORTS / "council-workshop-norway-opening-20261123" / "all-sol"
NORWAY_MIXED_IMPASSE = REPORTS / "council-workshop-norway-focus-resume-20261124" / "mixed-final"


def read(path):
    return json.loads(path.read_text())


def plan():
    settings = read(NORWAY_FEASIBLE / "settings.json")
    family, world, registered, order = identify(settings)
    assert (family, world, order[0]) == ("guinea", "feasible", "NOR")
    feasible = Mandates.from_case(case_for(family, "feasible"), order)
    impasse = Mandates.from_case(case_for(family, "impasse"), order)
    assert feasible.options == impasse.options
    changes = {seat: sorted(feasible.allowed[seat] - impasse.allowed[seat])
               for seat in order if feasible.allowed[seat] != impasse.allowed[seat]}
    assert changes == {"NOR": ["briefing", "regional"]} and impasse.allowed["NOR"] <= feasible.allowed["NOR"]
    feasible_packages = sorted(set(feasible.options).intersection(*feasible.allowed.values()))
    impasse_packages = sorted(set(impasse.options).intersection(*impasse.allowed.values()))
    assert feasible_packages == ["briefing", "regional"] and not impasse_packages
    return {"countries": order, "model": SOL, "seat_models": {"NOR": ASTRA},
            "turn_cap": registered["turn_cap"], "call_cap": registered["call_cap"], "case_delta": changes,
            "feasible_packages": {"feasible": feasible_packages, "impasse": impasse_packages}}


def compare(design):
    target = HERE / "mixed"
    settings = read(target / "settings.json")
    for key in ("countries", "model", "seat_models", "turn_cap", "call_cap"):
        assert settings[key] == design[key]
    assert settings["case"] == case_for("guinea", "feasible")
    ghana_paths = [GHANA / name for name in (
        "all-sol", "feasible-all-sol", "sol-with-astra-norway", "feasible-sol-with-astra-norway",
    )]
    result = score([*ghana_paths, NORWAY_FEASIBLE, NORWAY_IMPASSE, NORWAY_MIXED_IMPASSE, target], trace=True)
    assert len(result["meetings"]) == 8
    for meeting in result["meetings"]:
        assert meeting["feasible_packages"] == design["feasible_packages"][meeting["world"]]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "score"))
    args = parser.parse_args()
    design = plan()
    if args.command == "plan":
        print(pretty(design))
    else:
        assert design == read(HERE / "plan.json")
        print(pretty(compare(design)))
