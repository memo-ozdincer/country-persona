"""Capacity reference for sequential voluntary, signed, role-local disclosures."""
from collections import Counter
import json

from public_planner import HORIZON, apply, states, terminal


def verdict(world, opening, chooser):
    """Return how many continuation slots suffice with that selection policy."""
    state = opening
    for step in range(HORIZON+1):
        if terminal(state):
            return step
        if step == HORIZON:
            break
        i = (step + 1) % 2
        choice = chooser(world, state, i)
        if choice:
            state = apply(state, i, choice, bool(world[i] & choice))
    return None


def choose_local(world, state, i):
    # Only this role's private set is available. Use peer's public signs.
    a, b, c, d = state
    own, peer = (a, c) if i == 0 else (c, a)
    remaining = 15 & ~(b | d | own)
    local = world[i]
    for group in (peer & local, peer & ~local, ~local, local):
        available = group & remaining
        if available:
            return available & -available
    return None


def reachable(world, opening):
    """Shortest certificate assuming full information about both menus."""
    candidates = {opening}
    for step in range(HORIZON+1):
        if any(map(terminal, candidates)):
            return step
        i = (step + 1) % 2
        candidates |= {apply(state, i, 1 << o, bool(world[i] & (1 << o)))
                       for state in candidates for o in range(4)}
    return None


def scores():
    counts = Counter()
    for world, opening in states():
        agreement = bool(world[0] & world[1])
        for arm, steps in (("local_script", verdict(world, opening, choose_local)),
                           ("omniscient_capacity", reachable(world, opening))):
            counts[arm, agreement, steps] += 1
    return {arm: {label: {str(n): counts[arm, overlap, n] for n in (*range(HORIZON+1), None)}
                  for overlap, label in ((True, "agreement"), (False, "impasse"))}
            for arm in ("local_script", "omniscient_capacity")}


if __name__ == "__main__":
    print(json.dumps(scores(), indent=2))
