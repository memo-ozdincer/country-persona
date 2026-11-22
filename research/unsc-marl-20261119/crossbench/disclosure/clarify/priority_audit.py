"""Audit how much the fixed role-local control depends on its priority order."""
from itertools import permutations
import json

from public_planner import states
from voluntary_bound import verdict

GROUPS = ("match_peer", "exclude_peer", "exclude_unknown", "accept_unknown")


def policy(order):
    def choose(world, state, i):
        a, b, c, d = state
        own, peer = (a, c) if i == 0 else (c, a)
        remaining = 15 & ~(b | d | own)
        local = world[i]
        candidates = (peer & local, peer & ~local, ~peer & ~local, ~peer & local)
        for idx in order:
            eligible = remaining & candidates[idx]
            if eligible:
                return eligible & -eligible
        return None
    return choose


def report():
    all_worlds = list(states())
    results = []
    for order in permutations(range(len(GROUPS))):
        counts = [0, 0]
        turns = 0
        chooser = policy(order)
        for world, opening in all_worlds:
            first = verdict(world, opening, chooser)
            if first is not None:
                counts[int(not (world[0] & world[1]))] += 1
            turns += first if first is not None else 4
        results.append({"order": [GROUPS[i] for i in order], "agreement": counts[0], "impasse": counts[1],
                        "balanced_score": 0.5 * (counts[0]/916 + counts[1]/108),
                        "mean_turns": turns/len(all_worlds)})
    return results


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
