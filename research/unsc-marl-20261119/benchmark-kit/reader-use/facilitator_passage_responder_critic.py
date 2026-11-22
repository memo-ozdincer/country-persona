"""Fit a responder-aware request critic while keeping communication costs exact."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import facilitator_passage_advantage_fit as old

joint, fit, D, R = old.joint, old.fit, old.D, old.R
EVIDENCE = joint.HERE / "facilitator-passage-responder-critic-evidence"
DECLARED = np.ones(2)


def receipt_features(points, opening, replies, admission):
    joint_sends = np.einsum("rbm,rbtc->mtc", opening, D.one_hot(replies))
    admitted = joint_sends * admission
    sent = (1 - D.LOSS) * joint_sends + D.LOSS * joint_sends[:, :1]
    successful = (1 - D.LOSS) * admitted + D.LOSS * admitted[:, :1]
    failed = (sent - successful).sum(-1)
    ending = np.einsum("mtc,mcn->mtn", successful, D.LAST) + failed[..., None] * np.eye(8)[:, None, :]
    visit = opening.sum((0, 1))
    assert np.allclose(ending.sum(-1), visit[:, None], rtol=0, atol=1e-12)
    scale = np.where(visit > 1e-12, visit, 1.)
    delta = (ending - ending[:, :1]) / scale[:, None, None]
    x = np.stack((delta @ points, delta @ ((points == 70) * D.COMPLETE_BONUS)), axis=-1)
    send_cost = ((sent - sent[:, :1]) @ D.SEND_COST) / scale[:, None]
    costs = (send_cost + D.QUERY_COST) * (visit[:, None] > 1e-12)
    reference, _ = old.advantages(points, opening, replies, admission)
    assert np.allclose(x.sum(-1) - costs, reference, rtol=0, atol=1e-11)
    return x, costs, visit


def train(development, model):
    rows = []
    for public, target in development.values():
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            _, mass, _, (_, replies) = old.context(public, prior, model)
            x, costs, visit = receipt_features(public, mass, replies, fit.PERFECT)
            reference, _ = old.advantages(target, mass, replies, fit.PERFECT)
            valid = old.QUESTIONS & (visit[:, None] > 1e-12)
            weight = visit / np.maximum(1, old.QUESTIONS.sum(-1))
            rows.append((x[valid] / 10, (reference + costs)[valid] / 10,
                         np.broadcast_to(weight[:, None], valid.shape)[valid]))
    x, y, weight = (np.concatenate(col, axis=0) for col in zip(*rows, strict=True))
    w = np.sqrt(weight)
    coefficients = np.linalg.lstsq(np.vstack((x * w[:, None], np.eye(2))),
                                    np.r_[y * w, DECLARED], rcond=None)[0]
    rmse = {name: float(np.sqrt(np.average((10 * (x @ theta - y)) ** 2, weights=weight)))
            for name, theta in (("declared", DECLARED), ("fitted", coefficients))}
    return coefficients, {"examples": len(y), "weighted_rmse": rmse}


def evaluate(public, target, measured, prior, model, opening, coefficients, previous):
    opening, mass, simple, (frozen, replies) = old.context(public, prior, model, opening)
    x, costs, visit = receipt_features(public, mass, replies, fit.PERFECT)
    critic = x @ coefficients - costs
    declared = x.sum(-1) - costs
    observed, _ = old.advantages(target, mass, replies, measured)
    baseline = joint.metric((*opening, np.zeros(8, dtype=int), replies), prior, target, measured)
    policies = {"frozen": frozen, "previous_fit": old.best_question(simple @ previous),
                "declared": old.best_question(declared), "responder_critic": old.best_question(critic),
                "hindsight": old.best_question(observed)}
    answers = {}
    for name, chair in policies.items():
        result = joint.metric((*opening, chair, replies), prior, target, measured)
        value = result["net"] - baseline["net"]
        assert abs(value - visit @ observed[np.arange(8), chair]) < 1e-10
        answers[name] = {"net": result["net"], "gain_over_fixed_team_silence": value,
                         "requests": result["expected_requests"], "questions": chair.tolist(),
                         "guarded_points": result["guarded_points"], "strict_complete": result["strict_complete"]}
    assert all(arm["net"] <= answers["hindsight"]["net"] + 1e-10 for arm in answers.values())
    return {"receipt_visits": visit.tolist(), "critic_values": critic.tolist(),
            "declared_values": declared.tolist(), "measured_values": observed.tolist(), "policies": answers}


def run():
    model_file = old.adaptive.EVIDENCE / "results.json"
    previous_file = old.EVIDENCE / "results.json"
    model = joint.historic.read(model_file)
    weights = np.asarray(joint.historic.read(previous_file)["coefficients"])
    development, archived = fit.OLD.base.cases()
    passage = joint.held()
    assert not {tuple(x[0]) for x in development.values()} & {tuple(x[0]) for x in passage.values()}
    theta, summary = train(development, model["fit"])
    matrix_cases = {}
    for case, (points, channel) in passage.items():
        matrix_cases[case] = {}
        for name, arms in model["cases"][case].items():
            prior = R.TEST_PRIORS[name]
            matrix_cases[case][name] = {
                opening_name: evaluate(points, points, channel, prior, model["fit"],
                                       tuple(np.asarray(p) for p in arms[arm]["team"][:2]), theta, weights)
                for opening_name, arm in (("fitted_opening", "adaptive"), ("planner_opening", "declared_block_planner"))
            }
    bank_cases = {
        case: {name: evaluate(public, target, fit.PERFECT, R.TEST_PRIORS[name], model["fit"], None, theta, weights)
               for name in fit.live.PRIORS}
        for case, (public, target) in archived.items()
    }
    unique = {tuple(map(tuple, pair)) for pair in archived.values()}
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", model_file, previous_file)
    return {"weights": theta.tolist(), "fitting": summary, "passage_cases": matrix_cases,
            "score_bank_cases": bank_cases, "unique_score_bank_pairs": len(unique),
            "sha256": {str(p.relative_to(joint.HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
