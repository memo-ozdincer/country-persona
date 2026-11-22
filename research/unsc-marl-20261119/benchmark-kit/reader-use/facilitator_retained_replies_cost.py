"""Price the additional local generation calls in the retained-draft comparisons."""
import argparse
import json
from unittest.mock import patch

import numpy as np

import facilitator_retained_replies_replay as study

fit, D = study.fit, study.D


def run(scenarios, weights):
    outcome = {}
    for name, case in scenarios.items():
        retained = case["comparison"]["retain"]
        matrix = np.asarray(retained["held_admission"])
        points = np.asarray(retained["authored_points"])
        ideal = weights["policies"]["ideal"]
        data = {}
        for label, published in retained["policies"].items():
            prior = fit.ROUTE.TEST_PRIORS[label]
            opener, opening = fit.context(points, prior)
            tail = fit.action_policy(ideal["weights"], points, opening, np.asarray(ideal["feature_channel"]))
            fixed = published["ideal_fit"]
            assert tail[0].tolist() == fixed["requests_by_opening"]
            value = fit.value(points, matrix)
            cost_by_send = 2. * (np.arange(4) != 0)
            rows = {}
            for price in (0., .05, .2, 1.):
                with patch.object(fit, "value", lambda _, __: value - price * cost_by_send):
                    quiet = fit.exact(points, opening, matrix, independent=True)
                no_requests = fit.measure(quiet, opener, opening, prior, points, matrix)
                mass = np.einsum("rbm,mt,rbtc->tc", opening, fit.heard(D.one_hot(quiet[0])), D.one_hot(quiet[1]))
                calls = float((mass * cost_by_send).sum())
                quiet_net = no_requests["net"] - price * calls
                learned_net = fixed["net"] - price * fixed["expected_author_calls"]
                rows[str(price)] = {"fitted_net": learned_net, "no_request_net": quiet_net,
                                    "fitted_advantage": learned_net - quiet_net,
                                    "no_request_author_calls": calls, "fitted_author_calls": fixed["expected_author_calls"]}
            assert abs(rows["0.0"]["fitted_advantage"] - fixed["gain_over_budget_matched_no_request"]) < 1e-10
            data[label] = rows
        outcome[name] = data
    return outcome


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    archive = study.trained.read(study.study.EVIDENCE / "replay.json")
    saved = study.trained.read(study.study.HERE / "facilitator-measured-channel-evidence/fits.json")
    print(json.dumps(run(archive["scenarios"], saved), indent=2))
