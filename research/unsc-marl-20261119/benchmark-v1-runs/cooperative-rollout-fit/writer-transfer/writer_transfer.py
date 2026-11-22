"""Validate fitted head strength on synthetic returns and transfer frozen teams."""
import argparse
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RUNS = PARENT.parent
TARGET = RUNS / "tolerance-2686-transfer/scoped-writer"
sys.path.insert(0, str(PARENT))
import reward_fit as reward
import rollout_fit as s
from routing_transfer import runtime

READ = s.wire.n.read
SCALES = tuple(product((0., .5, 1.), repeat=2))


def plan():
    pins = (Path(__file__), HERE / "protocol.md", PARENT / "plan.json", PARENT / "results.json",
            PARENT / "reward-results.json", s.INITIAL, TARGET / "scores.json",
            TARGET / "scoped-route.json", TARGET / "verbatim-route.json",
            s.TRANSFER / "results.json", Path(s.__file__), Path(runtime.__file__))
    return {"training_banks": 36, "validation_banks": 12, "scales": SCALES,
            "sha256": {str(p.resolve().relative_to(RUNS)): s.digest(p) for p in pins if p.resolve().is_relative_to(RUNS)}}


def arrays(values):
    return [tuple(np.array(part, dtype=float) for part in stage) for stage in values]


def scaled(weights, scale):
    return [(scale[0] * r, scale[1] * q) for r, q in weights]


def validate(locked, banks, init, weights):
    trials = list(reward.contexts(banks, locked, init))
    summary = []
    silence = [float(s.o.controls(points, s.o.opening(*opening, law), law, opening)
               ["exact_no_request"]["released"]) for points, law, opening, _, _ in trials]
    for scale in SCALES:
        outcomes = [s.metric(points, law, opening, s.deploy(forecast, mass, scaled(weights, scale)))
                    for points, law, opening, mass, forecast in trials]
        summary.append({"scale": list(scale), "mean_net": mean(out["net"] for out in outcomes),
                        "mean_released": mean(out["released"] for out in outcomes),
                        "below_silence": sum(out["released"] < threshold - 1e-9
                                             for out, threshold in zip(outcomes, silence, strict=True))})
    base = summary[0]
    for row in summary:
        row["eligible"] = row["mean_released"] >= base["mean_released"] - 1e-9 and row["below_silence"] <= base["below_silence"]
    chosen = max((row for row in summary if row["eligible"]),
                 key=lambda row: (row["mean_net"], -sum(row["scale"]), -row["scale"][0]))
    return chosen["scale"], summary, len(trials)


def condition_key(row):
    return row["law"], row["prior_information"], row["review_offset"]


def cases(locked):
    archive = READ(s.TRANSFER / "results.json")["rows"]
    score_banks = READ(TARGET / "scores.json")["banks"]
    for case, points in locked["test_banks"].items():
        yield case, points, [row for row in archive if row["case"] == case]
    for name, points in score_banks.items():
        route = READ(TARGET / f"{name}-route.json")
        assert points == route["score_bank"]
        yield name, points, route["rows"]


def replay(points, law, opening, policy):
    measured = s.metric(points, law, opening, policy)
    computed, _ = runtime.trace_table(law, opening, {"interval_team": policy, "interval_fixed": policy}, points)
    checked = computed["interval_team"]
    assert all(abs(value - checked[k]) <= 1e-9 for k, value in measured.items())
    measured["receipt_mass"] = [float(value) for value in checked["receipt_mass"]]
    return measured


