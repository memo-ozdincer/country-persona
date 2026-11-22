"""Fit a brief-reward router with arbitrary source positions balanced."""
from hashlib import sha256
import json
from pathlib import Path

import facilitator_record_policy as parent

HERE = parent.HERE
PRIOR = HERE / "facilitator-record-policy-results.json"


def mirror_cases(cases):
    swapped = {}
    for (panel, mode), case in cases.items():
        # Keep each document with its relation, its original grading and its
        # described actor. Only the address used in the simulator changes.
        receipts = {frozenset(1 - i for i in mask): mark for mask, mark in case["receipts"].items()}
        swapped[(panel, mode)] = {"reads": case["reads"][::-1], "receipts": receipts}
    return swapped


def merged(cases, swapped):
    return cases | {(f"{panel}-swapped", channel): row for (panel, channel), row in swapped.items()}


def run():
    base = parent.base
    train = parent.collect(parent.development())
    swapped = mirror_cases(train)
    assert mirror_cases(swapped) == train
    training = merged(train, swapped)
    states, actions, outcomes, mass = parent.training_batch(training)
    trace, fit = base.base.optimizer.fit(states, actions, outcomes["brief"], mass)
    balanced = base.base.observed_weights(states, fit["joint_learned"])
    previous = parent.dev.load(PRIOR)
    from facilitator_policy_audit import freeze

    brief = {freeze(row["state"]): row["probabilities"] for row in previous["policies"]["brief"]}
    frozen = parent.dev.transfer.policy(parent.dev.transfer.FROZEN)
    policies = [("balanced", "learned", balanced), ("balanced_erased", "learned_erased", balanced),
                ("brief", "learned", brief), ("frozen", "learned", frozen), ("greedy", "greedy", {})]
    practice = parent.evaluate(training, policies, "training")
    assert abs(practice["balanced"]["summary"]["mean"]["brief_net"] - trace[-1]["record_reward"]) < 1e-9
    test = parent.collect(parent.held_out())
    reversed_test = mirror_cases(test)
    comparisons = {
        inventory: {"original_slots": parent.evaluate(test, policies, inventory),
                    "swapped_slots": parent.evaluate(reversed_test, policies, inventory)}
        for inventory in ("split", "overlap")
    }
    for inventory, arms in comparisons.items():
        for method in ("brief", "frozen", "greedy"):
            assert arms["original_slots"][method] == previous["transfer"][inventory][method]
        for method in ("balanced", "balanced_erased"):
            for case, before in arms["original_slots"][method]["cases"].items():
                after = arms["swapped_slots"][method]["cases"][case]
                assert abs(before["receipt_slot_1_only"] - after["receipt_slot_2_only"]) < 1e-8
                assert abs(before["brief_net"] - after["brief_net"]) < 1e-8
    return {"scope": "One retrospective joint fit on the same authored development receipts with both arbitrary slot assignments. "
                     "The held-out docket texts and scores are excluded from training, and the two test assignments replay the same briefs.",
            "updates": base.base.optimizer.STEPS, "trace": trace, "training": practice, "transfer": comparisons,
            "file_sha256": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in
                            (Path(__file__), Path(parent.__file__), PRIOR)},
            "policy": [{"state": key, "probabilities": values} for key, values in balanced.items()]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
