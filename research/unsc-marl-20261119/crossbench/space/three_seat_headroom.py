"""Bound how much a better disclosure policy could improve each workshop."""
from collections import defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import three_seat_residual as residual

HERE = Path(__file__).resolve().parent
transfer = residual.transfer
protocol = transfer.protocol
base = transfer.base
FIT = HERE / "evidence/three-seat-residual.json"


def receipt_events(grid, world, i, j):
    first, second = (grid.claim(world, 0, i), grid.claim(world, 1, j))
    events = []
    for got_a, got_b in product((False, True), repeat=2):
        view = (first if got_a else None, second if got_b else None)
        mass = (base.DELIVER if got_a else 1 - base.DELIVER) * (
            base.DELIVER if got_b else 1 - base.DELIVER)
        _, supported = grid.information(view)
        if supported:
            events.append((mass, view, np.array([1.])))
            continue
        choices = [0.]
        for ask in protocol.actions(view)[1:]:
            grade = grid.claim(world, *ask)[1]
            certifies = grid.information(view, (*ask, grade))[1]
            choices.append(protocol.REPLY * bool(certifies) - protocol.FEE)
        events.append((mass, view, np.array(choices)))
    return events


def exact_independent(grid, balanced=False):
    roster = grid.prior(balanced)
    facts = {(world, i, j): receipt_events(grid, world, i, j)
             for world in grid.worlds for i, j in product(range(3), repeat=2)}
    best = -1.
    winning = None
    n = 0
    for left in product(range(3), repeat=len(grid.cards[0])):
        for right in product(range(3), repeat=len(grid.cards[1])):
            n += 1
            questions = {}
            for world, mass in roster.items():
                for amount, view, rewards in facts[world, left[world[0]], right[world[1]]]:
                    earned = amount * mass * rewards
                    if view in questions:
                        questions[view] += earned
                    else:
                        questions[view] = earned
            value = sum(totals.max() for totals in questions.values())
            if value > best + 1e-12:
                best = value
                winning = {"left_grade_columns": left, "right_grade_columns": right,
                           "chair": [{"received": view, "query": None if len(reward) == 1 else
                                      protocol.actions(view)[int(np.argmax(reward))]}
                                     for view, reward in questions.items()]}
    clairvoyant = defaultdict(float)
    for world, mass in roster.items():
        most = max(sum(p * rewards.max() for p, _, rewards in facts[world, i, j])
                   for i, j in product(range(3), repeat=2))
        clairvoyant[world] = mass * most
    assert winning is not None
    check = transfer.Experiment(grid, balanced)
    weights = np.zeros((len(check.states), transfer.MAX_ACTIONS))
    recorded_chair = {row["received"]: row["query"] for row in winning["chair"]}
    for state, index in check.states.items():
        if state[0] == "A":
            choice = 2 * winning["left_grade_columns"][state[1]]
        elif state[0] == "B":
            choice = winning["right_grade_columns"][state[1]]
        else:
            choice = protocol.actions(state[1]).index(recorded_chair.get(state[1]))
        weights[index, choice] = 1.
    actual = check.metrics(weights)
    assert abs(actual["net"] - best) < 1e-9
    return {"best_independent_net": float(best), "independent_openings_enumerated": n,
            "attaining_policy": winning, "exact_attaining_replay": actual,
            "any_protocol_upper_bound": float(sum(clairvoyant.values()))}


def run():
    old = json.loads(FIT.read_text())
    cases = residual.fixture_cases()
    result = {}
    with patch.dict(transfer.FIXTURES, cases):
        for name, values in old["targets"].items():
            grid = transfer.Grid(name)
            measured = exact_independent(grid)
            scripted = values["scores"]["script"]["net"]
            assert scripted <= measured["best_independent_net"] + 1e-9
            assert measured["best_independent_net"] <= measured["any_protocol_upper_bound"] + 1e-9
            result[name] = measured | {
                "measured_public_script": scripted,
                "learned_anchored": values["scores"]["anchored_learned"]["net"],
                "independent_headroom_over_script": measured["best_independent_net"] - scripted,
                "optimistic_headroom_over_script": measured["any_protocol_upper_bound"] - scripted,
            }
    positive = exact_independent(transfer.Grid("space"), True)
    previous = json.loads((HERE / "evidence/three-seat-followup.json").read_text())
    scored_peer = previous["results"]["balanced"]["frozen_balanced_script"]["net"]
    positive["attained_with_peer"] = scored_peer
    positive["attained_gain_over_best_independent"] = scored_peer - positive["best_independent_net"]
    return {"scope": "A known-prior deterministic opening and exact chair comparison with no emitter peer hop. "
                     "The optimistic upper bound is allowed to know the hidden world when selecting both "
                     "openings and the follow-up, but the verifier still requires the same visible evidence. "
                     "No additional training occurs.",
            "results": result, "earlier_outer_space_reference": positive,
            "residual_results_sha256": sha256(FIT.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
