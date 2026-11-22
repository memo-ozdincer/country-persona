"""Change the forecast inside the same robust optimizer and verify dispatch."""
import argparse
import json
from pathlib import Path
from statistics import mean
import sys
from unittest.mock import patch

import numpy as np

from forecast_mechanism import HERE, PARENT, READ, RUNS, REFERENCE, options, runtime, s

TARGET = RUNS / "tolerance-2686-transfer"
sys.path.insert(0, str(TARGET))
import route_tolerance as router

WRITERS = ("scoped", "verbatim")
VARIANTS = ("nominal", "learned_pair", "half_additive_pair")


def plan():
    paths = {"program": Path(__file__), "protocol": HERE / "robust-protocol.md",
             "router": Path(router.__file__), "exact_result": HERE / "results.json",
             "fit": REFERENCE, "writer_scores": TARGET / "scoped-writer/scores.json",
             "forecast_rules": HERE / "forecast_mechanism.py"}
    for name in WRITERS:
        for role in ("route", "bank"):
            paths[f"{name}_{role}"] = TARGET / "scoped-writer" / f"{name}-{role}.json"
    return {"sha256": {name: s.digest(file) for name, file in paths.items()},
            "writers": list(WRITERS), "variants": list(VARIANTS)}


def run(name):
    assert plan() == READ(HERE / "robust-plan.json")
    directory = TARGET / "scoped-writer"
    bank_file = directory / f"{name}-bank.json"
    saved = READ(directory / f"{name}-route.json")
    base_forecast = s.interval.forecasts
    reward_fit = READ(REFERENCE)
    weights, strength = np.array(reward_fit["weights"]), reward_fit["selected_strength"]
    init = READ(s.INITIAL)["training"]["budget_fit"]
    reference = router.run(bank_file)
    assert json.loads(json.dumps(reference)) == saved
    points = np.asarray(saved["score_bank"], dtype=float)
    singleton = s.interval.s.t.cal.estimated(points)
    rules = {"nominal": reference}
    for label in VARIANTS[1:]:
        def changed(calibration, grade):
            values = base_forecast(calibration, grade)
            return dict(options(values, weights, strength))[label]
        with patch.object(s.interval, "forecasts", changed):
            rules[label] = router.run(bank_file)

    rows = []
    for entries in zip(*(document["rows"] for document in rules.values()), strict=True):
        baseline = entries[0]
        keys = ("law", "prior_information", "review_offset")
        condition = {key: baseline[key] for key in keys}
        law, proxy = s.a.laws()[condition["law"]]
        announced = law if condition["prior_information"] == "exact" else proxy
        opening = s.o.replan.study.opening(singleton, announced, init)
        cases = {}
        for label, scenario in zip(rules, entries, strict=True):
            assert {key: scenario[key] for key in keys} == condition
            arms = {}
            for key in (router.ref.TEAM, router.ref.FIXED):
                saved_policy = scenario["choices"][key]
                table = tuple(np.asarray(item) for item in saved_policy["deployed_actions"])
                if saved_policy["stochastic"]:
                    checked = router.ref.replay(law, opening, table, points)
                else:
                    replay, _ = runtime.trace_table(law, opening, {"interval_team": table, "interval_fixed": table}, points)
                    checked = replay["interval_team"]
                measured = scenario["outcomes"][key]
                assert all(abs(checked[field] - measured[field]) <= 1e-9
                           for field in ("net", "released", "cost", "queries"))
                arms[key] = {"result": measured, "policy": saved_policy,
                             "receipt_mass": [float(x) for x in checked["receipt_mass"]]}
            cases[label] = arms
        rows.append(condition | {"silence": baseline["true_silence"], "arms": cases})
    assert len(rows) == 18
    summary = {}
    for label in VARIANTS:
        values = [r["arms"][label][router.ref.TEAM]["result"] for r in rows]
        comparisons = {"nominal_team": ("nominal", router.ref.TEAM),
                       "nominal_fixed": ("nominal", router.ref.FIXED),
                       "same_forecast_fixed": (label, router.ref.FIXED)}
        summary[label] = {
            "mean_released": mean(v["released"] for v in values),
            "mean_cost": mean(v["cost"] for v in values),
            "below_silence": sum(v["released"] < r["silence"] - 1e-9 for v, r in zip(values, rows, strict=True)),
            **{name: s.compare([v["net"] - r["arms"][kind][policy]["result"]["net"]
                                for v, r in zip(values, rows, strict=True)])
               for name, (kind, policy) in comparisons.items()},
        }
    return {"writer": name, "summary": summary, "rows": rows, "independent_replays": len(rows) * len(VARIANTS) * 2,
            "plan_sha256": s.digest(HERE / "robust-plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", *WRITERS))
    mode = parser.parse_args().mode
    print(json.dumps(plan() if mode == "plan" else run(mode), indent=2))
