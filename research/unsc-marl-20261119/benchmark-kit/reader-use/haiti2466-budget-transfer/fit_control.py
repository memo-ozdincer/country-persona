"""Compare both saved fits prospectively on the same authored docket banks."""
import json

import numpy as np

import plan


def run():
    prior_run = plan.read(plan.FIT)["training"]
    forecast = plan.read(plan.FORECAST)
    results = {}
    for cap, row in forecast["curves"].items():
        points = np.asarray(row["prefix"])
        results[cap] = {}
        for label in ("uniform", "correlated_duplicates"):
            prior = plan.R.TEST_PRIORS[label]
            measured = plan.fit.PERFECT
            teams = {name: plan.budget.adaptive.contextual_policies(points, prior, model)[0]
                     for name, model in prior_run.items()}
            fitted = teams["budget_fit"]
            even = (fitted[0], fitted[1], *plan.fit.exact(
                points, plan.joint.opening(*fitted[:2], prior), measured, independent=True
            ))
            teams["same_openers_exact_no_request"] = even
            values = {key: plan.joint.metric(value, prior, points, measured) for key, value in teams.items()}
            for key, score in values.items():
                score["net_over_same_openers_exact_no_request"] = score["net"] - values["same_openers_exact_no_request"]["net"]
            values["same_opening_maps"] = bool(all(
                np.array_equal(a, b) for a,b in zip(teams["budget_fit"][:2], teams["unbounded_fit"][:2], strict=True)
            ))
            results[cap][label] = values
    assert abs(results["70"]["uniform"]["budget_fit"]["net"] -
               forecast["aggregate_uniform_modeled"]["learned"]["net"]) < 1.e-12
    return results


if __name__ == "__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
