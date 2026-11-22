"""Replay an alternative fixed target with identical saved native receipts."""
import json
from pathlib import Path

import review_witness_run as check

m = check.m

e = m.e
HERE = Path(__file__).resolve().parent


def run():
    context, inventory, plan = m.select()
    scores, label, law, team, fixed, openers, policies = context
    _, _, initial, params = m.model_inputs()
    coordinates = tuple(float(scores[i]) for i in (0, 1, 2, 4))
    _, alternatives, _, _ = m.selector.choose(coordinates, openers, law, params)
    assert fixed != "fixed_3" and plan["ideal"]["learned"]["ask"] == "russia"
    cached = {e.checksum(row["request"]): row["reply"] for row in check.read_lines("calls.jsonl")}
    matched, unavailable = [], []

    def replay(request):
        key = e.checksum(request)
        if key not in cached:
            unavailable.append(request)
            return {"text": "", "termination": "unavailable"}
        matched.append(key)
        return cached[key]

    options = (scores, label, law, team, "fixed_3", openers, policies | {"fixed": alternatives["fixed_3"]})
    records = {row["arm"]: row for row in m.simulate(options, inventory, replay)}
    fixed_row = records["fixed"]
    learned = records["learned"]
    report = {"fixed_alternative": fixed_row, "saved_requests_matched": len(matched), "unavailable": unavailable}
    if not unavailable and fixed_row["final_mask"] == learned["final_mask"]:
        learned_release = e.read(HERE / "results.json")["learned"]["released"]
        report["identical_compiled_record"] = True
        report["released_70"] = learned_release
        report["net_difference"] = learned["cost"] - fixed_row["cost"]
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
