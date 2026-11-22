"""Optimize deterministic joint routing with an explicit robust quality floor."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np
import scipy
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from prior_qualification import vertices, D
from routing_transfer import a, calibration, interval, o, runtime, wire

EPS = 1e-7


def forecast_data(points, reported, priors, opening):
    forecasts = [interval.forecasts(calibration(points), np.clip(reported + offset, 0, 70))
                 for offset in (-7, 0, 7)]
    rows = []
    fixed_maps = [np.where(D.CHAIR_LEGAL[:, target], target, 0) for target in range(4)]
    for grade, prior in product(forecasts, priors):
        mass = o.opening(*opening, prior)
        controls = [o.measure(grade, mass, prior, opening, (q, o.choose_response(q, mass, grade)))
                    for q in fixed_maps]
        opening_cost = prior.sum(1) @ D.SEND_COST[opening[0]] + prior.sum(0) @ D.SEND_COST[opening[1]]
        rows.append({"grade": grade, "prior": prior, "mass": mass, "quality_floor": controls[0]["released"],
                     "fixed_net": max(r["net"] for r in controls), "opening_cost": opening_cost})
    return rows


def coefficients(queries, rows):
    heard = o.fit.heard(D.one_hot(queries))
    seen = np.stack([np.einsum("rbm,mt->rbt", r["mass"], heard) for r in rows])
    reachable = tuple(zip(*np.nonzero(seen.max(axis=0) > 0), strict=True))
    legal = np.broadcast_to(D.FINAL_LEGAL, (8, 4, 4, 4))
    entries = [(r, b, t, int(action)) for r, b, t in reachable
               for action in np.flatnonzero(legal[r, b, t])]
    states = {state: i for i, state in enumerate(reachable)}
    eq = np.zeros((len(states), len(entries) + 1))
    for i, item in enumerate(entries):
        eq[states[item[:3]], i] = 1
    release, nets, quality_offset, net_offset = [], [], [], []
    for row, probabilities in zip(rows, seen, strict=True):
        mass, grade = row["mass"], row["grade"]
        opening_mass = mass.sum(axis=(0, 1))
        base = opening_mass @ grade
        uplifts = D.LAST @ grade - grade[:, None]
        effect = np.einsum("rbm,mt,mc->rbtc", mass, heard, uplifts)
        release.append([effect[key] for key in entries])
        nets.append([effect[key] - probabilities[key[:3]] * D.SEND_COST[key[3]] for key in entries])
        quality_offset.append(base - row["quality_floor"])
        net_offset.append(base - row["opening_cost"] - opening_mass @ D.QUERY_COST[queries] - row["fixed_net"])
    return entries, eq, np.array(release), np.array(nets), np.array(quality_offset), np.array(net_offset)


def problems(coeffs, quality_only):
    entries, eq, release, nets, quality_offset, net_offset = coeffs
    gain, offset = (release, quality_offset) if quality_only else (nets, net_offset)
    ub = np.column_stack((-gain, np.ones(len(gain))))
    bound = offset
    if not quality_only:
        ub = np.vstack((ub, np.column_stack((-release, np.zeros(len(release))))))
        bound = np.r_[bound, quality_offset + EPS / 10]
    objective = np.r_[np.zeros(len(entries)), -1]
    return objective, eq, ub, bound


def solve(coeffs, quality_only=False, integer=False):
    objective, eq, ub, bound = problems(coeffs, quality_only)
    n = len(objective) - 1
    ones = np.ones(len(eq))
    if integer:
        result = milp(objective, integrality=np.r_[np.ones(n), 0],
                      bounds=Bounds(np.r_[np.zeros(n), -np.inf], np.r_[np.ones(n), np.inf]),
                      constraints=(LinearConstraint(eq, ones, ones), LinearConstraint(ub, -np.inf, bound)),
                      options={"mip_rel_gap": 0})
    else:
        result = linprog(objective, A_ub=ub, b_ub=bound, A_eq=eq, b_eq=ones,
                         bounds=[(0, 1)] * n + [(None, None)],
                         options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9})
    if result.status == 2:
        return None
    assert result.success, result.message
    assert np.all(ub @ result.x <= bound + EPS) and np.allclose(eq @ result.x, ones, atol=EPS, rtol=0)
    if integer:
        assert -result.mip_dual_bound <= -result.fun + EPS
    return result.x


def deterministic(queries, coeffs, solution):
    local = solution[:-1]
    if np.max(np.abs(local - np.rint(local))) > EPS:
        return None
    entries, eq, release, nets, floor, fixed = coeffs
    actions = np.rint(local)
    assert np.array_equal(eq[:, :-1] @ actions, np.ones(len(eq)))
    if np.min(release @ actions + floor) < -EPS:
        return None
    response = np.zeros((8, 4, 4), dtype=int)
    for (r, b, t, c), use in zip(entries, actions, strict=True):
        if use:
            response[r, b, t] = c
    return (queries, response), float(np.min(nets @ actions + fixed))


def optimize(maps, scenarios):
    upper, best_quality = [], -np.inf
    for index, q in enumerate(maps):
        coefs = coefficients(q, scenarios)
        quality = solve(coefs, quality_only=True)
        assert quality is not None
        best_quality = max(best_quality, quality[-1])
        if quality[-1] >= -EPS:
            relaxed = solve(coefs)
            if relaxed is not None:
                upper.append((relaxed[-1], index, coefs, relaxed))
    best, incumbent, integer_calls = None, -np.inf, 0
    bounds = sorted(upper, key=lambda row: (-row[0], row[1]))
    for upper_value, index, coefs, relaxed in bounds:
        if upper_value <= incumbent + EPS:
            break
        found = deterministic(maps[index], coefs, relaxed)
        if found is None:
            integer_calls += 1
            solution = solve(coefs, integer=True)
            found = None if solution is None else deterministic(maps[index], coefs, solution)
            assert solution is None or found is not None
        if found is not None and found[1] > incumbent:
            best, incumbent = found
    audit = {"chair_maps_examined": len(maps), "maps_with_relaxed_floor": len(upper),
             "best_relaxed_quality_margin": float(best_quality),
             "best_relaxed_net_margin": float(bounds[0][0]) if bounds else None,
             "mixed_integer_calls": integer_calls,
             "best_deterministic_net_margin": incumbent if best is not None else None}
    return best, audit


def evaluate(policy, points, prior, opening):
    result = o.measure(points, o.opening(*opening, prior), prior, opening, policy)
    return {field: result[field] for field in ("released", "cost", "net", "queries")}


def run():
    label, source = "uniform", "myanmar"
    settings = wire.n.read(HERE.parent / "source-policies.json")["contexts"]
    opening = settings[f"{source}/{label}/dominant_only"]["opening"]
    assert opening == settings[f"unifil/{label}/dominant_only"]["opening"]
    opening = tuple(np.array(row) for row in opening)
    record = wire.n.read(HERE.parent / "routing-results.json")
    points = np.array(record["banks"][0]["points"], dtype=float)
    focus = next(r for r in record["rows"] if r["context"] == f"{source}/{label}/dominant_only"
                 and r["review_offset"] == 7)
    scenarios = forecast_data(points, focus["reported_target_pair_grade"], vertices(label), opening)
    assert len(scenarios) == 9
    fixed = np.array([np.where(D.CHAIR_LEGAL[:, target], target, 0) for target in range(4)])
    assert all(any(np.array_equal(row, q) for row in o.fit.MAPS) for q in fixed)
    selected, audits = {}, {}
    for name, maps in (("interval_team", o.fit.MAPS), ("interval_fixed", fixed)):
        selected[name], audits[name] = optimize(maps, scenarios)
    true, _ = a.laws()[label]
    oracle = o.controls(points, o.opening(*opening, true), true, opening)
    silence = oracle["exact_no_request"]
    exact_fixed_net = max(value["net"] for name, value in oracle.items() if name != "exact_ask_reply")
    results = {}
    for name, policy in selected.items():
        if policy is None:
            continue
        data = evaluate(policy, points, true, opening)
        quality = [evaluate(policy, r["grade"], r["prior"], opening)["released"] - r["quality_floor"]
                   for r in scenarios]
        margin = [evaluate(policy, r["grade"], r["prior"], opening)["net"] - r["fixed_net"]
                  for r in scenarios]
        assert min(quality) >= -EPS
        assert np.isclose(min(margin), audits[name]["best_deterministic_net_margin"], rtol=0, atol=EPS)
        results[name] = data | {"table": [p.tolist() for p in policy], "prospective_quality_margins": quality,
                                "prospective_net_margins": margin, "quality_over_silence": data["released"] - silence["released"],
                                "net_over_exact_fixed": data["net"] - exact_fixed_net}
    if len(results) == 2:
        brute_force, _ = runtime.trace_table(true, opening, selected, points)
        for name, values in brute_force.items():
            assert all(np.isclose(values[field], results[name][field], rtol=0, atol=EPS)
                       for field in ("net", "released", "cost", "queries"))
    inputs = (Path(__file__), HERE / "protocol.md", *(HERE.parent / name for name in
              ("source-policies.json", "prior-results.json", "routing-results.json")))
    prior_rows = wire.n.read(inputs[-2])["rows"]
    old = next(r for r in prior_rows if focus["context"] in r["contexts"] and r["review_offset"] == 7)["prior_envelope"]
    return {"scipy": scipy.__version__, "scenario_count": len(scenarios), "forecast_bank": [r["grade"].tolist() for r in scenarios],
            "opening_tables": [row.tolist() for row in opening], "tolerance": EPS, "search": audits,
            "results": results, "archived": old,
            "sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in inputs}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
