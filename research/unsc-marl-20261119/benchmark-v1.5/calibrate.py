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


def process_anchors():
    cases = e.cases()
    fixtures = {}
    for row in e.read(e.HERE / "process-anchors.json"):
        case = cases[row["case"]]
        calls = []
        for text in [*row["notes"], row["final"]]:
            request = e.build_request(case, row["arm"], 0, calls)
            calls.append({key: request[key] for key in ("speaker", "stage", "visible", "source_ids")}
                         | {"text": text, "input_tokens": 1, "output_tokens": 1, "termination": "complete"})
        packet = e.process_packet(case, calls)
        fixtures[packet["id"]] = (packet, row["expect"], case, calls)
    return dict(sorted(fixtures.items()))


def score(marks, mode="final"):
    fixtures = anchors() if mode == "final" else process_anchors()
    e.require(set(marks) == set(fixtures), "Incomplete anchor coverage")
    mismatches = []
    total = 0
    for key, (packet, expected, *context) in fixtures.items():
        verdict = marks[key]
        if mode == "final":
            e.judge.score(packet, verdict)
            actual = {unit["id"]: unit["status"] for unit in verdict["units"]}
            actual["guard"] = verdict["guard"]["status"]
        else:
            e.process_score(*context, verdict)
            actual = {rating["id"]: rating["points"] for rating in verdict["ratings"]}
        for field, status in expected.items():
            total += 1
            if actual[field] != status:
                mismatches.append({"id": key, "field": field, "expected": status,
                                   "observed": actual[field]})
    return {"packets": len(fixtures), "target_labels": total,
            "correct_labels": total - len(mismatches), "mismatches": mismatches}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("final", "process"), default="final")
    parser.add_argument("--verdicts", type=Path)
    args = parser.parse_args()
    if args.verdicts:
        e.emit(score(e.read(args.verdicts), args.mode))
    elif args.mode == "process":
        e.emit({key: fixture[0] for key, fixture in process_anchors().items()})
    else:
        e.emit({key: e.judge.request(packet) for key, (packet, _) in anchors().items()})
