"""Score both questions and replay their effect on identical sender calibration."""
import json

from collect_split import GROUND, HERE, SYSTEMS, grounded, plan, prior, read
from score_judgments import METHODS, replay, summarize


def run():
    assert plan() == read(HERE / "plan.json")
    outputs = read(HERE / "verified.json")["outputs"]
    fixtures = grounded.fixtures()
    assert len(outputs) == 4 * len(fixtures)
    stages = {mode: {} for mode in SYSTEMS}
    combined = {}
    for key, fixture in fixtures.items():
        if fixture["mutation"]:
            group = "mutation"
        elif key.startswith("control/"):
            group = "control"
        else:
            group = "archived"
        base = {"weight": fixture["weight"], "met": fixture["met"], "group": group}
        for mode in SYSTEMS:
            margins = {}
            for side, mapping in prior.MAPPINGS.items():
                logits = outputs[f"{key}/{mode}/{side}"]["logits"]
                positive = next(letter for letter, name in mapping.items() if name == "process")
                negative = next(letter for letter, name in mapping.items() if name == "fund")
                margins[side] = logits[positive] - logits[negative]
            choices = {side: margin > 0 for side, margin in margins.items()}
            mean = sum(margins.values()) / len(margins)
            stages[mode][key] = base | {"margins": margins | {"mean": mean},
                                        "judgments": choices | {"mean": mean > 0,
                                                               "agreement": all(choices.values())}}
        combined[key] = base | {"judgments": {
            method: all(stages[mode][key]["judgments"][method] for mode in SYSTEMS)
            for method in METHODS}}
    views = {"coverage": stages["coverage"], "conjunction": combined}
    groups = ("archived", "mutation", "control")
    return {
        "stages": stages, "combined": combined,
        "relationship_metrics": {stage: {group: summarize([r for r in rows.values() if r["group"] == group])
                                          for group in groups} for stage, rows in views.items()},
        "guard_clears": {group: {method: sum(r["judgments"][method]
            for r in stages["guard"].values() if r["group"] == group) for method in METHODS} for group in groups},
        "sender_replay": {stage: replay(rows) for stage, rows in views.items()},
        "answer_witness_baseline": read(GROUND / "results.json")["downstream"]["mean"]["overall"],
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
