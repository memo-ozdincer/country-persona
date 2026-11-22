"""Export masked finals and score matched checklist and archived writer outputs."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent
sys.path.insert(0, str(ARCHIVE.parents[1] / "benchmark"))
import evaluate as e
from run_suite import verify_release


def load(path):
    return {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}


def pairs():
    verify_release()
    cases = e.cases()
    base = load(ARCHIVE / "format-evidence/records.jsonl")
    new = load(HERE / "evidence/records.jsonl")
    assert set(base) == set(new)
    for key, old in base.items():
        case = cases[key.split("/")[0]]
        yield key, case, {"baseline": [{}, {}, old["response"]],
                          "checklist": [{}, {}, new[key]["response"]]}


def deck(rows):
    packets = {}
    for _, case, arms in rows:
        for calls in arms.values():
            packet = e.final_packet(case, calls)
            packets[packet["id"]] = packet
    return [packets[k] for k in sorted(packets)]


def score(rows):
    original = e.read(ARCHIVE / "format-marks.json")
    current = e.read(HERE / "marks.json")
    result = {}
    used_current = set()
    changes = Counter()
    for key, case, arms in rows:
        scored = {}
        for arm, calls in arms.items():
            packet = e.final_packet(case, calls)
            marks = original if arm == "baseline" else current
            if arm == "checklist":
                used_current.add(packet["id"])
            scored[arm] = e.final_score(case, calls, marks[packet["id"]])
            scored[arm]["receipt_id"] = packet["id"]
            scored[arm]["word_count"] = len(calls[-1]["text"].split())
            scored[arm]["input_tokens"] = calls[-1]["input_tokens"]
            scored[arm]["output_tokens"] = calls[-1]["output_tokens"]
        before, after = (scored[a]["units"] for a in ("baseline", "checklist"))
        for unit in before:
            changes[unit, before[unit], after[unit]] += 1
        result[key] = scored
    assert set(current) == used_current
    summary = {}
    for arm in ("baseline", "checklist"):
        grades = [pair[arm] for pair in result.values()]
        summary[arm] = {
            "exact": sum(r["mechanical"]["accepted"] for r in grades),
            "released": sum(r["release"] for r in grades),
            "strict": sum(r["strict"] for r in grades),
            "released_70_total": sum(r["released_70"] for r in grades),
            "raw_70_total": [sum(r["raw_70"][i] for r in grades) for i in range(2)],
            "input_tokens": sum(r["input_tokens"] for r in grades),
            "output_tokens": sum(r["output_tokens"] for r in grades),
        }
    return {"summary": summary, "criterion_transitions": [
        {"criterion": criterion, "baseline": before, "checklist": after, "count": count}
        for (criterion, before, after), count in sorted(changes.items())
    ], "episodes": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("deck", "score"))
    args = parser.parse_args()
    e.emit(deck(pairs()) if args.mode == "deck" else score(pairs()))
