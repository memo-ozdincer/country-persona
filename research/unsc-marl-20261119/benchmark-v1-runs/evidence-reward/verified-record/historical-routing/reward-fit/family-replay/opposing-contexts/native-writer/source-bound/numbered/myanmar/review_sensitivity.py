"""Re-evaluate the locked calibration with one criterion of reviewer disagreement."""
import argparse

import numpy as np

import evaluate_transfer as q

t, m, n = q.t, q.m, q.n


def run(endpoint, results_path):
    verified = n.read(results_path)[endpoint]
    bank = np.array(verified["bank"])
    cases = n.read(t.HERE / "plan.json")
    pair = cases["calibration"]["mask"]
    assert pair != 0
    parameters = tuple([np.array(a) for a in n.read(p)["parameters"]]
                       for p in (m.HERE.parents[1] / "fit.json", m.HERE.parent / "sparse-results.json"))
    original = n.read(m.o.replan.study.OLD)["training"]["budget_fit"]
    result = {}
    for shift in (-7, 0, 7):
        named = {}
        for key, prior in m.o.R.TEST_PRIORS.items():
            row = q.evaluate(bank, prior, pair, parameters, original, review_delta=shift)
            locked = row["approaches"]["locked_pair"]
            anchor = verified["population"][key]
            if shift == 0:
                assert row == anchor
            policy = locked["selected"]
            named[key] = {"selected": policy, "score_estimate": locked["prediction"][pair],
                          "margin_over_oracle_fixed": locked["selected_margin_vs_oracle_fixed"],
                          "released_delta_vs_silence": locked["selected_released_delta_vs_silence"]}
        result[shift] = named
    return {"true_pair_grade": float(bank[pair]), "changes_to_pair_grade_only": result}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--intact", action="store_true")
    results_path = t.HERE / ("intact-results.json" if cli.parse_args().intact else "results.json")
    q.e.emit({endpoint: run(endpoint, results_path) for endpoint in ("native", "rank_normalized")})
