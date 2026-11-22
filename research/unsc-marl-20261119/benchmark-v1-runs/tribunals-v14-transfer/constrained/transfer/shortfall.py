"""Audit direct adaptive optimization of the smallest quality shortfall."""
import json
import importlib.util
from pathlib import Path
from statistics import mean

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("crosscase_floor_audit", HERE / "transfer.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
EPS, TEAM, FIXED = audit.EPS, audit.TEAM, audit.FIXED
coefficients, solve, provider = audit.coefficients, audit.solve, audit.provider
a, o, vertices, wire = audit.a, audit.o, audit.vertices, audit.wire
comparison, digest, forecast_data = audit.comparison, audit.digest, audit.forecast_data
held, replay = audit.held, audit.replay


def optimize_shortfall(scenarios):
    best_quality, pool = -np.inf, []
    for index, q in enumerate(o.fit.MAPS):
        coefs = coefficients(q, scenarios)
        quality = float(solve(coefs, quality_only=True)[-1])
        if quality > best_quality + EPS:
            pool.clear()
        if quality >= best_quality - EPS:
            pool.append((quality, index, coefs))
        best_quality = max(quality, best_quality)
    selected = None
    for quality, index, coefs in pool:
        if quality < best_quality - EPS:
            continue
        boundary = list(coefs)
        boundary[-2] = coefs[-2] - best_quality + EPS / 10
        solution = solve(boundary)
        if solution is not None and (selected is None or solution[-1] > selected[2][-1] + EPS):
            selected = index, coefs, solution
    assert selected is not None
    index, coefs, solution = selected
    return best_quality, provider(o.fit.MAPS[index], coefs, solution)


def run():
    locked = wire.n.read(HERE / "plan.json")
    prior = wire.n.read(HERE / "results.json")
    assert prior["plan_sha256"] == digest(HERE / "plan.json")
    rows = []
    for row in prior["rows"]:
        original = row["updated"][TEAM]
        after = original
        evidence = {}
        if row["expanded_searches"].get(TEAM, {}).get("qualified") is False:
            case, label, info, offset = (row[k] for k in ("case", "law", "prior_information", "review_offset"))
            points = np.array(locked["banks"][case], dtype=float)
            visible = points.copy()
            visible[[3, 7]] = np.nan
            opening = tuple(np.array(desk) for desk in row["opening"])
            actual, _ = a.laws()[label]
            priors = [actual] if info == "exact" else vertices(label)
            scenarios = forecast_data(visible, np.clip(points[3] + offset, 0, 70), priors, opening)
            bound, policy = optimize_shortfall(scenarios)
            assert bound < -EPS
            mass = o.opening(*opening, actual)
            oracles = o.controls(points, mass, actual, opening)
            after = held(policy, points, actual, opening, oracles, stochastic=True)
            margins = []
            for s in scenarios:
                realized = replay(s["prior"], opening, policy, s["grade"])
                margins.append(realized["released"] - s["quality_floor"])
            assert np.isclose(min(margins), bound, atol=EPS, rtol=0)
            evidence = {"best_worst_forecast_quality_margin": bound,
                        "realized_forecast_quality_margins": margins, "policy": [v.tolist() for v in policy]}
        rows.append({k: row[k] for k in ("case", "law", "prior_information", "review_offset")} |
                    {"original": original, "after": after, "expanded": evidence,
                     "strongest_matched_fixed_net": max(row["updated"][FIXED]["net"], row["old"][FIXED]["net"])})
    report = {}
    for name, group in (("all", rows), ("expanded", [r for r in rows if r["expanded"]])):
        report[name] = {
            "conditions": len(group),
            "held_net_change": comparison([r["after"]["net"] - r["original"]["net"] for r in group]),
            "held_quality_change": comparison([r["after"]["released"] - r["original"]["released"] for r in group]),
            "held_cost_change": mean(r["after"]["cost"] - r["original"]["cost"] for r in group),
            **{label: {
                "below_silence": sum(r[label]["over_informed_silence_quality"] < -EPS for r in group),
                "vs_matched_fixed": comparison([r[label]["net"] - r["strongest_matched_fixed_net"] for r in group]),
                "vs_informed_fixed": comparison([r[label]["over_informed_fixed"] for r in group]),
            } for label in ("original", "after")},
        }
    pins = (Path(__file__), HERE / "shortfall-protocol.md", HERE / "results.json", HERE / "plan.json")
    return {"summary": report, "rows": rows, "sha256": {p.name: digest(p) for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
