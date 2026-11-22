"""Optimize team and fixed policies under the same content-admission model."""
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import numpy as np

import content_stress as c

s, o, a, r, n, HERE = c.s, c.o, c.a, c.r, c.n, c.HERE
original_payoff, original_measure = o.payoff, o.measure


def change(points):
    mask = np.arange(8)
    return (1 - o.D.LOSS) * (points[mask | 4] - points[mask & ~4])


def price(points, mass, actions):
    q, reply = actions
    hears = o.fit.heard(o.D.one_hot(q))[:, 3]
    receives = np.einsum("rbm,m,rb->m", mass, hears, reply[:, :, 3] == 3)
    return float(receives @ change(points))


def run():
    original_path = HERE / "content-stress.json"
    old = n.read(original_path)
    bank_path = c.c.t.HERE / "numeric-results.json"
    bank = np.array(n.read(bank_path)["score_banks"]["native"])
    initialization = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    calibration = {i: bank[i] for i in range(7) if i != 3}
    results = {}

    for rate in (0., .25, .50, 1.):
        def payoff(points):
            reward = original_payoff(points).copy()
            reward[:, 3, 3] -= rate * change(points)
            return reward

        def measure(points, mass, prior, opening, actions):
            base = original_measure(points, mass, prior, opening, actions)
            lost = rate * price(points, mass, actions)
            return base | {"released": base["released"] - lost, "net": base["net"] - lost}

        rows = {}
        with patch.object(o, "payoff", payoff), patch.object(o, "measure", measure):
            for label, (actual, dominant) in a.laws().items():
                for state, prior in (("correct", actual), ("dominant", dominant)):
                    openings = o.replan.study.opening(r.f.views(bank)["4"], prior, initialization)
                    apparent, truth = o.opening(*openings, prior), o.opening(*openings, actual)
                    cache = {}
                    for shift in (-7, 0, 7):
                        key = f"{label}/{state}/{shift}"
                        settings = r.evaluate_locked(calibration, bank[3] + shift, prior, openings, apparent, cache)
                        row = {}
                        for arm in ("interval_team", "interval_fixed"):
                            selected, actions = settings[arm]
                            measured = measure(bank, truth, actual, openings, actions)
                            if rate == 0:
                                assert abs(price(bank, truth, actions) - old["rows"][key][arm]["exposure"]["points_at_risk"]) < 1e-10
                                assert abs(measured["net"] - old["rows"][key][arm]["net"]["0.0"]) < 1e-10
                            row[arm] = {"policy": selected, "net": measured["net"], "released": measured["released"],
                                        "net_change_vs_frozen": measured["net"] - old["rows"][key][arm]["net"][str(rate)]}
                        rows[key] = row
        margins = [entry["interval_team"]["net"] - entry["interval_fixed"]["net"] for entry in rows.values()]
        results[str(rate)] = {"wins": sum(m > 1e-10 for m in margins), "losses": sum(m < -1e-10 for m in margins),
                              "mean_net_margin": sum(margins) / len(margins),
                              "mean_net_change_vs_frozen": {mode: sum(row[mode]["net_change_vs_frozen"] for row in rows.values()) / len(rows)
                                                            for mode in ("interval_team", "interval_fixed")},
                              "rows": rows}
    pins = (Path(__file__), HERE / "risk-planning.md", original_path, bank_path)
    return {"rates": results, "sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in pins}}


if __name__ == "__main__":
    s.e.emit(run())
