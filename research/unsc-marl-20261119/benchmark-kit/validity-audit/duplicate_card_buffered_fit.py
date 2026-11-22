"""Fit decentralized buffered delivery against reliable and mixed partners."""
from hashlib import sha256
from itertools import product
import json
import sys

import numpy as np

from duplicate_card_outcome_policy import EVIDENCE, PRIORS, PRIVATE, RECEIPT, SIGNAL_COST, TRAIN, TRAIN_PROFILES
from duplicate_card_transport import FAULTS, MASKS, PHASE_POLICY, inputs, mask_weight, simulate
from source_route_fit import MESSAGE_COST
from source_route_signal import ANNOUNCEMENTS, POLICIES

PAIR_REWARD = 7.
TRAIN_FAILURE = (.15, .15)
SELF_WEIGHT = .5
POOL = np.asarray(list(product(POLICIES, repeat=2)))
SEATS = np.arange(2)


def action_matrix(pair_gain, delivery_fail):
    # A buffered writer uses the pair only if both distinct attempted cards
    # arrive. Failed transmissions still cost the sender.
    return (pair_gain * (1 - delivery_fail) ** 2 * (RECEIPT == 3)
            - MESSAGE_COST * np.add.outer([0, 1, 1], [0, 1, 1]))


def response(seat, peer_bit):
    return POOL[:, peer_bit, PRIVATE[:, seat]]


def self_values(prior, matrix, signal_fail, first, second):
    bits = np.stack([first, second], axis=-1)
    values = np.zeros((len(POOL), len(POOL)))
    for mask in MASKS:
        left, right = (response(seat, bits[:, 1-seat] * mask[seat]) for seat in (0, 1))
        values += (matrix[left[:, None], right[None, :]] @ prior) * mask_weight(mask, signal_fail)
    return values - SIGNAL_COST * (prior @ bits.sum(axis=1))


def cross_values(prior, matrix, fail, seat, own_bit, legacy):
    other = 1 - seat
    old_bit = legacy[other, PRIVATE[:, other], 0]
    values = np.zeros(len(POOL))
    for mask in MASKS:
        old_phase = 1 + 2 * old_bit + own_bit * mask[other]
        old_action = legacy[other, PRIVATE[:, other], old_phase]
        own_action = response(seat, old_bit * mask[seat])
        # Buffered values are symmetric in the two delivery actions and costs.
        values += (matrix[own_action, old_action] @ prior) * mask_weight(mask, fail)
    return values - SIGNAL_COST * (prior @ (own_bit + old_bit))


def compile_policy(announcements, indices):
    table = np.zeros((2, 4, 5), dtype=np.int8)
    for seat, (bit, choice) in enumerate(zip(announcements, indices, strict=True)):
        table[seat, :, 0] = bit
        types = np.arange(4)
        for peer_bit in (0, 1):
            phase = 1 + 2 * np.asarray(bit) + peer_bit
            table[seat, types, phase] = POOL[choice, peer_bit]
    return table


def optimize(prior, pair_gain, rates, partners=(), self_weight=1.):
    signal_fail, delivery_fail = rates
    matrix = action_matrix(pair_gain, delivery_fail)
    cache = {}
    for seat, announcement in product((0, 1), ANNOUNCEMENTS):
        if partners:
            bit = np.asarray(announcement)[PRIVATE[:, seat]]
            cache[seat, announcement] = np.mean(
                [cross_values(prior, matrix, signal_fail, seat, bit, legacy) for legacy in partners], axis=0
            )
    extrema = {}
    for left, right in product(ANNOUNCEMENTS, repeat=2):
        bits = (np.asarray(left)[PRIVATE[:, 0]], np.asarray(right)[PRIVATE[:, 1]])
        values = self_values(prior, matrix, signal_fail, *bits)
        if partners:
            values = (self_weight * values + (1 - self_weight) / 2 *
                      (cache[0, left][:, None] + cache[1, right][None, :]))
        idx = np.unravel_index(values.argmax(), values.shape)
        entry = (float(values[idx]), compile_policy((left, right), idx))
        if left == right == ANNOUNCEMENTS[0]:
            extrema["silent"] = entry
        if "optional" not in extrema or entry[0] > extrema["optional"][0] + 1e-10:
            extrema["optional"] = entry
    return extrema


def play_buffered(table, prior, values, rates):
    return simulate(table, prior, values, *rates)["writer"]["buffered"]


