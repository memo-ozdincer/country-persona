"""Decompose the writer intervention on matched routing and delivery costs."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_ftf_bounded_writer as writer

original = writer.original
route, base = original.route, original.base


def frozen_policies():
    plan = original.read(writer.PLAN)["team"]
    priors, pool, fitted = original.selections()
    frozen = {**pool, **fitted}
    team = []
    for label, mass in plan["feasible_mixture"]["mixture"].items():
        if label in plan["added_policies"]:
            slot = plan["added_policies"][label]
            policy, swap = slot["policy"], slot["swap_desks"]
        else:
            orientation, name = label.split(":", 1)
            policy, swap = frozen[name], orientation == "swapped"
        team.append((base.space.as_policy(policy), swap, mass))
    comparator = original.read(writer.SILENT)
    silent = [(base.space.as_policy(policy), False, comparator["mixture"][name])
              for name, policy in comparator["tables"].items()]
    return priors, team, silent


def delivery_distribution(policies, prior):
    weighted = np.zeros(8)
    cost = 0.
    for policy, swap, mass in policies:
        result = route.evaluate(policy, prior.T if swap else prior, np.zeros(8), route.TRAIN_LOSS)
        weighted += mass * np.asarray(result["receipt_distribution"])
        cost -= mass * result["net"]
    assert np.isclose(weighted.sum(), 1)
    return weighted, cost


def evaluate(scored_path):
    old_path = writer.BASE / "scores.json"
    original_scores = original.read(old_path)
    new_scores = original.read(scored_path)
    observed_compare = writer.compare(scored_path)["comparison"]
    priors, team, independent = frozen_policies()
    outcome = {}
    for name, prior in priors.items():
        team_receipts, team_cost = delivery_distribution(team, prior)
        ref_receipts, ref_cost = delivery_distribution(independent, prior)
        net_receipt_difference = team_receipts - ref_receipts
        row = {}
        for category, vector in (("raw", "raw_vector"), ("release", "eligible_vector")):
            starting = np.array(original_scores[vector])
            ending = np.array(new_scores[vector])
            uplift = ending - starting
            effects = net_receipt_difference * uplift
            matched = observed_compare[category][name]
            assert abs(matched["original"] - ((net_receipt_difference @ starting) - team_cost + ref_cost)) < 1e-8
            assert abs(matched["bounded"] - ((net_receipt_difference @ ending) - team_cost + ref_cost)) < 1e-8
            assert abs(matched["bounded"] - matched["original"] - effects.sum()) < 1e-8
            row[category] = {"team_absolute_uplift": float(team_receipts @ uplift),
                             "independent_absolute_uplift": float(ref_receipts @ uplift),
                             "net_margin_change": float(effects.sum()), "receipts_contributions": effects.tolist()}
        outcome[name] = {"team_receipts": team_receipts.tolist(), "independent_receipts": ref_receipts.tolist(),
                         "team_cost": team_cost, "independent_cost": ref_cost, **row}
    return {
        "scope": "Frozen routing probabilities and fees. Multiply each per-receipt score change by the "
                 "difference in receipt probabilities to recover the change in team-minus-independent margin.",
        "original_scores_sha256": original.digest(old_path), "new_scores_sha256": original.digest(scored_path),
        "outcomes": outcome,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scores", type=Path)
    print(json.dumps(evaluate(cli.parse_args().scores), indent=2))
