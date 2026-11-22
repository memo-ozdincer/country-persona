"""Replay the frozen sent-grade policies on existing source-linked games."""
from itertools import permutations, product
import json
from statistics import mean

import numpy as np
import torch

import joint_opener as opener
import selective as s

base, shared = s.base, s.shared


def solve(data, peer):
    grid = data.grid
    left, right = map(len, grid.cards)
    receipts = s.original.suite.RECEIPTS
    points = np.zeros((left, len(base.ACTIONS), right, len(receipts), 3))
    fees = np.zeros((left, len(base.ACTIONS)))
    for (i, j), mass in data.prior.items():
        world = (i, j)
        for action, (column, send) in enumerate(base.ACTIONS):
            a = grid.claim(world, 0, column)
            fees[i, action] += mass * base.FEE * send
            for b_col in range(3):
                b = grid.claim(world, 1, b_col)
                truth = 0.
                for got_a, got_b in product((False, True), repeat=2):
                    view = (a if got_a else None, b if got_b else None)
                    prob = (base.DELIVER if got_a else 1-base.DELIVER) * (
                        base.DELIVER if got_b else 1-base.DELIVER)
                    truth += prob * bool(grid.information(view)[1])
                for seen, probability in base.observations(a, send):
                    points[i, action, j, receipts.index(seen), b_col] += mass*truth*probability
    openings = np.asarray(list(product(range(6) if peer else (0, 2, 4), repeat=left)))
    branches = points[np.arange(left), openings].sum(1)
    scores = branches.max(axis=-1).sum(axis=(1, 2)) - fees[np.arange(left), openings].sum(axis=1)
    ix = int(scores.argmax())
    move = dict(first_actions=openings[ix], second_actions=branches[ix].argmax(axis=-1))
    result = s.original.exact_policy(data, move)
    assert abs(result["net"] - scores[ix]) < 1e-9
    return result


def run():
    torch.set_num_threads(1)
    previous = s.read(s.FIT)
    adapted = s.read(s.HERE / "joint-opener.json")
    w = torch.tensor(previous["weights"], dtype=torch.float64)
    fit = np.asarray(adapted["weights"])
    results = {}
    for docket in ("mali", "myanmar"):
        conditions = []
        for order in permutations(range(3)):
            grid = shared.Grid(docket, order)
            data = s.original.data_for(grid)
            start = data.probabilities(w).numpy()
            table = opener.basis(data, data.prior, start)
            comparisons = {"exact-independent": solve(data, False), "exact-peer": solve(data, True),
                           "original": s.measure(data, start, base.FEE)}
            for arm in ("joint-uniform", "joint-fitted", "same-recipient-exact"):
                p = opener.choose(data, start, table, fit, base.FEE, arm)
                comparisons[arm] = s.measure(data, p, base.FEE)
            assert all(score["net"] <= comparisons["exact-peer"]["net"] + 1e-9 for score in comparisons.values())
            assert comparisons["joint-fitted"]["net"] <= comparisons["same-recipient-exact"]["net"] + 1e-9
            conditions.append(dict(order=grid.packages, metrics=comparisons))
        macro = {arm: {measure: mean(conds["metrics"][arm][measure] for conds in conditions)
                       for measure in ("net", "after_followup", "peer_rate")} for arm in comparisons}
        results[docket] = dict(mean=macro, orders=conditions)
    return results


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
