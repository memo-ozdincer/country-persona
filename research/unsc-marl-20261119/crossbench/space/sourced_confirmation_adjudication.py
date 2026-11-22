"""Differentiate conflicting local evidence from missing authority to confirm."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import sourced_confirmation as test

HERE = Path(__file__).resolve().parent
RESULT = test.ROOT / "results.json"
ADJUDICATION = {
    "drc_review_timing/decline_conflict": (
        "An intention to act by 1 July establishes a deadline, with no evidence that a meeting was "
        "scheduled for that date. The summary does not independently exclude a separate schedule."),
    "drc_affected_state/decline_conflict": (
        "The summary identifies an affected-state statement and contains no DRC vote. It does not include "
        "the official attendance list or an explicit negative vote-participation statement."),
    "unami_authority/decline_conflict": (
        "A task to assess and recommend does not establish authority to amend a mandate. The excerpt "
        "does not explicitly enumerate excluded powers or rule out a separate authorization."),
}


def run():
    original = json.loads(RESULT.read_text())
    revised = []
    for recorded in original["records"]:
        row = recorded.copy()
        if row["id"] in ADJUDICATION:
            row["original_expected"] = row["expected"]
            row["original_reference_span"] = row["reference_span"]
            row["expected"] = ["decline_unverified", None]
            row["reference_span"] = None
            row["adjudication"] = ADJUDICATION[row["id"]]
            assert recorded["reference_span"]
        for method in test.TASKS:
            entry = row[method].copy()
            verdict = entry["stable"]
            expected = row["expected"]
            entry["joint_right"] = verdict == expected
            entry["status_right"] = bool(verdict) and verdict[0] == expected[0]
            entry["unsupported_confirmation"] = bool(verdict) and verdict[0] == "confirm" and verdict != expected
            row[method] = entry
        revised.append(row)
    assert ADJUDICATION.keys() <= {row["id"] for row in revised}
    comparison = {}
    for method in test.TASKS:
        aggregate = Counter()
        correctness = Counter()
        for row in revised:
            prediction = row[method]["stable"]
            expected = row["expected"]
            aggregate["total"] += 1
            aggregate["correct_status"] += bool(prediction) and prediction[0] == expected[0]
            aggregate["correct_decision_and_source"] += prediction == expected
            aggregate["unsupported_confirmations"] += bool(prediction) and prediction[0] == "confirm" and prediction != expected
            aggregate["confirmed_with_source_withheld"] += (row["id"].endswith("/decline_unverified")
                                                            and bool(prediction) and prediction[0] == "confirm")
            aggregate["withheld_valid_confirmations"] += expected[0] == "confirm" and prediction != expected
            aggregate["order_deferrals"] += prediction is None
            if prediction == expected:
                correctness[expected[0]] += 1
        lookup = {row["id"]: row for row in revised}
        clean_switches = []
        for row in revised:
            if row["expected"][0] != "confirm":
                continue
            base_id = row["id"].rsplit("/", 1)[0]
            withheld = lookup[base_id + "/decline_unverified"]
            assert withheld["proposed"] == row["proposed"]
            if row[method]["joint_right"] and withheld[method]["joint_right"]:
                clean_switches.append(base_id)
        comparison[method] = dict(aggregate) | {"joint_correct_by_reference": dict(correctness),
                                                 "correct_source_availability_pairs": clean_switches}
    return {"scope": "Three authoring labels reviewed against the visible excerpts alone before model results "
                     "were inspected. An omitted authority is unverified unless the passages explicitly conflict. "
                     "The raw model verdicts and initial labels remain archived.",
            "relabels": ADJUDICATION, "comparison": comparison,
            "source_case_sha256": {"drc": sha256(test.DRC.read_bytes()).hexdigest(),
                                   "unami": sha256(test.UNAMI.read_bytes()).hexdigest()},
            "records": revised}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