def run():
    lock = json.loads(json.dumps(plan()))
    assert lock == READ(HERE / "plan.json")
    locked = READ(PARENT / "plan.json")
    init = READ(s.INITIAL)["training"]["budget_fit"]
    prior_fit = arrays(READ(PARENT / "results.json")["weights"])
    reward_fit = READ(PARENT / "reward-results.json")
    reward_weights = np.array(reward_fit["weights"])
    training, validation = locked["training_banks"][:36], locked["training_banks"][36:]
    evaluation = list(cases(locked))
    anchor = {s.centered(bank) for bank in training}
    assert len(anchor) == 36 and len(validation) == 12
    assert not anchor & {s.centered(bank) for bank in validation}
    assert not {s.centered(bank) for bank in training + validation} & {s.centered(points) for _, points, _ in evaluation}
    refit, trace, contexts = s.train(locked | {"training_banks": training}, init)
    selection, metrics, count = validate(locked, validation, init, refit)
    history = {
        "neutral": reward.NO_FIT,
        "transferred": prior_fit,
        "responder_only": scaled(prior_fit, (1., 0.)),
        "chair_only": scaled(prior_fit, (0., 1.)),
        "refit_full": refit,
        "refit_selected": scaled(refit, selection),
    }
    laws = s.a.laws()
    rows = []
    for case, grades, conditions in evaluation:
        points = np.array(grades, dtype=float)
        assert len(conditions) == len({condition_key(row) for row in conditions}) == 18
        for original in conditions:
            tag, information, offset = condition_key(original)
            law, proxy = laws[tag]
            shown = law if information == "exact" else proxy
            opening, mass, forecast = s.context(points, np.clip(points[3] + offset, 0, 70), shown, init)
            arms = {name: s.deploy(forecast, mass, stages) for name, stages in history.items()}
            arms["learned_forecast"] = s.deploy(reward.corrected(forecast, reward_weights, reward_fit["selected_strength"]),
                                                mass, reward.NO_FIT)
            arms["exact_forecast"] = s.o.exact_parts(mass, forecast)["exact_ask_reply"]
            results = {name: replay(points, law, opening, arm) for name, arm in arms.items()}
            if case in {"scoped", "verbatim"}:
                for arm in ("neutral", "learned_forecast"):
                    assert all(abs(results[arm][key] - original["outcomes"][arm][key]) < 1e-9
                               for key in ("released", "cost", "net", "queries"))
            if "opening" in original:
                assert [v.tolist() for v in opening] == original["opening"]
            controls = original["outcomes"] if "outcomes" in original else original["updated"]
            for key in ("interval_team", "interval_fixed"):
                out = controls[key]
                results[key] = {field: float(out[field]) for field in ("released", "cost", "net", "queries")}
            actual = s.o.controls(points, s.o.opening(*opening, law), law, opening)
            best_fixed = max((row for key, row in actual.items() if key != "exact_ask_reply"), key=lambda row: row["net"])
            results["informed_fixed"] = {field: float(best_fixed[field]) for field in ("released", "cost", "net", "queries")}
            assert all(out["net"] <= actual["exact_ask_reply"]["net"] + 1e-9 for out in results.values())
            rows.append({"case": case, "law": tag, "prior_information": information, "review_offset": offset,
                         "silence_quality": float(actual["exact_no_request"]["released"]), "outcomes": results,
                         "opening": [v.tolist() for v in opening],
                         "policies": {name: [v.tolist() for v in arm] for name, arm in arms.items()}})
    summary = {}
    for group in ("archive", "scoped", "verbatim"):
        group_rows = [r for r in rows if (r["case"] not in {"scoped", "verbatim"} if group == "archive" else r["case"] == group)]
        summary[group] = {}
        for arm in (*history, "learned_forecast", "exact_forecast", "interval_team"):
            scores = [row["outcomes"][arm] for row in group_rows]
            summary[group][arm] = {
                "mean_released": mean(out["released"] for out in scores),
                "mean_cost": mean(out["cost"] for out in scores),
                "below_silence": sum(out["released"] < row["silence_quality"] - 1e-9
                                     for out, row in zip(scores, group_rows, strict=True)),
                **{f"vs_{base}": s.compare([out["net"] - row["outcomes"][base]["net"]
                                           for out, row in zip(scores, group_rows, strict=True)])
                   for base in ("neutral", "interval_team", "interval_fixed", "informed_fixed")},
            }
    assert len(rows) == 126
    return {"validation": {"conditions": count, "selected": selection, "trials": metrics},
            "fit": {"contexts": contexts, "weights": [[v.tolist() for v in stage] for stage in refit], "trace": trace},
            "summary": summary, "rows": rows, "independent_policy_replays": sum(len(r["policies"]) for r in rows),
            "plan_sha256": s.digest(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
