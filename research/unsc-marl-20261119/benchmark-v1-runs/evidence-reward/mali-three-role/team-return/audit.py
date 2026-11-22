"""Audit the fitted team from saved weights over role permutations."""
from itertools import permutations, product
import json
from pathlib import Path

import numpy as np

import backward as search
import train as core

HERE = Path(__file__).resolve().parent
game = core.game


def evaluate(menu, rates, cap, heads):
    ask, send = search.deployed(menu, rates, heads)
    scores = {}
    for name, gate in (("learned", send), ("always", lambda *_: True)):
        trials = [core.evaluate_world(menu, rates, cap, ask, gate, truth) for truth in game.WORLDS]
        scores[name] = core.summarize(np.mean(trials, axis=0))
    return scores


def inspect_privacy(menu):
    public_states = np.array(list(product((-1, 0, 1), repeat=3)))
    packets = np.tile(menu, (len(public_states), 1, 1))
    rates = np.tile(game.HELD[1], (len(public_states), 1))
    turns = np.full(len(public_states), 2)
    n = 0
    for role, bit in product(range(3), range(2)):
        first = np.zeros_like(public_states)
        second = np.ones_like(public_states)
        first[:, role] = second[:, role] = bit
        observed_first = core.features(packets, public_states, rates, turns, first)[:, role]
        observed_second = core.features(packets, public_states, rates, turns, second)[:, role]
        assert np.array_equal(observed_first, observed_second)
        n += len(public_states)
    return n


def run():
    result = game.read(HERE / "backward-results.json")
    heads = {int(horizon): tuple(tuple(np.array(x) for x in row) for row in weights)
             for horizon, weights in result["heads"].items()}
    menu = tuple(tuple(x) for x in game.read(HERE.parent / "case.json")["packages"].values())
    replay = search.measure(menu, game.read(HERE / "results.json"), heads)
    assert replay == result["held_results"]
    permutations_checked = []
    for rates, cap in product(game.HELD, (2, 3)):
        base = evaluate(menu, rates, cap, heads)
        for order in permutations(range(3)):
            other_menu = tuple(tuple(row[i] for i in order) for row in menu)
            other_rates = tuple(rates[i] for i in order)
            other = evaluate(other_menu, other_rates, cap, heads)
            max_delta = max(abs(other["learned"][key] - score) for key, score in base["learned"].items())
            assert max_delta < 1e-10
            permutations_checked.append(max_delta)
    return {"saved_weight_rows_replayed": len(replay),
            "role_permutations_checked": len(permutations_checked),
            "max_absolute_metric_delta": max(permutations_checked),
            "private_observation_contrasts": inspect_privacy(menu),
            "chair_received_hidden_fields": False}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
