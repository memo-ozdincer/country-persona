"""Calibrate documentary rewards from reviewed singleton records."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_conservative_frequency as study

base, R, D = study.base, study.R, study.D
OBSERVED = (0, 1, 2, 4)


def correct_singletons(public, assessed):
    # Preserve all publicly declared interactions, including any conjunction
    # that no singleton review can see.
    delta = assessed - public
    upgrades = np.array([delta[1 << i] - delta[0] for i in range(3)])
    bits = ((np.arange(8)[:, None] & R.BITS[1:]) != 0)
    declared = np.clip(public + delta[0] + bits @ upgrades, 0, 70)
    assert np.array_equal(declared[list(OBSERVED)], assessed[list(OBSERVED)])
    return declared


def shifted_pair(public):
    additive = public[0] + ((np.arange(8)[:, None] & R.BITS[1:]) != 0) @ (public[[1, 2, 4]] - public[0])
    residual = public - additive
    pairs = (3, 5, 6)
    extras = residual[list(pairs)]
    if not (extras > 0).any():
        return None
    rotated = np.roll(extras, 1)
    alternate = additive.copy()
    alternate[list(pairs)] += rotated
    alternate[7] = public[7]
    assert np.array_equal(alternate[list(OBSERVED)], public[list(OBSERVED)])
    return alternate


def evaluate(public, outcome, prior, left, right):
    opening = base.opening(D.one_hot(left), D.one_hot(right), prior).sum(1)
    reference = study.nominal_model(prior)
    cost = float(prior.sum(1) @ D.SEND_COST[left] + prior.sum(0) @ D.SEND_COST[right])
    result = {}
    for name, points in (("declared", public), ("singleton_review", correct_singletons(public, outcome)),
                         ("full_review", outcome)):
        quiet = study.fallback(reference, points)
        policy = study.best_for(reference.sum(1), study.returns(points, quiet)[-1])
        value = study.score(opening, study.returns(outcome, quiet), policy, cost)[0]
        result[name] = {"planner_points": points.tolist(), **value}
    return result


def run():
    out = {}
    prior_styles = {"same_priority": (base.PRIORITIES[0], base.PRIORITIES[0]),
                    "opposite_priority": (base.PRIORITIES[0], base.PRIORITIES[-1])}
    for key, (public, actual) in base.banks().items():
        out[key] = {}
        foil = shifted_pair(public)
        for name, outcome in (("archived", actual), ("shifted_bonus_control", foil)):
            if outcome is None:
                continue
            variants = {}
            for label in base.fit.live.PRIORS:
                p = R.TEST_PRIORS[label]
                for style, (left, right) in prior_styles.items():
                    variants[f"{label}/{style}"] = evaluate(public, outcome, p, left, right)
            out[key][name] = variants
    files = (Path(__file__), Path(study.__file__), Path(base.__file__), base.EVIDENCE / "calibration-protocol.md")
    return {"observed_review_masks": OBSERVED, "dockets": out,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
