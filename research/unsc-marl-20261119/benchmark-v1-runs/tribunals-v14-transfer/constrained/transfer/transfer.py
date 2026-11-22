"""Replay the conditional stochastic update on five previously scored UN banks."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from mixed_floor import best_fixed_tradeoffs, provider, replay
from solve_floor import coefficients, deterministic, forecast_data, solve, EPS
from prior_qualification import pick, vertices
from routing_transfer import a, digest, f, interval, o, wire, NUMBERED, POLICY

D = interval.D
TEAM, FIXED = "interval_team", "interval_fixed"
FIXED_MAPS = np.array([np.where(D.CHAIR_LEGAL[:, target], target, 0) for target in range(4)])
INPUTS = {
    "historical": POLICY.parent / "information.json",
    "somalia": NUMBERED / "somalia2753/numeric-results.json",
    "opening_checkpoint": o.replan.study.OLD,
}


def plan():
    historical = {}
    for row in wire.n.read(INPUTS["historical"])["runs"]:
        if row["suite"] == "historical":
            assert historical.setdefault(row["case"], row["bank"]) == row["bank"]
    assert set(historical) == {"myanmar", "unifil", "unama", "emergency"}
    somalia = wire.n.read(INPUTS["somalia"])["score_banks"]
    assert somalia["native"] == somalia["menu_order"]
    banks = historical | {"somalia": somalia["native"]}
    assert all(len(b) == 8 and all(0 <= grade <= 70 for grade in b) for b in banks.values())
    files = {**INPUTS, "analysis": Path(__file__), "protocol": HERE / "protocol.md",
             "floor_optimizer": HERE.parent / "solve_floor.py",
             "stochastic_runtime": HERE.parent / "mixed_floor.py",
             "candidate_selection": HERE.parents[1] / "prior_qualification.py"}
    return {"banks": dict(sorted(banks.items())), "conditions": len(banks) * 18,
            "sha256": {name: digest(file) for name, file in files.items()}}


def full_search(maps, scenarios, deterministic_audit=False):
    bounds = []
    for i, q in enumerate(maps):
        coefs = coefficients(q, scenarios)
        sol = solve(coefs)
        if sol is not None:
            bounds.append((float(sol[-1]), i, coefs, sol))
    bounds.sort(key=lambda x: (-x[0], x[1]))
    if not bounds:
        return None, None, {"qualifying_relaxed_maps": 0, "mixed_integer_calls": 0}
    _, i, coefs, sol = bounds[0]
    stochastic = provider(maps[i], coefs, sol)
    selected, best, calls = None, -np.inf, 0
    if deterministic_audit:
        for value, j, coefs, relaxed in bounds:
            if value <= best + EPS:
                break
            candidate = deterministic(maps[j], coefs, relaxed)
            if candidate is None:
                calls += 1
                integer = solve(coefs, integer=True)
                if integer is not None:
                    candidate = deterministic(maps[j], coefs, integer)
                    assert candidate is not None
            if candidate is not None and candidate[1] > best:
                selected, best = candidate
    return (stochastic, selected,
            {"qualifying_relaxed_maps": len(bounds), "mixed_integer_calls": calls,
             "best_stochastic_worst_net": bounds[0][0],
             "best_deterministic_worst_net": float(best) if selected is not None else None})


def held(policy, points, law, opening, oracles, stochastic=False):
    if stochastic:
        result = replay(law, opening, policy, points)
    else:
        result = o.measure(points, o.opening(*opening, law), law, opening, policy)
    output = {k: float(result[k]) for k in ("released", "cost", "net", "queries")}
    assert output["net"] <= oracles["exact_ask_reply"]["net"] + EPS
    fixed = max(value["net"] for name, value in oracles.items() if name != "exact_ask_reply")
    output["over_informed_fixed"] = output["net"] - fixed
    output["over_informed_silence_quality"] = output["released"] - oracles["exact_no_request"]["released"]
    return output


def audit_bank(name, bank, initializer):
    true_points = np.array(bank, dtype=float)
    visible_points = true_points.copy()
    visible_points[[3, 7]] = np.nan
    rows = []
    for (label, (actual, proxy)), info in product(a.laws().items(), ("exact", "dominant_only")):
        priors = [actual] if info == "exact" else vertices(label)
        # The first four scores are the empty record and the three singletons.
        forecast_base = interval.s.t.cal.estimated(visible_points)
        assert np.isfinite(forecast_base).all()
        opening = o.replan.study.opening(forecast_base, actual if info == "exact" else proxy, initializer)
        oracles = o.controls(true_points, o.opening(*opening, actual), actual, opening)
        cache = {}
        for offset in (-7, 0, 7):
            reported = float(np.clip(true_points[3] + offset, 0, 70))
            original, _ = pick(visible_points, reported, priors, opening, cache)
            results = {key: held(policy, true_points, actual, opening, oracles)
                       for key, (_, policy, _) in original.items()}
            updated = dict(results)
            pure = results[TEAM]
            certificates, actions = {}, {}
            for mode, (_, _, count) in original.items():
                if count:
                    continue
                scenarios = forecast_data(visible_points, reported, priors, opening)
                maps = o.fit.MAPS if mode == TEAM else FIXED_MAPS
                mixed, plain, certificate = full_search(maps, scenarios, deterministic_audit=mode == TEAM)
                certificate["qualified"] = mixed is not None
                if mode == TEAM and plain is not None:
                    pure = held(plain, true_points, actual, opening, oracles)
                    actions["deterministic_expanded_team"] = [item.tolist() for item in plain]
                if mode == FIXED and mixed is None:
                    q, coefs, sol = best_fixed_tradeoffs(maps, scenarios)["fixed_best_quality"]
                    mixed = provider(q, coefs, sol)
                if mixed is not None:
                    updated[mode] = held(mixed, true_points, actual, opening, oracles, stochastic=True)
                    certificate["randomized_states"] = int(np.sum((mixed[1] > EPS).sum(-1) > 1))
                    actions[mode] = [item.tolist() for item in mixed]
                    if certificate["qualified"]:
                        for scenario in scenarios:
                            value = replay(scenario["prior"], opening, mixed, scenario["grade"])
                            assert value["released"] >= scenario["quality_floor"] - EPS
                certificates[mode] = certificate
            rows.append({"case": name, "law": label, "prior_information": info, "review_offset": offset,
                         "opening": [row.tolist() for row in opening],
                         "old": results, "updated": updated, "deterministic_expanded_team": pure,
                         "original_eligible": {key: int(item[2]) for key, item in original.items()},
                         "expanded_searches": certificates, "updated_policies": actions})
    return rows


def comparison(values):
    wins, losses = sum(v > EPS for v in values), sum(v < -EPS for v in values)
    return {"wins": wins, "ties": len(values) - wins - losses, "losses": losses,
            "mean": mean(values), "worst": min(values)}


def summary(rows):
    result = {}
    for name, group in [("all", rows)] + [(name, [r for r in rows if r["case"] == name])
                                       for name in sorted({r["case"] for r in rows})]:
        def strongest(r):
            return max(r["old"][FIXED]["net"], r["updated"][FIXED]["net"])

        methods = {"original": [r["old"][TEAM] for r in group],
                   "deterministic_expansion": [r["deterministic_expanded_team"] for r in group],
                   "stochastic_expansion": [r["updated"][TEAM] for r in group]}
        report = {mode: {
                    "net_vs_strongest_matched_fixed": comparison([t["net"] - strongest(r)
                                                                for t, r in zip(teams, group, strict=True)]),
                    "net_vs_informed_fixed": comparison([t["over_informed_fixed"] for t in teams]),
                    "below_silence": sum(t["over_informed_silence_quality"] < -EPS for t in teams)}
                  for mode, teams in methods.items()}
        report["changes"] = {
            "team_searches": sum(TEAM in r["expanded_searches"] for r in group),
            "fixed_searches": sum(FIXED in r["expanded_searches"] for r in group),
            "fixed_qualified": sum(r["expanded_searches"].get(FIXED, {}).get("qualified", False) for r in group),
            "team_outcomes": dict(sorted(Counter(
                ("no_qualified_team" if not r["expanded_searches"][TEAM]["qualified"] else
                 "deterministic_also_qualifies" if r["expanded_searches"][TEAM]["best_deterministic_worst_net"] is not None
                 else "requires_randomized_reply")
                for r in group if TEAM in r["expanded_searches"]).items())),
            "stochastic_vs_original_team": comparison([r["updated"][TEAM]["net"] - r["old"][TEAM]["net"] for r in group]),
        }
        result[name] = report
    return result


def run():
    locked = wire.n.read(HERE / "plan.json")
    assert locked == plan()
    init = wire.n.read(INPUTS["opening_checkpoint"])["training"]["budget_fit"]
    rows = []
    for name, bank in locked["banks"].items():
        rows.extend(audit_bank(name, bank, init))
        print(f"Scored {name}", file=sys.stderr, flush=True)
    assert len(rows) == locked["conditions"]
    return {"summary": summary(rows), "rows": rows, "plan_sha256": digest(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
