"""Compute the value of asking under each frozen responder."""
import json

import numpy as np

import facilitator_passage_adaptive_fit as adaptive


def request_values(points, opening_mass, replies, channel):
    fit, D = adaptive.fit, adaptive.D
    reply_distribution = D.one_hot(replies)
    actual_value = fit.value(points, channel)
    delivered = np.einsum("rbm,rbtc,mtc->mt", opening_mass, reply_distribution, actual_value)
    dropped = delivered[:, :1]
    joint = (1 - D.LOSS) * delivered + D.LOSS * dropped
    mass = opening_mass.sum((0, 1))
    return joint - mass[:, None] * D.QUERY_COST, mass


def run():
    joint, fit, D, R = adaptive.joint, adaptive.fit, adaptive.D, adaptive.R
    archive = joint.historic.read(adaptive.EVIDENCE / "results.json")
    output = {}
    for docket, (points, observed) in joint.held().items():
        output[docket] = {}
        for label, arms in archive["cases"][docket].items():
            prior = R.TEST_PRIORS[label]
            baseline = arms["hindsight_no_request"]["net"]
            planner = arms["declared_block_planner"]
            fitted = arms["adaptive"]
            tail_weights = archive["fit"]["weights"][2:]
            output[docket][label] = {}
            for name, record in (("fitted_opening", fitted), ("planned_opening", planner)):
                opening = tuple(np.asarray(p) for p in record["team"][:2])
                mass = joint.opening(*opening, prior)
                current_q, replies = fit.action_policy(tail_weights, points, mass, fit.PERFECT)
                policies = {}
                candidates = {"fitted": current_q, "silent": np.zeros(8, dtype=int)}
                for mode, channel in (("declared", fit.PERFECT), ("hindsight", observed)):
                    payoffs, visit = request_values(points, mass, replies, channel)
                    valid = visit > 1e-12
                    gains = np.divide(payoffs - payoffs[:, :1], visit[:, None],
                                      out=np.zeros_like(payoffs), where=valid[:, None])
                    beneficial_questions = D.CHAIR_LEGAL & (gains > 1e-10)
                    beneficial_questions[:, 0] = True
                    best = np.where(beneficial_questions, gains, -np.inf).argmax(-1)
                    assert np.all(best[~valid] == 0)
                    candidates[mode] = best
                    policies[mode] = {"conditional_gain": gains.tolist(), "receipt_probability": visit.tolist()}
                for mode, question in candidates.items():
                    metrics = joint.metric((*opening, question, replies), prior, points, observed)
                    policies.setdefault(mode, {}).update({"questions": question.tolist(), **metrics,
                                                         "gain_over_hindsight_no_request": metrics["net"] - baseline})
                assert policies["hindsight"]["net"] >= policies["fitted"]["net"] - 1e-10
                assert policies["hindsight"]["net"] >= policies["declared"]["net"] - 1e-10
                output[docket][label][name] = policies
    return output


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
