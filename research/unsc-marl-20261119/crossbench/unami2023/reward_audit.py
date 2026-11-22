"""Measure how two judges would reward omissions and contradictions."""
from collections import Counter
import json

import judge as original

HERE = original.HERE


def original_rows():
    payload = json.loads((HERE / "judge-evidence" / "results.json").read_text())
    return {group: {(r["record"], r["unit"]): (r["reference"], r["consensus"])
                    for r in block["details"]} for group, block in payload["judge"].items()}


def witness_rows():
    payload = json.loads((HERE / "witness-evidence" / "results.json").read_text())
    return {group: {(r["candidate"], r["field"]): (r["reference"], r["verdict"])
                    for r in block["records"]} for group, block in payload["groups"].items()}


def matrix(rows):
    counts = Counter(rows)
    classes = ("supported", "omitted", "contradicted")
    return {reference: {str(guess): counts[reference, guess] for guess in (*classes, None)} for reference in classes}


def run():
    baseline = original_rows()
    witness = witness_rows()
    shared = {}
    for group, baseline_rows in baseline.items():
        assert baseline_rows.keys() <= witness[group].keys()
        assert all(row[0] == witness[group][key][0] for key, row in baseline_rows.items())
        shared[group] = {"original": matrix(baseline_rows.values()),
                         "witness": matrix(witness[group][k] for k in baseline_rows)}

    records = {}
    for name in sorted({record for record, _ in baseline["generated"]}):
        old = [(ref, verdict) for (record, _), (ref, verdict) in baseline["generated"].items() if record == name]
        new = [(ref, verdict) for (record, _), (ref, verdict) in witness["generated"].items() if record == name]
        records[name] = {
            "review_points": 7 * sum(ref == "supported" for ref, _ in old),
            "original_points": 7 * sum(verdict == "supported" for _, verdict in old),
            "witness_provisional_points": 7 * sum(verdict == "supported" for _, verdict in new),
            "witness_points_in_review": 7 * sum(verdict is None for _, verdict in new),
            "witness_false_positive_points": 7 * sum(verdict == "supported" and ref != "supported" for ref, verdict in new),
            "witness_missed_supported_points": 7 * sum(verdict != "supported" and ref == "supported" for ref, verdict in new),
        }

    # Compare the best supported reference unit to a controlled single-edit
    # foil on the exact same target. Report ties and abstentions separately.
    controls = {}
    for name, rows in (("original", baseline["authored"]), ("witness", witness["authored"])):
        comparisons = []
        for (candidate, field), (truth, verdict) in rows.items():
            if candidate == "reference" or truth == "supported":
                continue
            _, restored = rows["reference", field]
            assert rows["reference", field][0] == "supported"
            if verdict is None or restored is None:
                change = "deferred"
            else:
                change = ("rewards_repair" if restored == "supported" and verdict != "supported" else
                          "rewards_error" if verdict == "supported" and restored != "supported" else "ties")
            comparisons.append({"candidate": candidate, "field": field, "effect": change})
        controls[name] = comparisons
    return {"shared_panels": shared, "candidate_rewards": records, "single_edit_reward_directions": controls,
            "scope": "The points reproduce what each judge would award for criterion coverage. "
                     "Points in review are withheld. This score excludes release guards, which the separate exact-span review "
                     "fails for every actual record."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
