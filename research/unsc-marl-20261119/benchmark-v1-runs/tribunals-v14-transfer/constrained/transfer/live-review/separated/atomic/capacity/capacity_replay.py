"""Compare compound and factored coverage and replay admitted grades."""
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

from capacity_atoms import HERE, PARENT, ATOMS, READ, base, old, records

sys.path.insert(0, str(PARENT.parent))
from separation_replay import EPS, reroute
from grade_and_route import PARENT as TRANSFER

RULES = ("compound_mean", "factored_mean", "compound_agreement", "factored_agreement")


def conjunction(values):
    return "unmet" if "unmet" in values else "uncertain" if "uncertain" in values else "met"


def predictions():
    outputs = READ(HERE / "verified.json")["model_outputs"]
    decided, rows = {}, {}
    for case, setup in records().items():
        rows[case] = {}
        for group, atoms in setup["target_components"].items():
            local = {}
            for item in ("compound", *ATOMS[group]):
                key = f"{case}/{group}/{item}"
                mean_logits = {meaning: mean(outputs[key + "/" + spec]["logits"][letter]
                                             for spec, labels in base.LABELS.items()
                                             for letter, semantic in labels.items() if semantic == meaning)
                               for meaning in base.DEFINITIONS}
                choices = {spec: labels[outputs[key + "/" + spec]["choice"]] for spec, labels in base.LABELS.items()}
                local[item] = {"mean": max(mean_logits, key=mean_logits.get),
                               "agreement": choices["ab"] if choices["ab"] == choices["ba"] else "uncertain",
                               "choices": choices, "mean_logits": mean_logits}
                decided[key] = local[item]
            rows[case][group] = {"expected": conjunction(atoms.values()), "expected_atoms": atoms} | {
                f"{method}_{decision}": local["compound"][decision] if method == "compound"
                else conjunction([local[item][decision] for item in ATOMS[group]])
                for method in ("compound", "factored") for decision in ("mean", "agreement")}
    return rows, decided


def scores(preds):
    atomic = READ(PARENT / "results.json")
    rubric = {r["id"]: r["weight"] for r in old.cases()["myanmar"]["criteria"]}
    scores = {}
    match = {"archived-pair": "myanmar/pair", "archived-full": "myanmar/control"}
    for rule in RULES:
        result = {}
        for key, name in match.items():
            previous = atomic["grades"]["scoped_mean"][name]
            criteria = dict(previous["units"])
            criteria.update({group: pred[rule] for group, pred in preds[key].items()})
            assert previous["guard"] == "clear"
            grade = sum(rubric[name] for name, state in criteria.items() if state == "met")
            result[name] = {"score": grade, "accepted": "uncertain" not in criteria.values(),
                            "units": criteria, "guard": previous["guard"],
                            "expected_score": previous["expected_score"]}
        scores[rule] = result
    return scores


def replay():
    preds, details = predictions()
    ratings = scores(preds)
    selective = READ(PARENT / "selective-results.json")
    prior_atomic = READ(PARENT / "results.json")
    banks = READ(TRANSFER / "plan.json")["banks"]
    archived = READ(TRANSFER / "results.json")["rows"]
    context = {(r["case"], r["law"], r["prior_information"], r["review_offset"]): r for r in archived}
    outcomes, cached = [], {}
    for row in selective["rows"]:
        case, mixture, info, offset = (row[key] for key in ("case", "law", "prior_information", "offset"))
        active = {}
        for rule in RULES:
            metrics = row["selected"]
            score = row["admitted_grade"]
            if case == "myanmar" and ratings[rule][case + "/pair"]["accepted"]:
                score = ratings[rule][case + "/pair"]["score"]
                key = case, mixture, info, score
                if key not in cached:
                    reuse = next((context[case, mixture, info, delta]["updated"]["interval_team"]
                                  for delta in (-7, 0, 7) if score == np.clip(banks[case][3] + delta, 0, 70)), None)
                    cached[key] = reuse if reuse is not None else reroute(
                        context[case, mixture, info, offset], np.asarray(banks[case], dtype=float), score)
                metrics = cached[key]
            active[rule] = {"grade": score, "metrics": metrics}
        outcomes.append({**row, "capacity": active})
    results = {}
    for rule in RULES:
        tests = {name: [v[name] for v in preds.values() if name in v] for name in ("role", "uk")}
        delta = [row["capacity"][rule]["metrics"]["net"] - row["original"]["net"] for row in outcomes]
        delta_vs_selective = [row["capacity"][rule]["metrics"]["net"] - row["selected"]["net"] for row in outcomes]
        results[rule] = {
            **{f"{name}_exact": sum(x[rule] == x["expected"] for x in vals) for name, vals in tests.items()},
            **{f"{name}_total": len(vals) for name, vals in tests.items()},
            "admitted_exact_archives": sum(r["accepted"] and r["score"] == r["expected_score"]
                                           for r in ratings[rule].values()),
            "below_informed_silence": sum(row["capacity"][rule]["metrics"]["over_informed_silence_quality"] < -EPS
                                         for row in outcomes),
            "net_mean_over_original": mean(delta), "net_mean_over_selective": mean(delta_vs_selective),
            "wins_over_original": sum(x > EPS for x in delta), "losses_over_original": sum(x < -EPS for x in delta),
        }
    atoms = {}
    for group in ATOMS:
        for mode in ("mean", "agreement"):
            paired = [(details[f"{case}/{group}/{atom}"][mode], expected)
                      for case, predicates in preds.items() if group in predicates
                      for atom, expected in predicates[group]["expected_atoms"].items()]
            atoms[f"{group}/{mode}"] = {"exact": sum(got == expected for got, expected in paired), "total": len(paired)}
    old_outputs = READ(PARENT / "verified.json")["model_outputs"]
    latest_outputs = READ(HERE / "verified.json")["model_outputs"]
    repeated = []
    for key, previous in (("archived-pair", "myanmar/pair"), ("archived-full", "myanmar/control")):
        for group in ATOMS:
            for map_id in base.LABELS:
                before = old_outputs[f"{previous}/{group}/whole/{map_id}"]["logits"]
                after = latest_outputs[f"{key}/{group}/compound/{map_id}"]["logits"]
                repeated.append({"record": key, "criterion": group, "mapping": map_id, "logits_identical": before == after,
                                 "maximum_absolute_logit_delta": max(abs(value - after[letter]) for letter, value in before.items())})
    pins = (Path(__file__).resolve(), HERE / "plan.json", HERE / "verified.json", PARENT / "results.json",
            PARENT / "verified.json", PARENT / "selective-results.json", TRANSFER / "plan.json", TRANSFER / "results.json")
    assert len(outcomes) == 23
    return {"summary": results, "atoms": atoms, "selective_baseline": selective["summary"], "atomic_baselines": prior_atomic["summary"],
            "predicates": preds, "detail": details, "records": ratings, "repeated_compound_logits": repeated,
            "rows": outcomes, "sha256": {str(path.relative_to(TRANSFER)): old.digest(path) for path in pins}}


if __name__ == "__main__":
    print(json.dumps(replay(), ensure_ascii=False, indent=2))
