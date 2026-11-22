"""Regress response action values conditional on the exact development chair."""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

import facilitator_silence_joint_fit as study

budget, joint, fit, D, R = study.budget, study.joint, study.fit, study.D, study.R
EVIDENCE = study.EVIDENCE


def train(original):
    sets, _, _ = budget.development()
    xs, ys, ws = [], [], []
    cache = {}
    legal = D.FINAL_LEGAL[..., 1:]
    for public, target in sets["budget_fit"].values():
        for law in fit.live.PRIORS:
            key = (tuple(public), tuple(target), law)
            if key not in cache:
                prior = R.TEST_PRIORS[law]
                mass = joint.opening(*study.opening(public, prior, original), prior)
                question, response = fit.exact(target, mass, fit.PERFECT)
                heard = fit.heard(D.one_hot(question))
                visits = np.einsum("rbm,mt->rbt", mass, heard)
                value = np.einsum("rbm,mt,mtc->rbtc", mass, heard, fit.value(target, fit.PERFECT))
                feature = fit.features(public, mass, fit.PERFECT)[1]
                delta = (value[..., 1:] - value[..., :1]) / np.maximum(visits[..., None], 1e-12)
                shifted = feature[..., 1:, :] - feature[..., :1, :]
                include = (visits[..., None] > 1e-12) & legal
                weights = np.broadcast_to(visits[..., None] / np.maximum(legal.sum(-1, keepdims=True), 1), include.shape)
                cache[key] = shifted[include], delta[include], weights[include]
                optimal = np.where(D.FINAL_LEGAL, value, -np.inf).max(-1)
                chosen = np.take_along_axis(value, response[..., None], -1)[..., 0]
                assert np.allclose(optimal, chosen, rtol=0, atol=1e-10)
            x, y, weight = cache[key]
            xs.append(x)
            ys.append(y)
            ws.append(weight)
    x, y, w = map(np.concatenate, (xs, ys, ws))
    s = np.sqrt(w)
    coefficients, _, rank, _ = np.linalg.lstsq(x * s[:, None], y * s, rcond=None)
    return {"request": None, "reserve": 0., "response": coefficients.tolist(),
            "rank": int(rank), "examples": len(y), "distinct_feature_target_laws": len(cache),
            "weighted_rmse": float(np.sqrt(np.average((x @ coefficients - y) ** 2, weights=w)))}


def run():
    base = budget.read(study.OLD)
    archived = base["training"]["budget_fit"]
    original = budget.read(EVIDENCE / "results.json")
    model = train(archived)
    fits = {"regression": model, "response_aware": original["fit"]["response_aware"]}
    result = study.evaluate_held(base, archived, fits)
    result["2466"] = study.evaluate_2466(archived, fits)
    for case, caps in result.items():
        for cap, priors in caps.items():
            for label, row in priors.items():
                for arm in ("response_aware", "declared_exact_joint", "hindsight_exact_joint"):
                    assert row[arm] == original["cases"][case][cap][label][arm]
    files = (Path(__file__).resolve(), EVIDENCE / "results.json", EVIDENCE / "responder-regression-protocol.md")
    return {"fit": model, "cases": result,
            "sha256": {str(p.relative_to(study.HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
