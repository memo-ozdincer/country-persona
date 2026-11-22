"""Separate learned-library capacity from the exact unknown-prior limit."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_prior_robustness as evaluation

base, route = evaluation.base, evaluation.route
MAX_COLUMNS = 16
TOL = 1e-8


def certificate(initial, reward, priors):
    pool = dict(initial)
    matrix = route.receipt_matrix(reward, route.TRAIN_LOSS)
    baseline = np.array([evaluation.portfolio.contrasts.measure(route.best_silent(p, matrix), reward, p)["net"]
                         for p in priors.values()])
    trace = []
    for i in range(MAX_COLUMNS):
        scores = np.array([evaluation.at_prior(pool, reward, p) for p in priors.values()])
        gains = scores - baseline[:, None]
        lower, policy_weights = evaluation.maximin(gains)
        dual, prior_weights = evaluation.maximin(-gains.T)
        assert abs(lower + dual) <= TOL
        prior = np.einsum("i,ijk->jk", prior_weights, np.stack(list(priors.values())))
        candidate, maps = route.exact_optional(prior, matrix, route.TRAIN_LOSS)
        net = evaluation.portfolio.contrasts.measure(candidate, reward, prior)["net"]
        upper = net - baseline @ prior_weights
        assert upper + TOL >= lower
        trace.append({"lower": lower, "upper": float(upper), "exact_maps": maps,
                      "dual_prior": dict(zip(priors, prior_weights.tolist(), strict=True))})
        if upper - lower <= TOL or i == MAX_COLUMNS - 1:
            break
        assert not any(all(np.array_equal(a, b) for a, b in zip(candidate, p, strict=True))
                       for p in pool.values())
        pool[f"oracle_{i}"] = candidate
    return pool, policy_weights, trace


def run(path):
    bank = json.loads(path.read_text())
    priors = {k: np.asarray(p) for k, p in bank["prior_anchors"].items()}
    stress = {k: np.asarray(p) for k, p in bank["prior_stress"].items()}
    records = {}
    for name, checksum, planned, observed in base.held_out():
        row = bank["historical"][name]
        assert row["source_sha256"] == checksum
        original = {k: base.space.as_policy(p) for k, p in row["pool"].items()}
        pool, weights, trace = certificate(original, planned, priors)
        for p in (list(pool.values())):
            assert len(p) == 3
        values = {k: float(evaluation.at_prior(pool, observed, prior) @ weights)
                  for k, prior in {**priors, **stress}.items()}
        assert all(value <= row["results"][k]["exact_query"] + TOL for k, value in values.items())
        records[name] = {"library_lower": row["planned_certificate"]["minimax_gain"],
                         "certified_ceiling": trace[-1]["upper"] - trace[-1]["lower"] <= TOL,
                         "trace": trace, "oracle_mixture": evaluation.signed_policy(pool, weights),
                         "added_policies": {k: [part.tolist() for part in p] for k, p in pool.items() if k not in original},
                         "actual_net": values}
    return {"scope": "Column-generation certificate for all feasible two-desk policies on the public rubric "
                     "and the fixed anchor distributions. Added tables use the exact optional-query oracle. "
                     "Historical realized scores are used only for replay.",
            "input_sha256": base.space.runner.digest(path), "historical": records}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--report", type=Path, default=evaluation.OUT / "report.json")
    opt = cli.parse_args()
    print(json.dumps(run(opt.report), indent=2))
