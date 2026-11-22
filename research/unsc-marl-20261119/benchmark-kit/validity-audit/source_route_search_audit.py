"""Separate proof coverage from delivery costs in the learned policies."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

from source_route_fit import CASE, CHOICES, MESSAGE_COST, reward
from source_route_search import PRIVATE, TEST_WEIGHTS, play
from source_route_signal import ANNOUNCEMENTS, PHASES, POLICIES, SIGNAL_COST, optimize, terminal_matrix

REPORT = Path(__file__).resolve().parent.parent / "evidence/source-route-signal/policy-search.json"
BLOCKS = np.array(CHOICES)


def totals(public, bits, actions, weights=TEST_WEIGHTS):
    coverage = public | BLOCKS[0, actions[..., 0]] | BLOCKS[1, actions[..., 1]]
    earned = np.array([reward(int(view), weights) for view in coverage])
    signals = int(bits.sum())
    blocks = int(np.count_nonzero(actions))
    return {
        "mean_proof": float(earned.mean()),
        "signals": signals,
        "blocks": blocks,
        "mean_return": float(earned.mean() - (SIGNAL_COST * signals + MESSAGE_COST * blocks) / len(earned)),
    }, earned.tolist()


def coverage_contrast():
    # No private source is already public. Increase the relative priority of
    # the comparison, then disregard costs to isolate the information ceiling.
    weights = (4, 4, 7)
    proof = np.array([[reward(a | b, weights) for b in CHOICES[1]] for a in CHOICES[0]])
    values = proof[POLICIES[:, None, :, None], POLICIES[None, :, None, :]]
    scores = []
    for left, right in product(ANNOUNCEMENTS, repeat=2):
        conditional = [(np.equal(left, x)[:, None] & np.equal(right, y)[None, :]) for x, y in PHASES]
        scores.append(sum((values * worlds).sum(axis=(2, 3)).max() for worlds in conditional) / len(PRIVATE))
    silent, announce, optional = optimize(0, weights)
    return {"public": 0, "weights": weights, "coverage_ceiling_silent": float(values.mean(axis=(2, 3)).max()),
            "coverage_ceiling_signals": float(max(scores)), "net_return_ceiling_silent": silent,
            "net_return_ceiling_always_announce": announce, "net_return_ceiling_optional": optional}


def run():
    data = json.loads(REPORT.read_text())
    no_signal = np.stack(np.meshgrid(np.arange(len(POLICIES)), np.arange(len(POLICIES))), axis=-1).reshape(-1, 2)
    actions = POLICIES[no_signal[:, None, :], PRIVATE[None]]
    rows = []
    for case in data["masks"]:
        mask = case["public"]
        payoff = terminal_matrix(mask, TEST_WEIGHTS)
        values = payoff[actions[..., 0], actions[..., 1]].mean(axis=-1)
        assert abs(values.max() - case["no_signal_optimal"]) < 1e-9
        best = np.isclose(values, values.max(), rtol=0, atol=1e-9)
        silent = [totals(mask, np.zeros_like(choices), choices) for choices in actions[best]]
        row = {
            "public": mask,
            "optimal_silent_policy_count": len(silent),
            "silent_proof_range": [min(x[0]["mean_proof"] for x in silent),
                                   max(x[0]["mean_proof"] for x in silent)],
            "silent_block_range": [min(x[0]["blocks"] for x in silent), max(x[0]["blocks"] for x in silent)],
        }
        for variant in ("single_entry", "coordinated"):
            table = np.asarray(case[variant]["table"])
            original = [x[0] for x in play(table[None], payoff)]
            summary, proof = totals(mask, *original[:2])
            assert abs(summary["mean_return"] - case[variant]["return"]) < 1e-9
            table[..., 0] = 0
            blocked = [x[0] for x in play(table[None], payoff)]
            ablated, _ = totals(mask, *blocked[:2])
            row[variant] = {**summary, "signals_blocked_without_refit": ablated,
                            "matched_by_optimal_silent_per_world_proof": any(p == proof for _, p in silent)}
        rows.append(row)
    return {"policy_search_sha256": sha256(REPORT.read_bytes()).hexdigest(),
            "source_packet_sha256": sha256(CASE.read_bytes()).hexdigest(), "masks": rows,
            "post_test_proof_coverage_contrast": coverage_contrast()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
