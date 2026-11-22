"""Compare the learned mixture with a scripted requester tuned on the announced rubric."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_ftf_writer_effects as effects

writer, original, base, route = effects.writer, effects.original, effects.base, effects.route
limit, digest = original.limit, original.digest


def select():
    priors, _, silent = effects.frozen_policies()
    planned = original.public_payoff()
    table = route.receipt_matrix(planned, route.TRAIN_LOSS)
    informed = np.array([
        route.evaluate(route.best_silent(p, table), p, planned, route.TRAIN_LOSS)["net"]
        for p in priors.values()
    ])
    pool = {}
    for order in base.ORDERS:
        policy = base.remap_policy(route.scripted(), order)
        label = "".join(map(str, order))
        for swap in (False, True):
            pool[f"query:{label}:{'reverse' if swap else 'forward'}"] = (policy, swap)
    for i, (policy, _, _) in enumerate(silent):
        pool[f"independent:{i}"] = (policy, False)
    returns = []
    for policy, swap in pool.values():
        cells = limit.pilot.cell_returns(policy, table)
        returns.append([float((cells * (p.T if swap else p)).sum()) for p in priors.values()])
    gains = np.asarray(returns).T - informed[:, None]
    _, weights = limit.game_search(gains)
    return pool, weights, gains @ weights


def evaluate(path):
    candidates, weights, planned = select()
    scores = original.read(path)
    priors, learned, _ = effects.frozen_policies()
    points = np.array(scores["eligible_vector"])
    assert scores["raw_vector"] == scores["eligible_vector"]
    outcomes = {}
    for name, prior in priors.items():
        scripted = sum(mass * route.evaluate(policy, prior.T if swap else prior, points, route.TRAIN_LOSS)["net"]
                       for (policy, swap), mass in zip(candidates.values(), weights, strict=True))
        observed = scores["results"]["release"][name]["team"]
        replay = sum(mass * route.evaluate(policy, prior.T if swap else prior, points, route.TRAIN_LOSS)["net"]
                     for policy, swap, mass in learned)
        assert abs(observed - replay) < 1e-8
        outcomes[name] = {"scripted": scripted, "learned": replay, "margin": replay - scripted}
    return {
        "scope": "Post-run comparator ablation. Its weights use only the announced (pre-generation) rubric. "
                 "Same routing rules and message fees, but choose among twelve oriented and field-permuted "
                 "hand-scripted requesters plus the pre-existing independent controls. Use the same writer bank.",
        "score_sha256": digest(path), "announced_worst_gap": float(planned.min()),
        "scripted_mixture": dict(zip(candidates, weights.tolist(), strict=True)),
        "outcomes": outcomes,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scores", type=Path)
    args = cli.parse_args()
    print(json.dumps(evaluate(args.scores), indent=2))
