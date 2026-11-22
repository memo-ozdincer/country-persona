"""Certify prior-blind policy mixtures for the Gaza routing diagnostic."""
import json
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

import routing

TRAIN = ("uniform", "correlated_development", "correlated_diagnostic_2", "correlated_diagnostic_3")


def menus():
    choices = np.asarray(list(product((0, 1), repeat=12))).reshape(-1, 2, 6)
    flexible = routing.PAIR[np.arange(len(routing.PAIR)), choices]
    rank = np.asarray(list(product(routing.PRIORITIES, repeat=2)))
    return {"flexible": flexible, "rank": rank}


def values(prior, receivers):
    q_loss, r_loss, q_cost, r_cost = routing.config()
    mass = routing.masses(prior, q_loss)
    costs = q_cost * (routing.REQUESTS @ prior.sum(axis=1)) + r_cost
    success = np.einsum("eqri,tqri->et", mass, np.eye(4)[receivers])
    return 42 + (1 - r_loss) * 28 * success - costs[:, None]


def mixture(train_values, informed):
    values = train_values - informed[:, None]
    n = values.shape[1]
    inequalities = np.c_[-values, np.ones(len(values))]
    equality = np.r_[np.ones(n), 0.0][None, :]
    result = linprog(np.r_[np.zeros(n), -1.0], A_ub=inequalities, b_ub=np.zeros(len(values)),
                     A_eq=equality, b_eq=[1.0], bounds=[(0, None)] * n + [(None, None)], method="highs")
    assert result.success, result.message
    weights = result.x[:-1]
    dual = -result.ineqlin.marginals
    assert np.all(weights >= 0) and np.all(dual >= 0)
    assert np.isclose(weights.sum(), 1.) and np.isclose(dual.sum(), 1.)
    lower, upper = min(values @ weights), max(dual @ values)
    assert abs(lower - upper) < 1e-8
    return weights, dual, lower, upper


def report():
    path = routing.HERE / "routing-results.json"
    reference = json.loads(path.read_text())["results"]
    priors = dict(routing.priors())
    informed = [reference[name]["policies"]["exact_interactive"]["net"] for name in TRAIN]
    outcomes = {}
    for menu, receivers in menus().items():
        prior_values = {name: values(p, receivers).ravel() for name, p in priors.items()}
        kind = {"rank": "independent_priority_by_request", "flexible": "exact_interactive"}[menu]
        for name, policy_values in prior_values.items():
            assert np.isclose(max(policy_values), reference[name]["policies"][kind]["net"])
        weights, dual, lower, upper = mixture(np.stack([prior_values[name] for name in TRAIN]), np.asarray(informed))
        support = []
        for index in np.flatnonzero(weights > 1e-10):
            sender, receiver = divmod(index, len(receivers))
            support.append({"weight": float(weights[index]), "sender": routing.REQUESTS[sender].tolist(),
                            "receiver": receivers[receiver].T.tolist()})
        score = {name: sum(entry["weight"] * routing.measure(p, np.asarray(entry["sender"]),
                                                             np.asarray(entry["receiver"]))["net"]
                           for entry in support) for name, p in priors.items()}
        assert all(np.isclose(score[name], weights @ prior_values[name]) for name in priors)
        outcomes[menu] = {"candidates": len(weights), "certified_training_margin_lower": float(lower),
                          "certified_training_margin_upper": float(upper), "dual_training_priors": dual.tolist(),
                          "mixture": support, "all_prior_scores": score}
    return {"scope": "Use a public random draw over decentralized policy pairs before either desk sees a card. "
                     "Fit both menus against the same four development priors with maximin regret to informed interaction. "
                     "The six unselected availability priors do not enter either fit. Their underlying historical docket is shared.",
            "code_sha256": routing.digest(Path(__file__)), "reference_sha256": routing.digest(path),
            "training_priors": TRAIN, "diagnostic_priors": [name for name in priors if name not in TRAIN],
            "outcomes": outcomes}


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
