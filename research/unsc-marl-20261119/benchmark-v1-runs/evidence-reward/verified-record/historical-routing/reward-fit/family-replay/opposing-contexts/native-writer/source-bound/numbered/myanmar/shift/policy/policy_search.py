"""Improve a tabular sender and responder with modeled team reward."""
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import information_frontier as f

a, s, n, m = f.a, f.s, f.n, f.m
o, D = m.o, m.D
TOL = 1e-10


def improve(points, mass, prior, opening):
    """Search legal one-state chair deviations with an exact best response."""
    visits = mass.sum((0, 1))
    cache = {}

    def team(asks):
        key = tuple(int(x) for x in asks)
        if key not in cache:
            asks = np.array(key)
            pair = asks, o.choose_response(asks, mass, points)
            cache[key] = pair, o.measure(points, mass, prior, opening, pair)
        return cache[key]

    options = np.flatnonzero(visits > TOL)
    fixed = {target: team(np.where(D.CHAIR_LEGAL[:, target], target, 0))
             for target in range(4)}
    initial = max(fixed, key=lambda t: (fixed[t][1]["net"], -t))
    current = fixed[initial]
    trace = []
    while True:
        visits_in_round = []
        for mask in options:
            old = current[0][0][mask]
            for target in np.flatnonzero(D.CHAIR_LEGAL[mask]):
                if target == old:
                    continue
                asks = current[0][0].copy()
                asks[mask] = target
                value = team(asks)
                if value[1]["net"] > current[1]["net"] + TOL:
                    visits_in_round.append((value[1]["net"], -int(mask), -int(target), value))
        if not visits_in_round:
            break
        _, mask, target, current = max(visits_in_round, key=lambda x: x[:3])
        trace.append({"mask": -mask, "target": -target, "forecast_net": current[1]["net"],
                      "forecast_release": current[1]["released"]})
    oracle = o.exact_parts(mass, points)["exact_ask_reply"]
    ceiling = o.measure(points, mass, prior, opening, oracle)
    assert current[1]["net"] <= ceiling["net"] + TOL
    gap = ceiling["net"] - current[1]["net"]
    return current[0], {"initial_target": initial, "initial": fixed[initial][1],
                        "final": current[1], "updates": trace, "evaluated": len(cache),
                        "oracle_gap": gap, "chair_actions": current[0][0].tolist(),
                        "reply_actions": current[0][1].tolist()}


def summarize(rows):
    result = {}
    for suite in ("historical", "synthetic_dense", "synthetic_sparse"):
        for prior in ("correct_mixture", "dominant_only"):
            for budget in ("4", "5", "7", "8"):
                selected = [r["budgets"][budget] for r in rows
                            if (r["suite"], r["prior_information"]) == (suite, prior)]
                margin = [r["held_net_over_fixed"] for r in selected]
                quality = [r["held_quality_over_silence"] for r in selected]
                result[f"{suite}/{prior}/{budget}"] = {
                    "rows": len(selected), "wins": sum(x > TOL for x in margin),
                    "losses": sum(x < -TOL for x in margin), "mean_margin": sum(margin) / len(margin),
                    "documentary_losses": sum(x < -TOL for x in quality),
                    "forecast_optima": sum(r["oracle_gap"] <= TOL for r in selected),
                    "avg_tables": sum(r["evaluated"] for r in selected) / len(selected)}
    return result


def run():
    checkpoint = HERE.parent / "information.json"
    previous = n.read(checkpoint)["runs"]
    initial = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    laws = a.laws()
    rows = []
    for row in previous:
        bank = np.array(row["bank"])
        actual, proxy = laws[row["prior"]]
        declared = actual if row["prior_information"] == "correct_mixture" else proxy
        scores = f.views(bank)
        opening = o.replan.study.opening(scores["4"], declared, initial)
        mass = o.opening(*opening, declared)
        held = o.opening(*opening, actual)
        control = o.controls(bank, held, actual, opening)
        fixed = max(r["net"] for key, r in control.items() if key != "exact_ask_reply")
        silence = control["exact_no_request"]["released"]
        values = {}
        for budget, forecast in scores.items():
            actions, learned = improve(forecast, mass, declared, opening)
            result = o.measure(bank, held, actual, opening, actions)
            assert result["net"] <= control["exact_ask_reply"]["net"] + TOL
            if learned["oracle_gap"] <= TOL and row["prior_information"] == "correct_mixture" and budget == "8":
                assert abs(result["net"] - control["exact_ask_reply"]["net"]) <= TOL
            values[budget] = learned | {"held_net_over_fixed": result["net"] - fixed,
                                         "held_quality_over_silence": result["released"] - silence,
                                         "held_query_rate": result["queries"]}
        rows.append({k: row[k] for k in ("suite", "case", "prior", "prior_information", "bank")} | {"budgets": values})
    assert len(rows) == 120
    pins = (Path(__file__), HERE / "protocol.md", checkpoint, Path(f.__file__), Path(o.__file__))
    return {"rows": rows, "summary": summarize(rows), "exhaustive_chair_tables": len(o.fit.MAPS),
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    s.q.e.emit(run())
