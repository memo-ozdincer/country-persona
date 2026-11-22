"""Select a routing table and desk assignment from previous synthetic inventory counts."""
import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

import routing_prior_robustness as robust

base, route = robust.base, robust.route
PILOT_SIZE = 32
UNIFORM_MASS = 16
TRIALS = 128
SEED = 291406


def cell_returns(policy, matrix):
    ask, send, reply = policy
    with_query = matrix[send[:, None], reply[:, ask].T]
    erased = matrix[send[:, None], reply[:, 0]]
    return (1 - route.TRAIN_LOSS) * with_query + route.TRAIN_LOSS * erased - route.SIGNAL_COST * (ask[:, None] > 0)


def silent_fitted(matrix, actual, estimated, target, tables):
    """Batch the same exact silent search over pilot estimates."""
    left = tables
    values = np.einsum("kla,tlr->tkra", matrix[left], estimated)
    values = np.where(route.SEND[None, None, :, :], values, -np.inf)
    by_sender = values.max(axis=-1).sum(axis=-1)
    chosen = by_sender.argmax(axis=1)
    expected = by_sender[np.arange(len(estimated)), chosen]
    right = values[np.arange(len(estimated)), chosen].argmax(axis=-1)
    net = np.einsum("tlr,lr->t", actual[left[chosen, :, None], right[:, None, :]], target)
    return expected, net


def summarize(values, independence, robust_gain):
    difference = values - independence
    return {"mean": float(values.mean()), "p10": float(np.quantile(values, .1)),
            "wins_vs_independent_oracle": int((difference > 1e-9).sum()),
            "ties_vs_independent_oracle": int((np.abs(difference) <= 1e-9).sum()),
            "mean_gain_over_robust": float(values.mean() - robust_gain)}


def run(path):
    archive = json.loads(path.read_text())
    truth = {k: np.asarray(v) for group in ("prior_anchors", "prior_stress") for k, v in archive[group].items()}
    rng = np.random.default_rng(SEED)
    draws = {k: rng.multinomial(PILOT_SIZE, p.ravel(), size=TRIALS).reshape(TRIALS, 8, 8) for k, p in truth.items()}
    estimated = {k: (counts + UNIFORM_MASS / 64) / (PILOT_SIZE + UNIFORM_MASS) for k, counts in draws.items()}
    tables = np.asarray(list(product(*(np.flatnonzero(row) for row in route.SEND))))
    records = {}
    for name, checksum, intended, observed in base.held_out():
        target_case = archive["historical"][name]
        assert checksum == target_case["source_sha256"]
        matrix = route.receipt_matrix(intended, route.TRAIN_LOSS)
        actual = route.receipt_matrix(observed, route.TRAIN_LOSS)
        policies = {k: base.space.as_policy(p) for k, p in target_case["pool"].items()}
        names = [f"{role}:{k}" for role in ("forward", "swapped") for k in policies]
        planned_by_cell = np.stack([cell_returns(p, matrix) for p in policies.values()])
        actual_by_cell = np.stack([cell_returns(p, actual) for p in policies.values()])
        planned_bank = np.concatenate((planned_by_cell, planned_by_cell.transpose(0, 2, 1)))
        actual_bank = np.concatenate((actual_by_cell, actual_by_cell.transpose(0, 2, 1)))
        rows = {}
        for label, prior in truth.items():
            prior_estimate = estimated[label]
            estimated_portfolio = np.einsum("plr,tlr->tp", planned_bank, prior_estimate)
            actual_portfolio = np.einsum("plr,lr->p", actual_bank, prior)
            chosen = estimated_portfolio.argmax(axis=1)
            learned_results = actual_portfolio[chosen]
            estimated_silent, actual_silent = silent_fitted(matrix, actual, prior_estimate, prior, tables)
            voting = estimated_portfolio[np.arange(TRIALS), chosen] >= estimated_silent - 1e-9
            hybrid = np.where(voting, learned_results, actual_silent)
            previous = target_case["results"][label]
            assert max(actual_silent) <= previous["independent"] + 1e-9
            assert np.isclose(
                              actual_portfolio[0], robust.portfolio.contrasts.measure(
                                  next(iter(policies.values())), observed, prior)["net"])
            observed_robust = previous["robust_mixture"]
            rows[label] = {"independent_oracle": previous["independent"], "robust_fixed": observed_robust,
                           "nominal_fixed": previous["nominal_uniform"],
                           "pilot_learned": summarize(learned_results, previous["independent"], observed_robust),
                           "pilot_independent": summarize(actual_silent, previous["independent"], observed_robust),
                           "pilot_hybrid": summarize(hybrid, previous["independent"], observed_robust),
                           "hybrid_mean_gain_vs_same_pilot_independence": float((hybrid - actual_silent).mean()),
                           "hybrid_portfolio_draws": int(voting.sum()),
                           "chosen_portfolio_arms": {key: int((chosen == i).sum()) for i, key in enumerate(names)
                                                     if (chosen == i).any()}}
        records[name] = rows
    return {"scope": "One simulated 32-episode pilot before choosing a single strategy and orientation for "
                     "future episodes. The pilot supplies previous joint inventory frequency counts. This is added "
                     "information relative to the prior-agnostic controls. Counts are synthetic. Policy selection "
                     "uses the intended rubric. Future net points exclude collecting the pilot.",
            "seed": SEED, "pilot_size": PILOT_SIZE, "uniform_pseudocounts": UNIFORM_MASS, "trials": TRIALS,
            "prior_report_sha256": base.space.runner.digest(path), "results": records}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, default=robust.OUT / "report.json")
    opt = p.parse_args()
    print(json.dumps(run(opt.report), indent=2))
