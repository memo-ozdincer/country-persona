"""Exhaustively stress the constrained negotiation policy using matched interventions."""
import argparse
from collections import Counter
from itertools import permutations, product
import json
from pathlib import Path

import torch

from environment import FAMILIES, HOLD, outcome, overlap, world
from structured import Delegate, rollout


def exhaustive_worlds(family):
    n = len(FAMILIES[family]["options"])
    menus = [
        {i for i, bit in enumerate(bits) if bit}
        for bits in product((0, 1), repeat=n) if any(bits)
    ]
    return [world(family, order, (a, b))
            for a, b in product(menus, repeat=2) for order in permutations(range(n))]


def scripted(cases, name):
    rows = []
    for case in cases:
        first = [bits.index(1) for bits in case["mandates"]]
        if name == "hold":
            proposals = ballots = [HOLD, HOLD]
        elif name == "solo_first":
            proposals = ballots = first
        elif name == "peer_priority":
            proposals = first
            ballots = [
                next((choice for choice in first if case["mandates"][role][choice]), HOLD)
                for role in range(2)
            ]
        elif name == "full_exchange":
            # This comparator exchanges whole support menus and uses public
            # order to select their intersection. It has a larger channel.
            shared = overlap(case)
            proposals = [HOLD, HOLD]
            ballots = [shared[0] if shared else HOLD] * 2
        else:
            raise ValueError(name)
        rows.append({"case": case, "signals": proposals, "ballots": ballots, **outcome(case, proposals, ballots)})
    return rows


def summarize(rows, window):
    counts = Counter()
    groups = []
    for row in rows:
        counts["feasible"] += row["feasible"]
        counts["infeasible"] += not row["feasible"]
        counts["strict_feasible"] += row["strict"] and row["feasible"]
        counts["strict_infeasible"] += row["strict"] and not row["feasible"]
        for key in ("false_hold", "unsupported_signal", "unsupported_ballot"):
            counts[key] += row[key]
        groups.append(row["strict"])
    agreement = counts["strict_feasible"] / counts["feasible"]
    deadlock = counts["strict_infeasible"] / counts["infeasible"]
    return {
        **counts, "agreement_recall": agreement, "deadlock_recall": deadlock,
        "balanced_success": (agreement + deadlock) / 2,
        "worst_class_success": min(agreement, deadlock),
        "permutation_sensitive_success_profiles": sum(
            0 < sum(groups[i:i + window]) < window for i in range(0, len(groups), window)
        ),
        "total_profiles": len(groups) // window,
    }


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("policy", type=Path)
    args.add_argument("output", type=Path)
    paths = args.parse_args()
    torch.set_num_threads(1)
    policy = Delegate()
    policy.load_state_dict({k: torch.tensor(v) for k, v in json.loads(paths.policy.read_text()).items()})
    results = {}
    with torch.no_grad():
        for family in FAMILIES:
            cases = exhaustive_worlds(family)
            window = len(set(tuple(case["options"]) for case in cases))
            family_rows = {name: rollout(policy, cases, name, greedy=True)[0]
                           for name in ("peer", "silent")}
            # Group by display order so adjacent rows come from distinct
            # private-menu profiles. Restore original order for paired scoring.
            indexes = sorted(range(len(cases)), key=lambda i: i % window)
            shuffled_rows = rollout(policy, [cases[i] for i in indexes], "shuffled", greedy=True)[0]
            family_rows["shuffled"] = [row for _, row in sorted(zip(indexes, shuffled_rows))]
            for offset, index in enumerate(indexes):
                donor = indexes[offset - 1]
                assert index // window != donor // window
                assert family_rows["shuffled"][index]["received"] == family_rows["peer"][donor]["signals"][::-1]
            for name in ("hold", "solo_first", "peer_priority", "full_exchange"):
                family_rows[name] = scripted(cases, name)
            results[family] = {name: summarize(rows, window) for name, rows in family_rows.items()}
            real = family_rows["peer"]
            for control in ("silent", "shuffled"):
                compared = zip(real, family_rows[control])
                results[family][f"peer_vs_{control}"] = dict(Counter(
                    f"{'met' if a['strict'] else 'failed'}_vs_{'met' if b['strict'] else 'failed'}"
                    for a, b in compared
                ))
    with paths.output.open("x") as output:
        json.dump(results, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
