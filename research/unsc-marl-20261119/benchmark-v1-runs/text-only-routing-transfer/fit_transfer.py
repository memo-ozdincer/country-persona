"""Fit donor receipt values and run target policies without its pair labels."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import re
import runpy
from types import SimpleNamespace

import numpy as np

from extract import HERE, PATHS, QUESTIONS, RUNS, extract_cards, guard, pairs, read

PREVIOUS = RUNS/"terminal-feedback-routing"
prior = SimpleNamespace(**runpy.run_path(str(PREVIOUS/"fit.py")))
DONORS = ("2721", "2744")
NATIVE = RUNS/"delisting-witness-render/compact-results.json"
TARGET = RUNS/"hunger-2417-transfer/witness-routing/repair-results.json"
STOPWORDS = set("the a an of in to for at by is on and or by it from that this as has was its be who when with may would which".split())


def training_plan():
    paths = (Path(__file__), HERE/"plan.json", PREVIOUS/"plan.json", PREVIOUS/"fit.py",
             NATIVE, *[PATHS[d] for d in DONORS])
    return {
        "pins": {str(p.relative_to(RUNS.parent)): guard.suite.pin(p) for p in paths},
        "linked_feature_plan": guard.suite.pin(HERE/"plan.json"),
        "held": prior.plan()["held"], "seed": 24172721, "budgets": [64, 256],
        "ridge": 1.0, "semantic_scale": 4.0, "bonus_scale": 20.0,
        "fit_delivery": 0.65, "fit_send_probability": 0.65,
        "donors": list(DONORS),
    }


def extract_features():
    outputs = guard.historical.report.load(HERE/"evidence/labels.jsonl")
    raw = {}
    for row in outputs:
        ident = row["id"]
        labels = {label: row["logits"][letter] for letter, label in row["labels"].items()}
        raw.setdefault(ident, []).append(labels)
    result = {}
    for ident, observations in raw.items():
        assert len(observations) == 2
        means = {label: sum(row[label] for row in observations)/2 for label in observations[0]}
        margin = means["yes"] - max(means["no"], means["uncertain"])
        result[ident] = {"averaged_logits": means, "margin": margin, "per_order": observations}
    assert set(result) == {f"{key}/{name}" for key, name in product(pairs(), QUESTIONS)}
    return result


def vector(features, ident, spec):
    return np.array([1.0] + [
        float(np.tanh(features[f"{ident}/{q}"]["margin"] / spec["semantic_scale"])) for q in QUESTIONS
    ])


def core_2417():
    c = read(PATHS["2417"])
    lead = sum(row["points"] for row in c["public"])
    first = [lead+row["points"] for row in c["delegate"]]
    last = [lead+row["points"] for row in c["clause"]]
    joint = [a+b-lead for a, b in product(first, last)]
    return np.array([lead]+first+last+joint, dtype=float)


def donor_payoff(docket):
    case = read(PATHS[docket])
    lead = sum(row["weight"] for row in case["public"])
    if docket == "2721":
        early, late = case["early_statements"], case["late_clauses"]
        pairs = {tuple(row["requires"]): row["weight"] for row in case["comparisons"]}
        actual = [lead+a["weight"]+b["weight"]+pairs.get((a["id"], b["id"]), 0)
                  for a, b in product(early, late)]
    else:
        early, late = list(case["early"].values()), list(case["late"].values())
        compiled = read(NATIVE)["compiled"]
        actual = [compiled[f"{a}/{b}"]["scores"]["admitted"] for a, b in product(case["early"], case["late"])]
    first, last = ([lead+row["weight"] for row in roles] for roles in (early, late))
    return (lead, first, last, actual)


def train_donor(spec, features, donor_envs):
    logs, observed = {}, {}
    states = {}
    for docket in spec["donors"]:
        lead, first, last, actual = donor_envs[docket]
        rng = np.random.default_rng(spec["seed"]+int(docket))
        logs[docket] = []
        observed[docket] = {}
        for n in range(max(spec["budgets"])):
            i, j = int(rng.integers(len(first))), int(rng.integers(len(last)))
            send, delivery, return_delivery = rng.random(3)
            arrives = (send < spec["fit_send_probability"]) and (delivery < spec["fit_delivery"])
            back = return_delivery < spec["fit_delivery"]
            label = f"{docket}/{i}/{j}"
            if arrives and back:
                released = actual[i*len(last)+j]
                residual = released - (first[i]+last[j]-lead)
                observed[docket][label] = residual
            else:
                released = first[i] if arrives else last[j] if back else lead
            logs[docket].append({"episode": n+1, "view": i, "reply": j,
                                 "first": bool(arrives), "back": bool(back), "released": released})
            if n+1 in spec["budgets"]:
                states.setdefault(n+1, {}).update(observed[docket])
    fits = {}
    for budget, marks in states.items():
        order = sorted(marks)
        x = np.array([vector(features, ident, spec) for ident in order])
        y = np.array([marks[ident]/spec["bonus_scale"] for ident in order])
        # Centered intercept distinguishes pair quality from the donor mean.
        penalty = np.diag([0, spec["ridge"], spec["ridge"]])
        weights = np.linalg.solve(x.T @ x + penalty, x.T @ y)
        fits[budget] = {"coefficients": weights.tolist(), "unique_pair_rewards": marks,
                        "fitted_residuals": dict(zip(order, (spec["bonus_scale"] * (x @ weights)).tolist(), strict=True))}
    return {"fit": fits, "trajectories": logs}


def lexical(text):
    return set(re.findall(r"[a-z]+", text.lower()))-STOPWORDS


def overlap(pair):
    a, b = map(lexical, pair)
    return len(a&b)/max(len(a|b), 1)


def estimated_bonuses(spec, features, fits):
    texts = pairs()
    result = {}
    for group, identifiers in (
        ("2417", [f"2417/{i}/{j}" for i, j in product(range(3), range(2))]),
        ("held_wording", [f"held_wording/{i}/{j}" for i, j in product(range(3), range(2))]),
        ("fiction", [f"fiction/{i}" for i in range(4)]),
    ):
        bonuses = {}
        for budget, fit in fits.items():
            w = np.array(fit["coefficients"])
            bonuses[f"donor_fit_{budget}"] = [
                float(np.clip(vector(features, ident, spec) @ w, 0., 1.0)*spec["bonus_scale"])
                for ident in identifiers
            ]
        for feature in QUESTIONS:
            bonuses[feature] = [spec["bonus_scale"] * (features[f"{ident}/{feature}"]["margin"] > 0)
                                 for ident in identifiers]
        bonuses["both_features"] = [min(values) for values in zip(
            *(bonuses[name] for name in QUESTIONS), strict=True)]
        raw = [overlap(texts[ident]) for ident in identifiers]
        if group != "fiction":
            best = np.array(raw).reshape(3,2).argmax(axis=-1)
            bonuses["lexical"] = [
                spec["bonus_scale"] * int(j == best[i] and raw[2*i+j] > 0)
                for i, j in product(range(3), range(2))
            ]
            bonuses["standalone"] = [0.]*6
        result[group] = {"ids": identifiers, "word_overlap": raw, "predictions": bonuses}
    return result


def make_routes(spec, estimates, base):
    results = {}
    for group in ("2417", "held_wording"):
        tables = {name: base + np.array([0.]*6+bonus)
                  for name, bonus in estimates[group]["predictions"].items()}
        states = []
        held = spec["held"]
        for q0, q1, price, mass in product(held["delivery"], held["delivery"], held["prices"], held["priors"]):
            setting = q0, q1, price, np.array(mass)
            routes = {}
            for arm, observed in (("arrival_only", np.ones(3, dtype=int)), ("peer", np.arange(1,4))):
                for method, estimated in tables.items():
                    s, r = prior.best_route(estimated, observed, setting)
                    routes[f"{method}/{arm}"] = [s.astype(int).tolist(), r.tolist()]
            states.append({"setting": [q0, q1, price, mass], "routes": routes})
        results[group] = states
    return results


def score(spec, routes, target):
    out = {}
    for group, drafted in routes.items():
        rows = []
        for row in drafted:
            q0, q1, cost, mass = row["setting"]
            setting = q0, q1, cost, np.array(mass)
            scores = {}
            for name, (sender, reply) in row["routes"].items():
                observed = np.arange(1, 4) if name.endswith("/peer") else np.ones(3, dtype=int)
                scores[name] = prior.pay(target, observed, setting, np.array(sender), np.array(reply))
            for arm, observed in (("arrival_only", np.ones(3, dtype=int)), ("peer", np.arange(1,4))):
                scores[f"oracle/{arm}"] = prior.pay(target, observed, setting,
                                                   *prior.best_route(target, observed, setting))
            rows.append({"setting": row["setting"], "values": {k:v.round(8).tolist() for k,v in scores.items()}})
        summary = {label: dict(zip(("utility","release","send_cost","relationship","zero_release"),
                                   np.mean([r["values"][label] for r in rows], axis=0).round(8).tolist(), strict=True))
                   for label in rows[0]["values"]}
        for label, stats in summary.items():
            stats["wins_over_arrival_ceiling"] = sum(
                r["values"][label][0]>r["values"]["oracle/arrival_only"][0] for r in rows
            )
        out[group] = {"summary": summary, "scores": rows}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "fit", "score"))
    args = parser.parse_args()
    spec = training_plan()
    if args.mode == "plan":
        value = spec
    else:
        assert spec == read(HERE/"train-plan.json")
        if args.mode == "fit":
            features = extract_features()
            learnt = train_donor(spec, features, {d: donor_payoff(d) for d in DONORS})
            base = core_2417()
            estimates = estimated_bonuses(spec, features, learnt["fit"])
            value = {"features": features, "training": learnt, "estimated_bonuses": estimates,
                     "routes": make_routes(spec, estimates, base)}
        else:
            learnt = read(HERE/"fit.json")
            reference = np.array(read(TARGET)["tables"]["canonical/authored"])
            value = {"reference_sha256": guard.suite.pin(TARGET), "reference": reference.tolist(),
                     "evaluation": score(spec, learnt["routes"], reference)}
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
