"""Learn signed request advantages with fixed teammates and a public rubric."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import facilitator_passage_adaptive_request as counterfactual

adaptive = counterfactual.adaptive
joint, fit, D, R = adaptive.joint, adaptive.fit, adaptive.D, adaptive.R
EVIDENCE = joint.HERE / "facilitator-passage-advantage-fit-evidence"
QUESTIONS = D.CHAIR_LEGAL.copy()
QUESTIONS[:, 0] = False


def context(points, prior, team, opening=None):
    if opening is None:
        opening = joint.policies(points, prior, team)[0][:2]
    mass = joint.opening(*opening, prior)
    chair_features = fit.features(points, mass, fit.PERFECT)[0]
    tail = fit.action_policy(team["weights"][2:], points, mass, fit.PERFECT)
    return opening, mass, chair_features - chair_features[:, :1], tail


def advantages(points, mass, replies, channel):
    scores, visit = counterfactual.request_values(points, mass, replies, channel)
    return np.divide(scores - scores[:, :1], visit[:, None], out=np.zeros_like(scores),
                     where=visit[:, None] > 1e-12), visit


def best_question(value):
    allowed = QUESTIONS & (value > 1e-10)
    allowed[:, 0] = True
    return np.where(allowed, value, -np.inf).argmax(-1)


def fit_values(development, team):
    feature_rows, labels, sample_weights = [], [], []
    question_count = QUESTIONS.sum(-1)
    for public, target in development.values():
        for label in fit.live.PRIORS:
            _, mass, features, (_, replies) = context(public, R.TEST_PRIORS[label], team)
            gains, visits = advantages(target, mass, replies, fit.PERFECT)
            reachable = QUESTIONS & (visits[:, None] > 1e-12)
            weight = np.divide(visits, question_count, out=np.zeros_like(visits), where=question_count > 0)
            feature_rows.extend(features[reachable])
            labels.extend(gains[reachable])
            sample_weights.extend(np.broadcast_to(weight[:, None], reachable.shape)[reachable])
    x, y, sample_weights = map(np.asarray, (feature_rows, labels, sample_weights))
    scale = np.sqrt(sample_weights)
    coefficients, _, rank, singular = np.linalg.lstsq(x * scale[:, None], y * scale, rcond=None)
    predictions = x @ coefficients
    return coefficients, {"rows": len(y), "rank": int(rank), "singular_values": singular.tolist(),
                          "weighted_rmse": float(np.sqrt(np.average((predictions - y) ** 2, weights=sample_weights))),
                          "weighted_sign_accuracy": float(np.average((predictions > 1e-10) == (y > 1e-10),
                                                                     weights=sample_weights))}


def evaluate(points, channel, prior, team, opening, coefficients, quiet):
    opening, mass, features, (initial, replies) = context(points, prior, team, opening)
    declared, visit = advantages(points, mass, replies, fit.PERFECT)
    observed, _ = advantages(points, mass, replies, channel)
    predictions = features @ coefficients
    predictions[visit <= 1e-12] = 0
    policies = {"frozen_chair": initial, "regressed_advantage": best_question(predictions),
                "declared_counterfactual": best_question(declared),
                "measured_counterfactual": best_question(observed), "fixed_team_silence": np.zeros(8, dtype=int)}
    row = {}
    for name, chair in policies.items():
        scores = joint.metric((*opening, chair, replies), prior, points, channel)
        expected = float(visit @ observed[np.arange(8), chair])
        row[name] = {"questions": chair.tolist(), "expected_requests": scores["expected_requests"],
                     "net": scores["net"], "advantage_over_hindsight_no_request": scores["net"] - quiet,
                     "advantage_over_fixed_team_silence": expected,
                     "declared_request_value": float(visit @ declared[np.arange(8), chair])}
    for arm in row.values():
        assert abs(arm["net"] - row["fixed_team_silence"]["net"] - arm["advantage_over_fixed_team_silence"]) < 1e-10
        assert row["measured_counterfactual"]["net"] >= arm["net"] - 1e-10
        assert row["declared_counterfactual"]["declared_request_value"] >= arm["declared_request_value"] - 1e-10
    return {"policies": row, "receipt_mass": visit.tolist(), "estimated_advantages": predictions.tolist(),
            "declared_advantages": declared.tolist(), "measured_advantages": observed.tolist()}


def run():
    archive_path = adaptive.EVIDENCE / "results.json"
    archive = joint.historic.read(archive_path)
    development = fit.OLD.base.cases()[0]
    held_cases = joint.held()
    assert set(development).isdisjoint(held_cases)
    assert not {tuple(x[0]) for x in development.values()} & {tuple(x[0]) for x in held_cases.values()}
    coefficients, statistics = fit_values(development, archive["fit"])
    cases = {}
    for docket, (points, channel) in held_cases.items():
        cases[docket] = {}
        for law, row in archive["cases"][docket].items():
            prior = R.TEST_PRIORS[law]
            quiet = row["hindsight_no_request"]["net"]
            cases[docket][law] = {
                name: evaluate(points, channel, prior, archive["fit"],
                               tuple(np.asarray(x) for x in row[arm]["team"][:2]), coefficients, quiet)
                for name, arm in (("fitted_opening", "adaptive"), ("planner_opening", "declared_block_planner"))
            }
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", archive_path,
             Path(counterfactual.__file__).resolve())
    return {"coefficients": coefficients.tolist(), "development": list(development), "fit": statistics,
            "cases": cases, "sha256": {str(p.relative_to(joint.HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
