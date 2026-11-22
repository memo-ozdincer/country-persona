"""Expose conflicting cases that are indistinguishable to the current actors."""
from hashlib import sha256
import json
from pathlib import Path

import facilitator_receipt_ceiling as ceiling

HERE = ceiling.HERE
BASELINE = HERE / "facilitator-receipt-ceiling-results.json"
KEY = ("supports", "contradicts")


def run():
    cohorts = ceiling.datasets()
    cases = {key: row for group in cohorts.values() for key, row in group.items()}
    assert len(cases) == sum(map(len, cohorts.values())) == 12
    ambiguous = {key: case for key, case in cases.items() if case["reads"] == KEY}
    assert len(ambiguous) == 4
    decisive = frozenset({1})
    reference = {panel: row["receipts"][decisive] for (panel, _), row in ambiguous.items()}
    assert sum(row["expected"] == "withhold" for row in reference.values()) == 1
    assert all(row["action"] == "revise" for row in reference.values())

    frozen, independent = ceiling.stock()
    raw = ceiling.DEV.load(BASELINE)
    optimized_noisy = {ceiling.compiled.freeze(row["state"]): row["probabilities"]
                       for row in raw["evidence"]["unifil_colombia"]["split"]["optimal_policies"]["adaptive"]}
    best, certificate = ceiling.solve(cases, "split", True)
    systems = (("tuned_on_noisy_block", "learned", frozen | optimized_noisy),
               ("pooled_oracle", "learned", best), ("frozen_adaptive", "learned", frozen),
               ("trained_independent", "learned_erased", independent), ("greedy", "greedy", {}))
    replay = ceiling.measure(cases, systems, "split")
    assert abs(replay["pooled_oracle"]["summary"][ceiling.MODE]["brief_net"] - certificate["exact_net"]) < 1e-9

    collisions = {}
    for name, rows in replay.items():
        table = {panel: rows["cases"][f"{panel}/{ceiling.MODE}"] for panel in reference}
        delivery = {panel: row["receipt_slot_2_only"] + row["receipt_both"] for panel, row in table.items()}
        assert max(delivery.values()) - min(delivery.values()) < 1e-9
        collisions[name] = {"delivery_of_slot_2": delivery,
                            "false_action": {panel: row["false_action"] for panel, row in table.items()},
                            "usable_revision": {panel: row["usable_revise"] for panel, row in table.items()}}
        for panel, row in reference.items():
            if row["expected"] == "withhold":
                assert abs(table[panel]["false_action"] - delivery[panel]) < 1e-9
            else:
                assert table[panel]["usable_revise"] <= delivery[panel] + 1e-9
    return {"scope": "Exact retrospective comparison of cases with the same local observed relations, action "
                     "sets and roster. Optimized policies receive no differentiating per-case feature.",
            "observed_relation_pair": KEY, "decision_at_slot_2": reference,
            "pooled_ceiling": certificate, "cases": collisions, "replay": replay,
            "inputs_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in
                              (BASELINE, Path(__file__), Path(ceiling.__file__))}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
