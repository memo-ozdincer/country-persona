"""Measure where the public claim-type signal is available to learn."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path

import facilitator_claim_type_fit as study
from facilitator_transfer_attribution import reward_key


def cells(bank, kinds):
    grouped = defaultdict(list)
    for (panel, _), row in bank.items():
        grouped[kinds[panel], row["reads"]].append({"panel": panel, "receipt_payoffs": reward_key(row)})
    return grouped


def overlap(train, test, kinds):
    a, b = (cells(bank, kinds) for bank in (train, test))
    return [{
        "claim_kind": kind,
        "relation_pair": observed,
        "training_examples": a.get((kind, observed), []),
        "test_examples": rows,
        "test_payoff_patterns_absent_from_train": sorted(
            {row["receipt_payoffs"] for row in rows} -
            {row["receipt_payoffs"] for row in a.get((kind, observed), [])}
        ),
    } for (kind, observed), rows in b.items()]


def run(artifact):
    fit = json.loads(artifact.read_text())
    train, cohorts, kinds = study.datasets()
    assert fit["training_cases"] == {panel: kinds[panel] for panel, _ in train}
    augmented = study.prior.augmented(train)
    expanded = kinds | {f"{p}/swapped": k for p, k in kinds.items()}
    ceiling = study.ceilings(augmented, expanded, "training")
    gaps = {name: ceiling[name]["adaptive"] - fit["practice"]["overall"][name]["brief_net"]
            for name in ("relation_only", "claim_type")}
    assert all(gap >= -1e-9 for gap in gaps.values())
    coverage = {name: overlap(train, bank, kinds) for name, bank in cohorts.items()}
    comparisons = []
    for family, layouts in fit["transfer"].items():
        both_orders = study.prior.augmented(cohorts[family])
        for layout, result in layouts.items():
            rel, typed = (result["overall"][name]["brief_net"] for name in ("relation_only", "claim_type"))
            order_balanced = study.ceilings(both_orders, expanded, layout)
            comparisons.append({"cohort": family, "layout": layout,
                                "both_slot_orders_ceilings": order_balanced,
                                "both_slot_orders_oracle_gain": order_balanced["claim_type"]["adaptive"] -
                                order_balanced["relation_only"]["adaptive"],
                                "actual_claim_type_gain": typed - rel,
                                "oracle_claim_type_gain": result["ceilings"]["claim_type"]["adaptive"] -
                                result["ceilings"]["relation_only"]["adaptive"]})
    return {"scope": "Retrospective diagnostics. Exact fitting ceilings use both slot assignments and the original payoff. "
                      "The order-balanced transfer ceiling uses one common policy across both slot assignments. "
                     "Coverage matches public type and full observed relation pairs. Desks can have partial views.",
            "training_ceilings": ceiling, "training_gaps_to_ceiling": gaps, "transfer": comparisons,
            "max_absolute_transfer_gain": max(abs(r["actual_claim_type_gain"]) for r in comparisons),
            "observation_coverage": coverage,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), artifact)}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fit", type=Path)
    print(json.dumps(run(p.parse_args().fit), indent=2))
