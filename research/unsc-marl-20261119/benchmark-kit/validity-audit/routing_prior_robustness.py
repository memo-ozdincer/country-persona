"""Select a shared strategy without revealing the evaluation inventory distribution."""
import json
from itertools import combinations
from pathlib import Path

import numpy as np

import routing_learned_portfolio as portfolio

base, route = portfolio.base, portfolio.route
OUT = base.space.OUT / "routing-prior-robustness"
TOL = 1e-9


def stress_priors():
    uniform = route.TEST_PRIORS["uniform"]
    skew = route.TEST_PRIORS["asymmetric"]
    shifted = np.asarray([((i & 1) << 2) | ((i & 4) >> 2) | (i & 2) for i in route.STATES])
    opposites = np.eye(8)[:, ::-1] / 8
    return {"swapped_desks": skew.T.copy(),
            "shifted_fields": skew[np.ix_(shifted, shifted)],
            "more_duplicates": .85 * np.eye(8) / 8 + .15 * uniform,
            "mostly_complementary": .8 * opposites + .2 * uniform}


def maximin(gain):
    """Enumerate simplex vertices for a small, finite, zero-sum selection game."""
    rows, columns = gain.shape
    best = (-np.inf, None)
    for size in range(1, min(rows, columns) + 1):
        for support in combinations(range(columns), size):
            for binding in combinations(range(rows), size):
                selected = gain[np.ix_(binding, support)]
                equations = np.block([[selected, -np.ones((size, 1))],
                                      [np.ones((1, size)), np.zeros((1, 1))]])
                try:
                    solution = np.linalg.solve(equations, np.r_[np.zeros(size), 1.])
                except np.linalg.LinAlgError:
                    continue
                mass = solution[:-1]
                if np.any(mass < -TOL):
                    continue
                weight = np.zeros(columns)
                weight[list(support)] = np.maximum(mass, 0)
                weight /= weight.sum()
                candidate = float((gain @ weight).min())
                if candidate > best[0] + TOL:
                    best = candidate, weight
    assert best[1] is not None
    return best


def planned_pool(frozen, payoff, priors):
    pool = dict(frozen)
    matrix = route.receipt_matrix(payoff, route.TRAIN_LOSS)
    scores = []
    for name, prior in priors.items():
        best = route.best_silent(prior, matrix)
        baseline = portfolio.contrasts.measure(best, payoff, prior)["net"]
        pool[f"independent_{name}"] = best
        scores.append(baseline)
    return pool, np.array(scores)


def at_prior(pool, value, prior):
    return np.array([portfolio.contrasts.measure(p, value, prior)["net"] for p in pool.values()])


def signed_policy(pool, weight):
    return {key: float(prob) for key, prob in zip(pool, weight, strict=True) if prob > TOL}


def case(frozen, planned, actual, anchors, stress):
    pool, planned_independence = planned_pool(frozen, planned, anchors)
    expected = np.array([at_prior(pool, planned, p) for p in anchors.values()])
    gains = expected - planned_independence[:, None]
    lower, mixture = maximin(gains)
    dual, adversarial = maximin(-gains.T)
    assert abs(lower + dual) < TOL
    assert float((adversarial @ gains).max()) <= lower + TOL
    choices = {}
    for name, idx in (("nominal_uniform", int(expected[0].argmax())),
                      ("robust_single", int(gains.min(axis=0).argmax()))):
        choices[name] = np.eye(len(pool))[idx]
    choices["robust_mixture"] = mixture
    results = {}
    pay = route.receipt_matrix(actual, route.TRAIN_LOSS)
    for label, prior in {**anchors, **stress}.items():
        independent = route.best_silent(prior, pay)
        exact, count = route.exact_optional(prior, pay, route.TRAIN_LOSS)
        values = at_prior(pool, actual, prior)
        stats = {k: float(values @ v) for k, v in choices.items()}
        ceiling = portfolio.contrasts.measure(exact, actual, prior)["net"]
        assert max(stats.values()) <= ceiling + TOL
        results[label] = {**stats, "independent": portfolio.contrasts.measure(independent, actual, prior)["net"],
                          "exact_query": ceiling, "request_maps_examined": count}
    return {"prior_anchors": list(anchors), "prior_stress": list(stress), "choices": {
                name: signed_policy(pool, mass) for name, mass in choices.items()},
            "planned_certificate": {"minimax_gain": lower, "dual_upper": -dual,
                                    "dual_prior": dict(zip(anchors, adversarial.tolist(), strict=True)),
                                    "realized_anchor_gains_on_public_rubric": (gains @ mixture).tolist()},
            "pool": {k: [p.tolist() for p in policy] for k, policy in pool.items()},
            "results": results}


def main():
    _, frozen = portfolio.library()
    anchors, stress = route.TEST_PRIORS, stress_priors()
    assert all(np.isclose(p.sum(), 1) and np.all(p >= 0) for p in [*anchors.values(), *stress.values()])
    assert not any(np.allclose(a, s) for a in anchors.values() for s in stress.values())
    contrasts = {k: case(frozen, p, p, anchors, stress) for k, p in portfolio.contrasts.rewards().items()}
    historical = {k: {**case(frozen, intended, actual, anchors, stress), "source_sha256": source}
                  for k, source, intended, actual in base.held_out()}
    report = {"scope": "Select a shared mixture once per public rubric using three candidate inventory priors. "
                       "Neither the realized prior nor inventory is used to choose policy at deployment. "
                       "The public random draw precedes both private inventories. The certificate concerns the "
                       "stated rubric and prior hull. Actual historical receipts enter only at scoring.",
              "selector_code_sha256": base.space.runner.digest(Path(__file__)),
              "prior_anchors": {k: p.tolist() for k, p in anchors.items()},
              "prior_stress": {k: p.tolist() for k, p in stress.items()},
              "contrast": contrasts, "historical": historical}
    OUT.mkdir()
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
