"""Replay the conditional instruction against archived matched comparisons."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from held_suite import exclusion_trace, metrics
from replay import replay
from run import pretty


def compare(standard, priority, conditional):
    conditions = {
        "standard": (standard, False, False),
        "exclusions_first": (priority, True, False),
        "after_rejection": (conditional, False, True),
    }
    rows = {}
    reference = None
    for name, (directory, unconditional, after_rejection) in conditions.items():
        settings = json.loads((directory / "settings.json").read_text())
        assert settings.get("prioritize_exclusions", False) is unconditional
        assert settings.get("prioritize_exclusions_after_rejection", False) is after_rejection
        compared = {k: v for k, v in settings.items() if k not in {
            "started", "prioritize_exclusions", "prioritize_exclusions_after_rejection",
        }}
        if reference is None:
            reference = compared
        assert compared == reference
        case = settings["case"]
        result = replay(directory)
        rows[name] = {**metrics(result, case), **exclusion_trace(result, case, settings["countries"]),
                      "speech_actions": [[s["country"], s["action"], s["resulting_version"]]
                                         for s in result["history"]]}
    return rows


if __name__ == "__main__":
    opening = HERE.parent / "council-workshop-opening-agreement-20261123"
    gulf = HERE.parent / "council-workshop-held-pilot-20261123"
    transfer = HERE.parent / "council-workshop-exclusion-transfer-20261123"
    print(pretty({"feasible_opening": compare(opening / "standard", opening / "priority", HERE / "feasible-opening"),
                  "impasse": compare(gulf / "all-sol", transfer / "guinea-impasse-priority", HERE / "gulf-impasse")}))
