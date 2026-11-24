"""Compare France-opening Iraq assignments across the two mandate variants."""

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
FEASIBLE = REPORTS / "council-workshop-exclusion-policy-20261123" / "iraq-feasible-standard"
IMPASSE = REPORTS / "council-workshop-iraq-pilot-20261123" / "all-sol"
IMPASSE_MIXED = REPORTS / "council-workshop-iraq-focus-resume-20261124" / "mixed"
MIXED = HERE / "mixed"


def read(path):
    return json.loads(path.read_text())


def plan():
    settings = read(FEASIBLE / "settings.json")
    family, world, _, order = identify(settings)
    assert (family, world, order[0]) == ("iraq", "feasible", "FRA")
    feasible = Mandates.from_case(case_for("iraq", "feasible"), order)
    impasse = Mandates.from_case(case_for("iraq", "impasse"), order)
    assert feasible.options == impasse.options
    changes = {seat: sorted(feasible.allowed[seat] - impasse.allowed[seat])
               for seat in order if feasible.allowed[seat] != impasse.allowed[seat]}
    assert changes == {"ARE": ["hybrid"]} and impasse.allowed["ARE"] <= feasible.allowed["ARE"]
    feasible_packages = sorted(set(feasible.options).intersection(*feasible.allowed.values()))
    impasse_packages = sorted(set(impasse.options).intersection(*impasse.allowed.values()))
    assert feasible_packages == ["hybrid"] and not impasse_packages
    return {"countries": order, "model": SOL, "seat_models": {"ARE": ASTRA},
            "turn_cap": settings["turn_cap"], "call_cap": settings["call_cap"], "case_delta": changes,
            "feasible_packages": {"feasible": feasible_packages, "impasse": impasse_packages}}


def compare(design):
    settings = read(MIXED / "settings.json")
    for key in ("countries", "model", "seat_models", "turn_cap", "call_cap"):
        assert settings[key] == design[key]
    assert settings["case"] == case_for("iraq", "feasible")
    rows = score([FEASIBLE, IMPASSE, IMPASSE_MIXED, MIXED], trace=True)
    for meeting in rows["meetings"]:
        assert meeting["feasible_packages"] == design["feasible_packages"][meeting["world"]]
    return rows


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