def priority_pair(card):
    table = np.zeros((2, 4, 5), dtype=np.int8)
    preference = [0, 1, 2, card]
    table[:, :, 1:] = np.array(preference)[None, :, None]
    return table


def run(diverse=False):
    prior_phase, proof, values, hashes = inputs()
    population = {"proof": proof}
    if diverse:
        population.update({"phase": prior_phase, "first_priority": priority_pair(1),
                           "second_priority": priority_pair(2)})
    self_fit, self_policy = optimize(TRAIN, PAIR_REWARD, TRAIN_FAILURE)["optional"]
    mixed_fit, mixed_policy = optimize(TRAIN, PAIR_REWARD, TRAIN_FAILURE,
                                      tuple(population.values()), SELF_WEIGHT)["optional"]
    synthetic = PAIR_REWARD * (RECEIPT == 3)
    for name, score, policy, self_weight in (
        ("matched", self_fit, self_policy, 1.), ("mixed", mixed_fit, mixed_policy, SELF_WEIGHT),
    ):
        direct = play_buffered(policy, TRAIN, synthetic, TRAIN_FAILURE)["net"]
        swaps = [pair for other in population.values()
                 for pair in (np.stack((policy[0], other[1])), np.stack((other[0], policy[1])))]
        mean = sum(play_buffered(pair, TRAIN, synthetic, TRAIN_FAILURE)["net"] for pair in swaps) / len(swaps)
        assert np.isclose(score, self_weight * direct + (1 - self_weight) * mean), name

    pairs = {"guarded_original": prior_phase, "proof_original": proof,
             "matched_fit": self_policy, "mixed_fit": mixed_policy}
    partners = {"legacy_proof": proof, "training_phase" if diverse else "held_out_phase": prior_phase}
    if diverse:
        old_fit = json.loads((EVIDENCE / "outcome-policy.json").read_text())["training"]["tables"]
        for scenario in ("both_useful", "both_or_neither"):
            partners["held_out_" + scenario] = np.array(old_fit[list(TRAIN_PROFILES).index(scenario)])
        assert all(not np.array_equal(table, known)
                   for name, table in partners.items() if name.startswith("held_out")
                   for known in population.values())
    for name, policy in (("matched_fit", self_policy), ("mixed_fit", mixed_policy)):
        for partner, other in partners.items():
            pairs[f"{name}_first_{partner}"] = np.stack((policy[0], other[1]))
            pairs[f"{name}_second_{partner}"] = np.stack((other[0], policy[1]))

    rows = {}
    for name, prior in PRIORS.items():
        rows[name] = {}
        for condition in ("none", "both_10", "both_25"):
            rates = FAULTS[condition]
            controls = optimize(prior, values[1, 2] - values[0, 0], rates)
            policies = {**pairs, **{f"exact_buffered_{key}": table for key, (_, table) in controls.items()}}
            result = {key: play_buffered(table, prior, values, rates) for key, table in policies.items()}
            for key, (return_, _) in controls.items():
                assert np.isclose(result[f"exact_buffered_{key}"]["net"], values[0, 0] + return_)
            assert all(x["rejected_probability"] == 0 for x in result.values())
            assert all(x["net"] <= result["exact_buffered_optional"]["net"] + 1e-9 for x in result.values())
            rows[name][condition] = result

    report = {"scope": "Exact synthetic policy improvement and paired replay with a both-card receipt buffer.",
            "phase_policy_sha256": sha256(PHASE_POLICY.read_bytes()).hexdigest(),
            "score_hashes": hashes, "training_rates": TRAIN_FAILURE,
            "training_pair_reward": PAIR_REWARD, "candidate_policies_per_seat_per_announcement": len(POOL),
            "mixed_training_self_weight": SELF_WEIGHT, "synthetic_training_net": {"matched": self_fit, "mixed": mixed_fit},
            "trained_tables": {"matched": self_policy.tolist(), "mixed": mixed_policy.tolist()}, "priors": rows}
    if diverse:
        report["partner_population"] = list(population)
        report["held_out_policy_source_sha256"] = sha256((EVIDENCE / "outcome-policy.json").read_bytes()).hexdigest()
    return report


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--diverse"]):
        raise SystemExit("usage: duplicate_card_buffered_fit.py [--diverse]")
    print(json.dumps(run(bool(sys.argv[1:])), indent=2))
