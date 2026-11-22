"""Compare the frozen learned selector at each information budget."""
from hashlib import sha256
from pathlib import Path

import numpy as np

import information_frontier as f

a, s, n, m, HERE = f.a, f.s, f.n, f.m, f.HERE


def run():
    locked_path = HERE / "information.json"
    cases = n.read(locked_path)["runs"]
    fit, sparse = [n.read(p) for p in (m.HERE.parents[1] / "fit.json", m.HERE.parent / "sparse-results.json")]
    parameters = tuple([np.array(v) for v in p["parameters"]] for p in (fit, sparse))
    initial = n.read(m.o.replan.study.OLD)["training"]["budget_fit"]
    priors = a.laws()
    result = {}
    for row in cases:
        actual, proxy = priors[row["prior"]]
        announced = actual if row["prior_information"] == "correct_mixture" else proxy
        bank = np.array(row["bank"])
        views = f.views(bank)
        opening = m.o.replan.study.opening(views["4"], announced, initial)
        seen = m.o.opening(*opening, announced)
        held = m.o.opening(*opening, actual)
        controls = m.o.controls(bank, held, actual, opening)
        reference = max(v["net"] for k, v in controls.items() if k != "exact_ask_reply")
        for budget, forecast in views.items():
            script, learn = s.catalog(forecast, seen, announced, opening, parameters)
            policies = script | learn
            grades = {k: m.o.measure(forecast, seen, announced, opening, v) for k, v in policies.items()}
            feasible = [k for k, v in grades.items() if v["released"] >= grades["quiet"]["released"] - 1e-10]
            chosen = max(feasible, key=lambda k: (grades[k]["net"], k == "quiet"))
            assessed = m.o.measure(bank, held, actual, opening, policies[chosen])
            row_key = f"{row['suite']}/{row['prior_information']}/{budget}"
            result.setdefault(row_key, []).append({"case": row["case"], "prior": row["prior"], "selected": chosen,
                                                  "net_over_fixed": assessed["net"] - reference,
                                                  "exact_forecast_net_over_fixed": row["grades"][budget]["net_over_fixed"]})
    summary = {}
    for key, rows in result.items():
        net = [v["net_over_fixed"] for v in rows]
        summary[key] = {"conditions": len(net), "wins": sum(v > 1e-10 for v in net),
                        "losses": sum(v < -1e-10 for v in net), "mean_margin": sum(net) / len(net),
                        "selected_learned": sum(x["selected"] in ("dense", "sparse") for x in rows)}
    pins = (Path(__file__), locked_path, Path(f.__file__), HERE / "learned-frontier-protocol.md")
    return {"summary": summary, "details": result,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    s.q.e.emit(run())
