"""Export authored judge anchors and check quote-valid readings against target labels."""
import argparse
from pathlib import Path

import evaluate as e


def anchors():
    rows = e.judge.by_id(e.read(e.HERE / "anchors.json"))
    cases = e.cases()
    result = {}
    for name, row in rows.items():
        case = cases[row["case"]]
        packet = e.final_packet(case, [{}, {}, {"text": row["answer"]}])
        packet["id"] = e.checksum(["judge-anchor", name])[:16]
        result[packet["id"]] = (packet, row["expect"])
    return dict(sorted(result.items()))


def score(marks):
    fixtures = anchors()
    e.require(set(marks) == set(fixtures), "Incomplete anchor coverage")
    mismatches = []
    total = 0
    for key, (packet, expected) in fixtures.items():
        verdict = marks[key]
        e.judge.score(packet, verdict)
        actual = {unit["id"]: unit["status"] for unit in verdict["units"]}
        actual["guard"] = verdict["guard"]["status"]
        for field, status in expected.items():
            total += 1
            if actual[field] != status:
                mismatches.append({"id": key, "field": field, "expected": status,
                                   "observed": actual[field]})
    return {"packets": len(fixtures), "target_labels": total,
            "correct_labels": total - len(mismatches), "mismatches": mismatches}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verdicts", type=Path)
    args = parser.parse_args()
    if args.verdicts:
        e.emit(score(e.read(args.verdicts)))
    else:
        e.emit({key: e.judge.request(packet) for key, (packet, _) in anchors().items()})
