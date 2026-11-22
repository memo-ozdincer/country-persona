"""Check whether the full-information net losses reflect the documentary floor."""
import numpy as np

import learned_frontier as g

m, n = g.m, g.n
TOL = 1e-10


def run():
    receipt = n.read(g.HERE / "learned-information.json")
    locked = n.read(g.HERE / "information.json")
    priors = g.a.laws()
    initial = n.read(m.o.replan.study.OLD)["training"]["budget_fit"]
    summary = {}
    for row in locked["runs"]:
        group = f"{row['suite']}/{row['prior_information']}"
        selected = next(v for v in receipt["details"][f"{group}/8"]
                        if v["case"] == row["case"] and v["prior"] == row["prior"])
        if selected["net_over_fixed"] >= -TOL:
            continue
        bank = np.array(row["bank"])
        actual, dominant = priors[row["prior"]]
        advertised = actual if row["prior_information"] == "correct_mixture" else dominant
        opening = m.o.replan.study.opening(g.f.views(bank)["4"], advertised, initial)
        mass = m.o.opening(*opening, actual)
        controls = m.o.controls(bank, mass, actual, opening)
        options = {k: v for k, v in controls.items() if k != "exact_ask_reply"}
        fixed = max(v["net"] for v in options.values())
        silence = options["exact_no_request"]["released"]
        same_floor = max(v["net"] for v in options.values() if v["released"] >= silence - TOL)
        net = selected["net_over_fixed"] + fixed
        summary.setdefault(group, []).append({"case": row["case"], "prior": row["prior"],
                                               "unrestricted_margin": selected["net_over_fixed"],
                                               "quality_matched_margin": net - same_floor})
    return {"negative_full_grade_rows": summary}


if __name__ == "__main__":
    g.s.q.e.emit(run())
