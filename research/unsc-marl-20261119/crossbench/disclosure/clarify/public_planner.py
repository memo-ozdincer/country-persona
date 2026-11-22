"""Exact public-information query planning on the synthetic positive-opening grid.

Menu/opening pairs are uniformly represented within each outcome class.
This fixed prior is a model of the diagnostic grid, not of real delegation positions.
"""
from collections import Counter
from functools import lru_cache
from itertools import product
import json

OPTIONS = 4
MENUS = tuple(range(1, 1 << OPTIONS))
WORLDS = tuple(product(MENUS, repeat=2))
HORIZON = 4


def open_state(a, b):
    return (a, 0, b, 0)


def states():
    for x, y in WORLDS:
        for a, b in product((1 << i for i in range(OPTIONS) if x & (1 << i)),
                            (1 << i for i in range(OPTIONS) if y & (1 << i))):
            yield (x, y), open_state(a, b)


TOTALS = Counter(bool(x & y) for (x, y), _ in states())


def terminal(state):
    a, b, c, d = state
    return bool(a & c) or b | d == (1 << OPTIONS) - 1


@lru_cache(maxsize=None)
def posterior(state):
    a, b, c, d = state
    return [(x, y) for x, y in WORLDS if x & a == a and not x & b and y & c == c and not y & d]


def apply(state, i, option, accepts):
    new = list(state)
    new[2*i + int(not accepts)] |= option
    return tuple(new)


@lru_cache(maxsize=None)
def best(state, remaining):
    compatible = posterior(state)
    if not compatible:
        return 0, None
    if terminal(state):
        return sum(TOTALS[not bool(x & y)] for x, y in compatible), None
    if not remaining:
        return 0, None
    a, b, c, d = state
    options = ((i, 1 << o) for i in (0, 1) for o in range(OPTIONS)
               if not (1 << o) & (b | d | (a if i == 0 else c)))
    value, choice = 0, None
    for i, option in options:
        gain = sum(best(apply(state, i, option, accepts), remaining-1)[0] for accepts in (True, False))
        if gain > value:
            value, choice = gain, (i, option)
    return value, choice


def score(horizon):
    counts = Counter()
    for world, opening in states():
        state = opening
        rounds = 0
        while not terminal(state) and rounds < horizon:
            _, action = best(state, horizon-rounds)
            if action is None:
                break
            i, option = action
            state = apply(state, i, option, bool(world[i] & option))
            rounds += 1
        counts[(bool(world[0] & world[1]), rounds if terminal(state) else None)] += 1
    results = {name: {str(step): counts[agree, step] for step in (*range(horizon+1), None)}
               for agree, name in ((True, "agreement"), (False, "impasse"))}
    initial = {s for _, s in states()}
    expected = sum(best(s, horizon)[0] for s in initial)
    actual = sum(n * TOTALS[not agree] for (agree, i), n in counts.items() if i is not None)
    assert expected == actual
    return {"horizon": horizon, "score_by_step": results,
            "balanced_accuracy": actual / (2 * TOTALS[True] * TOTALS[False])}


if __name__ == "__main__":
    print(json.dumps({"primary": score(HORIZON),
                      "budget_curve": [score(k) for k in range(7)]}, indent=2))
