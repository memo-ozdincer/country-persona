"""Refit the shared-reward sender critic to a change in native writer behavior."""

import argparse
import json

import numpy as np

from experiment import HERE, PRIOR, previous

import routing

sender = routing.sender


def plan():
    files = (HERE / "fit.py", HERE / "fit-protocol.md", HERE / "plan.json",
             PRIOR / "routing.py", routing.SENDER / "plan.json", routing.SENDER / "results.json")
    return {str(path.relative_to(previous.RUNS)): sender.digest(path) for path in files}


def run():
    assert plan() == previous.base.read(HERE / "fit-plan.json")
    assert sender.plan() == previous.base.read(routing.SENDER / "plan.json")
    grades = previous.base.read(HERE / "scores.json")["outcomes"]
    original = previous.base.read(routing.SENDER / "results.json")
    transfer = previous.base.read(HERE / "routing.json")
    nothing, algeria, sponsors = [grades[name]["standalone"] for name in ("none", "algeria", "sponsors")]
    standalone = np.array([sponsors - nothing, algeria - nothing])
    values = np.array([[nothing, algeria, sponsors, grades[name]["known_pair"]]
                       for name in ("sponsors-first", "algeria-first")])
    log = sender.exploration(values)
    assert [r | {"reward": 0} for r in log] == [r | {"reward": 0} for r in original["exploration"]]
    critics = ("additive", "order_pooled", "order_aware")
    params = {name: sender.fit_team(log, name)[0] for name in critics}
    estimates = {name: sender.predict(params[name], name) for name in critics}
    outcomes = []
    for source_run in transfer["held"]:
        p, mix = (source_run[k] for k in ("delivery", "algeria_first"))
        truth = sender.evaluate_actions(values, standalone, p, mix)
        oracle = sender.choose(truth)
        assert source_run["oracle_send"] == sender.ACTION_NAMES[oracle]
        controls = {"always_withhold": 0, "always_send": 3, "oracle": oracle,
                    "frozen_2664": sender.ACTION_NAMES.index(source_run["transfer_send"])}
        actions = {name: sender.choose(sender.evaluate_actions(table, standalone, p, mix))
                   for name, table in estimates.items()}
        outcomes.append({
            "delivery": p, "algeria_first": mix,
            "policies": {name: truth[index] | {"action": sender.ACTION_NAMES[index]}
                         for name, index in (controls | actions).items()},
        })
    names = outcomes[0]["policies"].keys()
    return {
        "scores_sha256": sender.digest(HERE / "scores.json"),
        "exploration": log, "coefficients": params,
        "mean": {name: {
            **{key: round(float(np.mean([row["policies"][name][key] for row in outcomes])), 8)
               for key in ("release", "cost", "utility")},
            "oracle_matches": sum(row["policies"][name]["action"] == row["policies"]["oracle"]["action"]
                                  for row in outcomes),
        } for name in names},
        "held": outcomes,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan() if args.plan else run(), indent=2))
