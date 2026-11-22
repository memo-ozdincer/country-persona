"""Replay the frozen learned team on the separate verified Colombia endpoint."""
from functools import lru_cache
from itertools import permutations
import json
import sys
from unittest.mock import patch

from verified_bank import HERE, compile_bank, runner

sys.path.insert(0, str(HERE.parent / "ftf2020"))
import adaptive_align as align
import adaptive_transfer as transfer

relay = transfer.relay


def run():
    ids, verified = compile_bank()
    # Build the current case's public proof table using the same adapter as
    # the earlier held-out-to-fit UNAMI and UNIFIL comparisons.
    deck = ({name: None for name in ids},)
    with patch.multiple(transfer, named_sources=lambda: ({"colombia": deck}, {}),
                        record_bank=lambda spec: verified):
        mapped = align.enrich()["families"]["colombia"]
    frozen = transfer.read(transfer.FROZEN)
    policy = {transfer.immutable(row["local_state"]): row["probabilities"] for row in frozen["policy"]}

    @lru_cache(None)
    def distribution(target, anchor):
        return transfer.outcomes(policy, target, anchor, relay.DESIGN)

    weights = []
    for names in permutations(ids):
        score = transfer.mean([transfer.policy_compare(target, anchor, names, verified,
                                                        {"frozen_joint": distribution(target, anchor)})
                               for target, anchor in relay.SCENARIOS])
        weights.append({"slots": names, "mean": score})
    averaged = transfer.mean([row["mean"] for row in weights])
    best = {route: max(weights, key=lambda row: row["mean"][route]["net_gain_over_anchor"])
            for route in ("fixed_canonical", "adaptive_canonical")}
    return {"scope": "Frozen written-vote MARL weights. The four source IDs denote actual verified Colombia clauses, "
                     "with simulated availability and loss. All activity ends in an authored record assembly. "
                     "No provisional note or open-text semantic judge enters the score.",
            "sources": {name: runner.digest(path) for name, path in (
                ("compiled_bank", HERE / "verified-bank.json"), ("fitted_policy", transfer.FROZEN))},
            "alias_means": averaged, "best_scripted": best, "aligned": mapped, "aliases": weights}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
