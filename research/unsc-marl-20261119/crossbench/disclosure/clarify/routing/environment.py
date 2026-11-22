"""Budgeted sequential evidence. Each signed claim may name its next speaker."""
from functools import lru_cache
from itertools import product
from collections import Counter


def presentations(n):
    menus = range(1, 1 << n)
    options = tuple(1 << i for i in range(n))
    for x, y in product(menus, repeat=2):
        for a, b in product(options, repeat=2):
            if a & x and b & y:
                yield (x, y), (a, 0, b, 0)


def terminal(state, full):
    yes0, no0, yes1, no1 = state
    return bool(yes0 & yes1 or (no0 | no1) == full)


def record(state, role, bit, accepted):
    changed = list(state)
    changed[2*role + int(not accepted)] |= bit
    return tuple(changed)


def options_for(local, state, role, full):
    own, peer = state[2*role], state[2*(1-role)]
    remaining = full & ~(state[1] | state[3] | own)
    return tuple(remaining & x for x in (peer & local, ~peer & ~local, ~peer & local, peer & ~local))


def claim(local, state, role, step, full, flex):
    groups = options_for(local, state, role, full)
    order = (0, 3, 1, 2) if step == 0 and local.bit_count() == 1 else (0, 1, 2, 3)
    if flex and (local.bit_count() == 1 or (step == 0 and local.bit_count() == full.bit_count()-1)):
        order = (0, 3, 1, 2)
    for i in order:
        if groups[i]:
            return groups[i] & -groups[i]
    return 0


def routing_prior(local, post_claim, role, full, step=None, bit=None):
    """A role covering few packages can disclose its unresolved exclusions now."""
    choices = options_for(local, post_claim, role, full)
    return role if local.bit_count() == 1 and (choices[1] or choices[3]) else 1-role


def simulate(n, world, state, mode, route=routing_prior):
    full = (1 << n) - 1
    role = 1
    trace = []
    for step in range(n):
        if terminal(state, full):
            break
        local = world[role]
        bit = claim(local, state, role, step, full, flex=mode != "alternating")
        if bit:
            state = record(state, role, bit, bool(bit & local))
        next_role = 1 - role
        if mode == "flexible" and bit and not terminal(state, full):
            next_role = route(local, state, role, full, step, bit)
        trace.append((role, bit, bool(bit & local), next_role))
        role = next_role
    return terminal(state, full), trace


@lru_cache(maxsize=None)
def flexible_capacity(n, world, opening):
    # Only the baseline's first speaker is fixed. Choices here know both menus.
    full = (1 << n) - 1
    frontier = {(opening, 1)}
    for step in range(n+1):
        if any(terminal(state, full) for state, _ in frontier):
            return step
        if step == n:
            return None
        out = set()
        for state, role in frontier:
            eligible = options_for(world[role], state, role, full)
            bits = set(bit for i in range(n) for bit in [1 << i] if any(bit & group for group in eligible))
            for bit in bits or {0}:
                after = record(state, role, bit, bool(bit & world[role])) if bit else state
                for next_role in ((0, 1) if bit else (1-role,)):
                    out.add((after, next_role))
        frontier = out


def control(n, include_capacity=False):
    counts = Counter()
    calls = Counter()
    for world, opening in presentations(n):
        outcome = "agreement" if world[0] & world[1] else "impasse"
        counts["total", outcome] += 1
        for arm in ("alternating", "flexible_claims_alternating", "flexible"):
            certified, trace = simulate(n, world, opening, arm)
            counts[arm, outcome] += certified
            calls[arm] += len(trace)
        if include_capacity:
            counts["capacity", outcome] += flexible_capacity(n, world, opening) is not None
    return {
        "width": n, "slots": n,
        "cases": {"/".join(k): v for k, v in counts.items()},
        "total_slots": dict(calls),
    }
