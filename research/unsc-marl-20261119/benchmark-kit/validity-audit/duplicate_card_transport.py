"""Enumerate receipt failures and writer fallback under partner and link changes."""
from hashlib import sha256
from itertools import product
import json

import numpy as np

from duplicate_card_outcome_policy import (
    EVIDENCE, FIT, PRIORS, PRIVATE, RECEIPT, SIGNAL_COST, archived_profiles,
)
from source_route_search import LEGAL
from source_route_fit import MESSAGE_COST

PHASE_POLICY = EVIDENCE / "guarded-phase-policy.json"
MASKS = tuple(product((0, 1), repeat=2))
FAULTS = {
    "none": (0., 0.),
    "signals_10": (.10, 0.),
    "deliveries_10": (0., .10),
    "both_10": (.10, .10),
    "both_25": (.25, .25),
}


def mask_weight(mask, failure):
    return float(np.prod([1 - failure if kept else failure for kept in mask]))


def simulate(tables, prior, values, signal_fail, delivery_fail):
    bits = tables[np.arange(2), PRIVATE, 0]
    assert np.all(bits <= ((PRIVATE & 2) != 0))
    masses = np.zeros(4)
    num_deliveries = 0.
    for mask in MASKS:
        phase = 1 + 2 * bits + bits[:, ::-1] * mask
        actions = tables[np.arange(2), PRIVATE, phase]
        assert np.all(LEGAL[PRIVATE, actions])
        phase_weight = mask_weight(mask, signal_fail)
        num_deliveries += phase_weight * float(prior @ (actions != 0).sum(axis=1))
        for delivery in MASKS:
            left, right = (actions * delivery).T
            masses += np.bincount(RECEIPT[left, right], weights=prior, minlength=4) * (
                phase_weight * mask_weight(delivery, delivery_fail)
            )
    assert np.isclose(masses.sum(), 1)
    signals = float(prior @ bits.sum(axis=1))
    reward_by_receipt = np.array([values[0, 0], values[0, 1], values[0, 2], values[1, 2]])
    totals = {}
    for arm, receipt in (
        ("direct", masses),
        ("buffered", np.array([masses[:3].sum(), 0, 0, masses[3]])),
    ):
        totals[arm] = {
            "net": float(receipt @ reward_by_receipt - SIGNAL_COST * signals - MESSAGE_COST * num_deliveries),
            "record_points": float(receipt @ reward_by_receipt),
            "rejected_probability": float(receipt @ (reward_by_receipt == 0)),
            "writer_receipts": receipt.tolist(),
        }
    return {"attempted_signals": signals, "attempted_deliveries": num_deliveries,
            "transport_receipts": masses.tolist(), "writer": totals}


def inputs():
    phase = np.asarray(json.loads(PHASE_POLICY.read_text())["guarded_table"])
    old = np.asarray(json.loads(FIT.read_text())["learned_table"])
    profiles, hashes = archived_profiles()
    return phase, old, profiles["venezuela_original_release"], hashes


def run():
    phase, proof, values, hashes = inputs()
    policies = {
        "matching_phase_pair": phase,
        "one_old_desk_first": np.stack((proof[0], phase[1])),
        "one_old_desk_second": np.stack((phase[0], proof[1])),
        "two_old_desks": proof,
        "silence": np.zeros_like(phase),
    }
    report = {prior_name: {
        partner_name: {fault: simulate(table, prior, values, *rates) for fault, rates in FAULTS.items()}
        for partner_name, table in policies.items()
    } for prior_name, prior in PRIORS.items()}
    original = json.loads(PHASE_POLICY.read_text())["evaluation"]["venezuela_original_release"]["priors"]
    for prior, old in original.items():
        assert np.isclose(report[prior]["matching_phase_pair"]["none"]["writer"]["direct"]["net"],
                          old["guarded"]["net"])
    return {"scope": "Exact simulation of archived scored outputs and independent signal and card erasures. "
                     "Buffered writer sees both distinct cards or the validated empty packet.",
            "phase_policy_sha256": sha256(PHASE_POLICY.read_bytes()).hexdigest(),
            "proof_policy_sha256": sha256(FIT.read_bytes()).hexdigest(),
            "score_hashes": hashes, "fault_rates": FAULTS, "priors": report}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
