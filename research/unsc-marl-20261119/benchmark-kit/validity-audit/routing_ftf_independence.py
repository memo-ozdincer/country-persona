"""Freeze and score an independent-delivery control for the written-ballot case."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_ftf_record as record

route, base, limit = record.route, record.base, record.limit


def inputs():
    priors, _, _ = record.selections()
    return priors, record.public_payoff()


def plan():
    priors, payoff = inputs()
    table = route.receipt_matrix(payoff, route.TRAIN_LOSS)
    mixture = np.mean(list(priors.values()), axis=0)
    tables = {name: route.best_silent(p, table) for name, p in {**priors, "average": mixture}.items()}
    values = np.array([[route.evaluate(policy, prior, payoff, route.TRAIN_LOSS)["net"]
                        for policy in tables.values()] for prior in priors.values()])
    informed = values[np.arange(len(priors)), np.arange(len(priors))]
    _, mixture = limit.game_search(values - informed[:, None])
    return {
        "locked": {**record.locks(), "control_script": record.digest(Path(__file__))},
        "tables": {name: [row.tolist() for row in policy] for name, policy in tables.items()},
        "mixture": dict(zip(tables, mixture.tolist(), strict=True)),
    }


def score(path, control):
    observed = record.read(path)
    selected = record.read(control)
    assert selected["locked"] == {**record.locks(), "control_script": record.digest(Path(__file__))}
    weights = selected["mixture"]
    assert np.isclose(sum(weights.values()), 1) and min(weights.values()) >= 0
    policies = {name: base.space.as_policy(table) for name, table in selected["tables"].items()}
    priors, _ = inputs()
    result = {}
    for tag, vector in (("raw", "raw_vector"), ("release", "eligible_vector")):
        payoff = np.asarray(observed[vector])
        result[tag] = {}
        for name, prior in priors.items():
            net = sum(weights[key] * route.evaluate(p, prior, payoff, route.TRAIN_LOSS)["net"]
                      for key, p in policies.items())
            comparison = observed["results"][tag][name]
            assert net <= comparison["optimized_independent"] + 1e-8
            result[tag][name] = {"independent": net, "team": comparison["team"],
                                 "team_minus_independent": comparison["team"] - net}
    return {"control_sha256": record.digest(control), "observed_sha256": record.digest(path), "outcomes": result}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("plan", "score"))
    cli.add_argument("--observed", type=Path)
    cli.add_argument("--control", type=Path)
    args = cli.parse_args()
    print(json.dumps(plan() if args.mode == "plan" else score(args.observed, args.control), indent=2))
