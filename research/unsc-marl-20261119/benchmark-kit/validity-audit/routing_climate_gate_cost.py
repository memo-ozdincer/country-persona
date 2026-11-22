"""Measure how much gate-check cost the demonstrated routing gain can absorb."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_climate_scope_gate as gate

transfer, read, digest = gate.transfer, gate.read, gate.digest
route = transfer.route
PLAN = gate.MAIN / "plan.json"


def intervention_rate(group, prior, masks):
    total = 0.
    for p, swap, weight in group:
        result = route.evaluate(transfer.base.space.as_policy(p), prior.T if swap else prior,
                                np.zeros(8), route.TRAIN_LOSS)
        total += weight * sum(result["receipt_distribution"][mask] for mask in masks)
    return total


def evaluate(path):
    replayed = read(path)["outcomes"]["restriction"]
    masks = [int(row["id"].removeprefix("visible-")) for row in replayed["decisions"]]
    assert masks == [2, 3]
    plans = read(PLAN)["plans"]
    priors, _, _ = transfer.original.selections()
    comparison = {}
    for name, prior in priors.items():
        row = replayed["results"][name]
        rates = {label: intervention_rate(plan, prior, masks) for label, plan in plans.items()}
        comparison[name] = {"eligible_receipt_check_probability": rates, "comparisons": {}}
        for label in ("independent", "scripted"):
            difference = rates["learned"] - rates[label]
            gain = row["learned_gains"][label]
            assert gain > 0
            comparison[name]["comparisons"][label] = {
                "net_gain_before_judge_cost": gain, "expected_extra_judgments_combined": 4 * difference,
                "break_even_points_per_combined_judgment": gain / (4 * difference) if difference > 1e-12 else None,
            }
    return {
        "scope": "Price the exact demonstrated replay only. Both teams invoke the same four checks on the two "
                 "scope-calibrated receipts. All other receipts retain prior review. Null means the learned "
                 "plan uses no more judgments than its comparator.",
        "replay_sha256": digest(path), "plan_sha256": digest(PLAN), "cases": comparison,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("replay", type=Path)
    print(json.dumps(evaluate(cli.parse_args().replay), indent=2))
