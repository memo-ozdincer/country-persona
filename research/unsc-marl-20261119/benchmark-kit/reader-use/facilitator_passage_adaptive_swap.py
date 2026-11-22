"""Evaluate fitted follow-up with an explicit opening-policy intervention."""
import json

import numpy as np

import facilitator_passage_adaptive_fit as adaptive


def run():
    joint, fit, R = adaptive.joint, adaptive.fit, adaptive.R
    read = joint.historic.read
    archive = read(adaptive.EVIDENCE / "results.json")
    static_weights = read(joint.EVIDENCE / "weak-start.json")["fit"]["weights"][2:]
    adaptive_weights = archive["fit"]["weights"][2:]
    result = {}
    for docket, (points, channel) in joint.held().items():
        result[docket] = {}
        for label, controls in archive["cases"][docket].items():
            prior = R.TEST_PRIORS[label]
            opening = tuple(np.asarray(role) for role in controls["declared_block_planner"]["team"][:2])
            reference, stale_mass = fit.context(points, prior)
            actual_mass = joint.opening(*opening, prior)
            quiet = controls["hindsight_no_request"]["net"]
            row = {
                "changed_opening_actions": sum(int(np.count_nonzero(x != y))
                                               for x, y in zip(opening, reference, strict=True)),
                "planner_net_over_no_request": controls["declared_block_planner"]["net"] - quiet,
            }
            for name, weights in (("static_fit", static_weights), ("adaptive_fit", adaptive_weights)):
                row[name] = {}
                for context, mass in (("stale", stale_mass), ("refreshed", actual_mass)):
                    tail = fit.action_policy(weights, points, mass, fit.PERFECT)
                    score = joint.metric((*opening, *tail), prior, points, channel)
                    row[name][context] = {
                        "net_over_no_request": score["net"] - quiet,
                        "expected_requests": score["expected_requests"],
                        "followup": [v.tolist() for v in tail],
                    }
            result[docket][label] = row
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
