"""Certify the worst-case value of one plan across fixed UNIFIL priors."""
import argparse
import json

import numpy as np

import unifil_final_review as review

study, route = review.study, review.routing
TOL = 1e-8


def solve():
    payoff = 35 + route.points({"weights": (7, 7, 7), "joint": (3, 14)})
    loss = route.TRAIN_LOSS
    matrix = route.receipt_matrix(payoff, loss)
    uniform = route.TEST_PRIORS["uniform"]
    common, count = route.exact_optional(uniform, matrix, loss)
    results = {}
    for name, prior in route.TEST_PRIORS.items():
        optimum, same_count = route.exact_optional(prior, matrix, loss)
        assert same_count == count
        ceiling = route.evaluate(optimum, prior, payoff, loss)["net"]
        independent = route.evaluate(route.best_silent(prior, matrix), prior, payoff, loss)["net"]
        actual = route.evaluate(common, prior, payoff, loss)["net"]
        assert actual <= ceiling + TOL
        results[name] = {"uniform_plan_net": actual, "exact_independent_net": independent,
                         "optional_query_ceiling": ceiling, "gain": actual - independent}
    lower = min(row["gain"] for row in results.values())
    upper = min(row["optional_query_ceiling"] - row["exact_independent_net"] for row in results.values())
    assert lower <= upper + TOL
    return {"scope": "Public-rubric control. The uniform-optimal plan is applied to all declared priors. "
                     "The least per-prior exact gain bounds the best worst-case improvement, including mixtures.",
            "loss": loss, "receipt_payoff": payoff.tolist(), "case_sha256": study.common.runner.digest(study.TASK),
            "lower_worst_case_gain": lower, "upper_worst_case_gain": upper, "certified": upper - lower <= TOL,
            "request_maps_per_exact_solve": count, "plan": [p.tolist() for p in common], "priors": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.parse_args()
    print(json.dumps(solve(), indent=2))
