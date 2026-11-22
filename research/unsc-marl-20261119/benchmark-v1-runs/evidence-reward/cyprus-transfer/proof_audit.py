"""Check rendered exclusions and compare frozen policy controls over all worlds."""
from itertools import product
import json

import numpy as np

import transfer as t
from train import evaluate_world, summarize

game = t.game


def run():
    case, menu, ask, gate = t.setup()

    def always(*_):
        return True

    def no_communication(*_):
        return None

    def fixed(state, _):
        return next((i for i, bit in enumerate(state) if bit < 0), None)

    for state in product((-1, 0, 1), repeat=3):
        exclusion_text, received_options = t.proof(case, state).split("Compatible options after applying confirmed requirements: ")
        kept = set(case["packages"])
        for clause in exclusion_text.strip().split(". "):
            if clause:
                desk, exclusions = clause.rstrip(".").split(" excludes ")
                i = next(i for i, role in enumerate(case["roles"]) if role["name"] == desk)
                assert state[i] >= 0
                said = set(exclusions.split(", "))
                assert said == {k for k, values in case["packages"].items() if values[i] != state[i]}
                kept.difference_update(said)
        assert kept == {list(case["packages"])[menu.index(option)] for option in game.options(menu, state)}
        assert received_options == (", ".join(k for k in case["packages"] if k in kept) if kept else "none") + "."
    results = {}
    for budget in (2, 3):
        arms = {}
        for label, chair, responder in (("joint", ask, gate), ("always_reply", ask, always),
                                         ("fixed", fixed, always), ("silent", no_communication, always)):
            values = [evaluate_world(menu, t.RATES, budget, chair, responder, world) for world in game.WORLDS]
            arms[label] = summarize(np.mean(values, axis=0))
        results[budget] = arms
    return {"verified_public_states": 27, "modeled_evaluation": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
