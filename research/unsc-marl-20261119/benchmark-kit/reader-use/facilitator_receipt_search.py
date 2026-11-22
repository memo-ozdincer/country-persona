"""Bounded search over first-desk choices using a relaxed second-desk payoff."""
import numpy as np


def maximize(payoff):
    """Return the exact two-desk optimum up to floating point tolerance.

    Each unfinished first-desk state may use a different action for every
    second-desk state and action in the upper bound. Any actual first-desk
    table is among the choices this relaxation permits.
    """
    order = np.argsort(-np.ptp(payoff, axis=1).sum(axis=(1, 2)), kind="stable")
    ordered = payoff[order]
    first_states, _, second_states, second_actions = ordered.shape
    suffix = np.zeros((first_states + 1, second_states, second_actions))
    for i in range(first_states - 1, -1, -1):
        suffix[i] = suffix[i + 1] + ordered[i].max(axis=0)

    best = float(ordered[:, 0].sum(axis=0).max(axis=1).sum())
    visited = leaves = pruned = 0
    tolerance = 1e-12

    def explore(depth, partial):
        nonlocal best, visited, leaves, pruned
        visited += 1
        if depth == first_states:
            leaves += 1
            best = max(best, float(partial.max(axis=1).sum()))
            return
        branches = partial + ordered[depth]
        relaxed = branches + suffix[depth + 1]
        bounds = relaxed.max(axis=2).sum(axis=1)
        for option in np.argsort(-bounds, kind="stable"):
            if bounds[option] <= best + tolerance:
                pruned += 1
                continue
            explore(depth + 1, branches[option])

    explore(0, np.zeros_like(suffix[0]))
    return {"exact_net": best, "first_states": first_states, "second_states": second_states,
            "nodes": visited, "fully_scored_tables": leaves, "pruned_subtrees": pruned,
            "tolerance": tolerance}


def check():
    from itertools import product

    random = np.random.default_rng(144)
    for shape in ((1, 3, 3, 3), (3, 3, 4, 3), (5, 3, 6, 3)):
        for _ in range(8):
            payoff = random.normal(size=shape)
            first, actions, _, _ = payoff.shape
            exact = max(payoff[np.arange(first), table].sum(axis=0).max(axis=1).sum()
                        for table in product(range(actions), repeat=first))
            assert abs(maximize(payoff)["exact_net"] - exact) < 1e-10
