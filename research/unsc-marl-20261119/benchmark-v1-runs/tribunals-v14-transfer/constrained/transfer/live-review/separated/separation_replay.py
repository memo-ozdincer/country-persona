"""Reroute the archived trigger conditions using admitted split-stage grades."""
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

from pair_separation import HERE, READ, grades, old

sys.path.insert(0, str(HERE.parent))
from grade_and_route import EPS, PARENT, reroute


def criterion_audit(verdicts):
    modular = READ(old.MODULAR)["results"]
    marks_path = old.MODULAR.with_name("marks.json")
    marks = READ(marks_path)
    myanmar = READ(old.MYANMAR)["records"]["rank_normalized"]
    expected = {
        f"myanmar/{row}": {k for k, v in myanmar[mask]["score"]["units"].items() if v == "met"}
        for row, mask in (("pair", "3"), ("control", "7"))
    }
    for case in ("emergency", "unama"):
        used = modular[case]["records"]["normalized/3"]["used"]
        expected[f"{case}/pair"] = {
            f"{sid}-{i}" for sid in used for i, item in enumerate(marks[f"{case}/{sid}"]["units"], 1)
            if item[0] == "met"
        }
    expected["unama/control"] = set()
    result = {}
    for key, gold in expected.items():
        observed = verdicts[key].get("met")
        result[key] = {"expected_met": sorted(gold), "observed_met": observed}
        if observed is not None:
            result[key].update(missed=sorted(gold - set(observed)), extra=sorted(set(observed) - gold))
    return result, {path.name: old.digest(path) for path in (marks_path, old.MODULAR, old.MYANMAR)}


def replay():
    checks = grades()
    archived = READ(HERE.parent / "results.json")
    histories = READ(PARENT / "results.json")
    banks = READ(PARENT / "plan.json")["banks"]
    key_fields = ("case", "law", "prior_information", "review_offset")
    context = {tuple(r[k] for k in key_fields): r for r in histories["rows"]}
    cached = {}
    rows = []
    for row in archived["rows"]:
        case, law, info, offset = (row[k] for k in ("case", "law", "prior_information", "offset"))
        result = checks["verdicts"][case + "/pair"]
        before = row["original"]
        after, grade = before, None
        if result["accepted"]:
            grade = result["grade"]
            target = (case, law, info, grade)
            if target not in cached:
                match = next((context[case, law, info, d]["updated"]["interval_team"]
                              for d in (-7, 0, 7) if grade == np.clip(banks[case][3] + d, 0, 70)), None)
                original = context[case, law, info, offset]
                cached[target] = (match if match is not None else reroute(original, np.array(banks[case], float), grade))
            after = cached[target]
        rows.append({**row, "separated": after, "separated_grade": grade})
    assert len(rows) == 23
    net = [r["separated"]["net"] - r["original"]["net"] for r in rows]
    summary = archived["summary"] | {"separated": {
        "net_mean_over_original": mean(net), "wins": sum(v > EPS for v in net),
        "ties": sum(abs(v) <= EPS for v in net), "losses": sum(v < -EPS for v in net),
        "below_informed_silence": sum(r["separated"]["over_informed_silence_quality"] < -EPS for r in rows),
    }}
    pins = (Path(__file__).resolve(), HERE / "plan.json", HERE / "verified.json", HERE.parent / "results.json",
            PARENT / "results.json", PARENT / "plan.json", Path(sys.modules["grade_and_route"].__file__).resolve())
    criteria, criteria_pins = criterion_audit(checks["verdicts"])
    return {"grades": checks["verdicts"], "criteria": criteria, "criteria_sha256": criteria_pins,
            "summary": summary, "rows": rows,
            "sha256": {str(path.relative_to(PARENT)): old.digest(path) for path in pins}}


if __name__ == "__main__":
    print(json.dumps(replay(), ensure_ascii=False, indent=2))
