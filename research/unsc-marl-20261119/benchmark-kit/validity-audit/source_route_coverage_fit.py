"""Test whether reward-only routing can increase proof coverage."""
import json

import numpy as np

from source_route_fit import CHOICES, REQUIRES
from source_route_search import fit, play, PRIVATE, LEGAL, PROPOSALS, UPDATES, SEED
from source_route_search_audit import coverage_contrast, totals
from source_route_signal import POLICIES, terminal_matrix

TRAINING_WEIGHTS = ((4, 3, 7), (3, 5, 8), (5, 4, 9))
BLOCKS = np.array(CHOICES)


def claim_counts(public, actions):
    visible = public | BLOCKS[0, actions[:, 0]] | BLOCKS[1, actions[:, 1]]
    return tuple(int(np.count_nonzero(visible & need == need)) for need in REQUIRES)


def run():
    contrast = coverage_contrast()
    weights = contrast["weights"]
    public = contrast["public"]
    payoff = terminal_matrix(public, weights)
    left = POLICIES[:, PRIVATE[:, 0]]
    right = POLICIES[:, PRIVATE[:, 1]]
    silent = payoff[left[:, None], right[None, :]].mean(axis=-1)
    assert abs(silent.max() - contrast["net_return_ceiling_silent"]) < 1e-9
    silent_claim_counts = sorted({
        claim_counts(public, np.stack((left[a], right[b]), axis=-1))
        for a, b in np.argwhere(np.isclose(silent, silent.max(), rtol=0, atol=1e-9))
    })
    fitted = {}
    for variant in ("single_entry", "coordinated"):
        table, trace = fit(public, variant == "coordinated", TRAINING_WEIGHTS)
        bits, actions, returns = (x[0] for x in play(table[None], payoff))
        assert np.all(bits <= ((PRIVATE & 2) != 0))
        assert np.all(LEGAL[PRIVATE, actions])
        summary, proof = totals(public, bits, actions, weights)
        assert abs(summary["mean_return"] - returns.mean()) < 1e-9
        assert summary["mean_proof"] <= contrast["coverage_ceiling_signals"] + 1e-9
        assert summary["mean_return"] <= contrast["net_return_ceiling_optional"] + 1e-9
        fitted[variant] = {**summary, "claim_counts": claim_counts(public, actions),
                           "table": table.tolist(), "improvements": trace,
                           "worlds": [{"private": private.tolist(), "signals": signal.tolist(),
                                       "evidence": action.tolist(), "proof_points": score, "return": float(value)}
                                      for private, signal, action, score, value
                                      in zip(PRIVATE, bits, actions, proof, returns, strict=True)]}
    return {"training_weights": TRAINING_WEIGHTS, "seed": SEED, "updates": UPDATES,
            "proposals_per_update": PROPOSALS, "exact_controls": contrast,
            "optimal_silent_claim_counts": silent_claim_counts, "learned": fitted}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
