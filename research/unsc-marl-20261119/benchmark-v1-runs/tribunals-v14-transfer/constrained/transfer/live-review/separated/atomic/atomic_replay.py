"""Score constrained coverage choices and replay their effect on routing."""
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

from coverage_logits import HERE, PARENT, LABELS, READ, old, prior

sys.path.insert(0, str(PARENT))
from separation_replay import criterion_audit, EPS, reroute
from grade_and_route import PARENT as TRANSFER

METHODS = ("whole", "scoped", "scoped_ab", "scoped_ba", "whole_mean", "scoped_mean")


def interpret():
    saved = READ(HERE / "verified.json")
    plan = READ(HERE / "plan.json")
    supports = READ(PARENT / "outcome-audit.json")["support"]
    records = prior.records()
    expected, _ = criterion_audit({record: {} for record in records})
    outputs, item_checks = saved["model_outputs"], {}
    for key, views in plan["routing"].items():
        choices = {}
        for view, prompt in views.items():
            votes = {kind: LABELS[kind][outputs[prompt + "/" + kind]["choice"]]
                     for kind in LABELS} if prompt else dict.fromkeys(LABELS, "unmet")
            aligned = {}
            if prompt:
                for meaning in LABELS["ab"].values():
                    aligned[meaning] = mean(outputs[prompt + "/" + kind]["logits"][letter]
                                            for kind, mapping in LABELS.items()
                                            for letter, value in mapping.items() if value == meaning)
            choices[view] = votes | {"consensus": votes["ab"] if votes["ab"] == votes["ba"] else "uncertain",
                                     "mean": max(aligned, key=aligned.get) if prompt else "unmet",
                                     "mean_logits": aligned,
                                     "no_model_call": prompt is None}
        item_checks[key] = choices
    assert len(item_checks) == 44 and len(outputs) == 106
    judged = {}
    for method in METHODS:
        view, mode = method.split("_") if "_" in method else (method, "consensus")
        method_rows = {}
        for key, record in records.items():
            support = supports[key]["model_labels"]
            guard = "failed" if "N" in support else "uncertain" if "U" in support else "clear"
            units = {row["id"]: item_checks[key + "/" + row["id"]][view][mode] for row in record["criteria"]}
            accepted = guard != "uncertain" and "uncertain" not in units.values()
            grade = (record["public_base"] + sum(row["weight"] for row in record["criteria"]
                     if units[row["id"]] == "met")) if guard == "clear" else 0
            observed = {item for item, state in units.items() if state == "met"}
            expected_met = expected[key]["expected_met"] if key in expected else None
            method_rows[key] = {"accepted": accepted, "score": grade, "guard": guard, "units": units,
                               "exact": accepted and grade == record["expected_score"] and guard == record["expected_guard"],
                               "expected_score": record["expected_score"]}
            if expected_met is not None:
                gold = set(expected_met)
                method_rows[key].update(expected_met=expected_met, missing=sorted(gold - observed),
                                        extra=sorted(observed - gold))
        judged[method] = method_rows
    return item_checks, judged


def replay():
    items, judgments = interpret()
    old_routing = READ(PARENT / "results.json")
    banks = READ(TRANSFER / "plan.json")["banks"]
    original = READ(TRANSFER / "results.json")
    contexts = {(r["case"], r["law"], r["prior_information"], r["review_offset"]): r for r in original["rows"]}
    cached, observed = {}, []
    for entry in old_routing["rows"]:
        case, law, info, offset = (entry[k] for k in ("case", "law", "prior_information", "offset"))
        variants = {}
        for method in METHODS:
            rating = judgments[method][case + "/pair"]
            result, score = entry["original"], None
            if rating["accepted"]:
                score = rating["score"]
                grade_key = case, law, info, score
                if grade_key not in cached:
                    same = next((contexts[case, law, info, d]["updated"]["interval_team"] for d in (-7, 0, 7)
                                 if score == np.clip(banks[case][3] + d, 0, 70)), None)
                    cached[grade_key] = (same if same is not None else reroute(
                        contexts[case, law, info, offset], np.array(banks[case], float), score))
                result = cached[grade_key]
            variants[method] = {"admitted_grade": score, "performance": result}
        observed.append({**entry, "atomic": variants})
    summary = {}
    for method in METHODS:
        grades = list(judgments[method].values())
        paired = [value for key, value in judgments[method].items() if key.endswith("/pair")]
        performance = [row["atomic"][method]["performance"] for row in observed]
        change = [value["net"] - row["original"]["net"] for value, row in zip(performance, observed, strict=True)]
        summary[method] = {"accepted_records": sum(r["accepted"] for r in grades),
                           "exact_records": sum(r["exact"] for r in grades),
                           "exact_pairs": sum(r["exact"] for r in paired),
                           "net_mean_over_original": mean(change),
                           "net_wins": sum(x > EPS for x in change),
                           "net_losses": sum(x < -EPS for x in change),
                           "below_informed_silence": sum(r["over_informed_silence_quality"] < -EPS for r in performance)}
    pins = (Path(__file__).resolve(), HERE / "readout.md", HERE / "plan.json", HERE / "verified.json", PARENT / "outcome-audit.json",
            PARENT / "results.json", TRANSFER / "plan.json", TRANSFER / "results.json")
    assert len(observed) == 23
    return {"summary": summary, "prior_summary": old_routing["summary"],
            "per_item": items, "grades": judgments, "rows": observed,
            "sha256": {str(path.relative_to(TRANSFER)): old.digest(path) for path in pins}}


if __name__ == "__main__":
    print(json.dumps(replay(), ensure_ascii=False, indent=2))
