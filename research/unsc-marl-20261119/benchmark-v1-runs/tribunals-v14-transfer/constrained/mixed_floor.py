"""Deploy the floor-constrained relaxation as a private randomized responder."""
import json
from hashlib import sha256
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from solve_floor import (D, EPS, a, coefficients, forecast_data, o, problems, runtime,
                         solve, vertices, wire)

HERE = Path(__file__).resolve().parent


def unconstrained(coeffs):
    objective, eq, ub, bound = problems(coeffs, quality_only=False)
    n = len(coeffs[-1])
    result = linprog(objective, A_ub=ub[:n], b_ub=bound[:n], A_eq=eq, b_eq=np.ones(len(eq)),
                     bounds=[(0, 1)] * (len(objective) - 1) + [(None, None)],
                     options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9})
    assert result.success
    return result.x


def measures(coeffs, solution):
    _, _, release, nets, floor, fixed = coeffs
    x = solution[:-1]
    return (release @ x + floor, nets @ x + fixed)


def provider(queries, coeffs, optimum):
    response = np.zeros((8, 4, 4, 4))
    response[..., 0] = 1
    entries = coeffs[0]
    for state in {item[:3] for item in entries}:
        response[state] = 0
    for key, p in zip(entries, optimum[:-1], strict=True):
        response[key] = max(p, 0)
    assert np.allclose(response.sum(-1), 1, atol=EPS, rtol=0)
    response /= response.sum(-1, keepdims=True)
    assert np.where(np.broadcast_to(D.FINAL_LEGAL, response.shape), 0, response).sum() == 0
    return queries, response


def choose(probs, draw):
    if not 0 <= draw < 1:
        raise ValueError("Responder draw must be in [0, 1)")
    cumulative = np.cumsum(probs)
    return min(int(np.searchsorted(cumulative, draw, side="right")), int(np.flatnonzero(probs)[-1]))


def replay(law, opening, policy, points):
    q, response = policy
    silent = np.zeros(response.shape[:-1], dtype=int)
    receipt_mass, cost, queries = np.zeros(8), 0., 0.
    for left, right in product(range(8), repeat=2):
        for flags in product((0, 1), repeat=4):
            weight = law[left, right] * (1 - D.LOSS) ** sum(flags) * D.LOSS ** (4 - sum(flags))
            if not weight:
                continue
            initial = runtime.episode((left, right), opening, (q, silent), flags)
            view = initial["responder_view"]
            probs = response[view]
            queries += weight * bool(initial["query"])
            for card, probability in enumerate(probs):
                if probability:
                    interval_midpoint = float(sum(probs[:card]) + probability / 2)
                    if probability > EPS:
                        assert choose(probs, interval_midpoint) == card
                    reply = silent.copy()
                    reply[view] = card
                    branch = runtime.episode((left, right), opening, (q, reply), flags)
                    receipt_mass[branch["receipt"]] += weight * probability
                    cost += weight * probability * branch["cost"]
    assert np.isclose(receipt_mass.sum(), 1, atol=EPS, rtol=0)
    released = float(receipt_mass @ points)
    return {"released": released, "cost": cost, "net": released - cost, "queries": queries,
            "receipt_mass": receipt_mass.tolist()}


def score(name, policy, coeffs, solution, opening, scenarios, true, points, informed):
    scenario_quality, scenario_net = measures(coeffs, solution)
    assert all(np.isfinite(scenario_net))
    if name == "team_at_floor":
        assert min(scenario_quality) >= -EPS
    physical = replay(true, opening, policy, points)
    # Replay the nine forecast scenarios independently of the LP.
    for row, quality, margin in zip(scenarios, scenario_quality, scenario_net, strict=True):
        result = replay(row["prior"], opening, policy, row["grade"])
        assert np.isclose(result["released"] - row["quality_floor"], quality, atol=EPS, rtol=0)
        assert np.isclose(result["net"] - row["fixed_net"], margin, atol=EPS, rtol=0)
    q, reply = policy
    return {"guaranteed_quality_margin": float(min(scenario_quality)),
            "guaranteed_net_margin": float(min(scenario_net)),
            "quality_margins": scenario_quality.tolist(), "net_margins": scenario_net.tolist(),
            "randomized_reply_views": [dict(view=[int(i) for i in view], probabilities=reply[view].tolist())
                                      for view in zip(*np.nonzero((reply > EPS).sum(-1) > 1), strict=True)],
            "chair": q.tolist(), "reply_probabilities": reply.tolist(),
            "held": physical | {"quality_over_silence": physical["released"] - informed["silence"],
                                "net_over_exact_fixed": physical["net"] - informed["fixed_net"]}}


def best_admissible(maps, scenarios):
    selected = None
    for q in maps:
        coefs = coefficients(q, scenarios)
        sol = solve(coefs)
        if sol is not None and (selected is None or sol[-1] > selected[2][-1] + EPS):
            selected = q, coefs, sol
    return selected


def best_fixed_tradeoffs(maps, scenarios):
    controls = {}
    for q in maps:
        coefs = coefficients(q, scenarios)
        quality = solve(coefs, quality_only=True)[-1]
        at_quality = list(coefs)
        at_quality[-2] = coefs[-2] - quality
        sol_quality = solve(at_quality)
        sol_net = unconstrained(coefs)
        for key, solution, selection_key in (("fixed_best_quality", sol_quality, (quality, sol_quality[-1])),
                                              ("fixed_best_net", sol_net, (sol_net[-1],))):
            if key not in controls or selection_key > controls[key][0]:
                controls[key] = (selection_key, (q, coefs, solution))
    return {key: row[1] for key, row in controls.items()}


def run():
    transfer = HERE.parent
    archive = wire.n.read(HERE / "results.json")
    opening = tuple(np.array(row) for row in archive["opening_tables"])
    routed = wire.n.read(transfer / "routing-results.json")
    focus = next(r for r in routed["rows"] if r["context"] == "myanmar/uniform/dominant_only"
                 and r["review_offset"] == 7)
    points = np.array(routed["banks"][0]["points"], dtype=float)
    scenarios = forecast_data(points, focus["reported_target_pair_grade"], vertices("uniform"), opening)
    assert [r["grade"].tolist() for r in scenarios] == archive["forecast_bank"]
    selected = best_admissible(o.fit.MAPS, scenarios)
    assert selected is not None
    assert np.isclose(selected[-1][-1], archive["search"]["interval_team"]["best_relaxed_net_margin"],
                      atol=EPS, rtol=0)
    fixed = np.array([np.where(D.CHAIR_LEGAL[:, target], target, 0) for target in range(4)])
    assert best_admissible(fixed, scenarios) is None
    controls = best_fixed_tradeoffs(fixed, scenarios)
    true, _ = a.laws()["uniform"]
    oracle = o.controls(points, o.opening(*opening, true), true, opening)
    informed = {"silence": oracle["exact_no_request"]["released"],
                "fixed_net": max(v["net"] for k, v in oracle.items() if k != "exact_ask_reply")}
    output = {}
    candidates = {"team_at_floor": selected} | controls
    for name, (q, coefs, sol) in candidates.items():
        output[name] = score(name, provider(q, coefs, sol), coefs, sol, opening, scenarios, true, points, informed)
    inputs = (Path(__file__), HERE / "mixed-protocol.md", HERE / "solve_floor.py", HERE / "results.json",
              transfer / "routing-results.json")
    return {"methods": output, "archived": archive["archived"], "informed": informed,
            "sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in inputs}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
