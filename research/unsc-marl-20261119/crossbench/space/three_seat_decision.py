"""Jointly learn which truthful grade to share in a three-seat compromise."""
from collections import defaultdict
from functools import lru_cache
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ftf2020"))
from adaptive_fit import fit, STEPS

# These are fictional workshop grades for three existing package texts.
PACKAGES = ("A", "D", "F")
CARDS_A = ((3, 2, 0), (1, 2, 3), (0, 0, 2))
CARDS_B = ((1, 2, 0), (3, 1, 2), (3, 1, 0))
PUBLIC = (3, 2, 3)
WORLDS = tuple(product(range(len(CARDS_A)), range(len(CARDS_B))))
ACTIONS = tuple(product(range(len(PACKAGES)), (False, True)))
DELIVER = .9
PEER = .8
FEE = .03


def winner(a, b):
    values = [(min(g), sum(g)) if min(g) > 0 else (0, 0)
              for g in zip(a, b, PUBLIC, strict=True)]
    best = max(values)
    if best == (0, 0):
        return frozenset({"impasse"})
    return frozenset(PACKAGES[i] for i, value in enumerate(values) if value == best)


TRUTH = {world: winner(CARDS_A[world[0]], CARDS_B[world[1]]) for world in WORLDS}


@lru_cache(None)
def verify(first, second):
    possible = {world for world in WORLDS
                if (first is None or CARDS_A[world[0]][first[0]] == first[1])
                and (second is None or CARDS_B[world[1]][second[0]] == second[1])}
    assert possible
    return tuple(sorted(possible)), frozenset.intersection(*(TRUTH[world] for world in possible))


def prior(kind):
    count = sum("impasse" in options for options in TRUTH.values())
    weights = {}
    for world in WORLDS:
        if kind == "balanced":
            weights[world] = .5 / (count if "impasse" in TRUTH[world] else len(WORLDS) - count)
        elif kind == "uniform":
            weights[world] = 1.
        elif kind == "correlated":
            weights[world] = 4. if world[0] == world[1] else 1.
    z = sum(weights.values())
    return {world: w / z for world, w in weights.items()}


def message(world, seat, i):
    card = CARDS_A if seat == 0 else CARDS_B
    return i, card[world[seat]][i]


def observations(first, pay):
    return ((None, 1 - PEER), (first, PEER)) if pay else ((None, 1.),)


@lru_cache(None)
def decisions(first, second):
    states = []
    for success_a, success_b in product((False, True), repeat=2):
        shown = (first if success_a else None, second if success_b else None)
        p = (DELIVER if success_a else 1 - DELIVER) * (DELIVER if success_b else 1 - DELIVER)
        possible, warranted = verify(*shown)
        states.append((p, shown, possible, warranted))
    return tuple(states)


def earn(first, second):
    return sum(mass for mass, _, _, warranted in decisions(first, second) if warranted)


def compile_train():
    states = {}
    spec = defaultdict(float)
    width = 0

    def action(state, item, options):
        nonlocal width
        if state not in states:
            states[state] = width, options
            width += options
        return states[state][0] + item

    for world, p in prior("balanced").items():
        for i, (column, pay) in enumerate(ACTIONS):
            first = message(world, 0, column)
            a = action(("first", world[0]), i, len(ACTIONS))
            for seen, chance in observations(first, pay):
                for slot in range(len(PACKAGES)):
                    b = action(("second", world[1], seen), slot, len(PACKAGES))
                    gain = earn(first, message(world, 1, slot))
                    spec[(a, b), gain, pay] += p * chance
    choices = np.array([path for path, _, _ in spec])
    outcomes = np.array([(FEE * pay, 0., 35. + gain, 2.) for _, gain, pay in spec])
    return states, choices, outcomes, {"design_mixture": np.array(list(spec.values()))}


def onehot(choice, count):
    return tuple(float(i == choice) for i in range(count))


def optimal(roster, allow_peer):
    best, solution = -1., {}
    menu = range(len(ACTIONS)) if allow_peer else range(0, len(ACTIONS), 2)
    for opening in product(menu, repeat=len(CARDS_A)):
        response = defaultdict(lambda: [0.] * len(PACKAGES))
        charges = 0.
        for world, p in roster.items():
            col, pay = ACTIONS[opening[world[0]]]
            first = message(world, 0, col)
            charges += p * FEE * pay
            for seen, chance in observations(first, pay):
                for slot in range(len(PACKAGES)):
                    response[world[1], seen][slot] += p * chance * earn(first, message(world, 1, slot))
        picks = {key: int(np.argmax(scores)) for key, scores in response.items()}
        value = sum(response[key][slot] for key, slot in picks.items()) - charges
        if value > best + 1e-12:
            best = value
            solution = {("first", j): onehot(col, len(ACTIONS)) for j, col in enumerate(opening)}
            solution.update({("second", *key): onehot(slot, len(PACKAGES)) for key, slot in picks.items()})
    return best, solution


def first_priority():
    def first_best(card):
        return max(range(len(card)), key=card.__getitem__)

    return {("first", i): onehot(2 * first_best(card) + 1, len(ACTIONS)) for i, card in enumerate(CARDS_A)} | {
        ("second", j, obs): onehot(first_best(card), len(PACKAGES))
        for j, card in enumerate(CARDS_B) for obs in (None, *((h, x) for h in range(3) for x in range(4)))}


def replay(weights, roster, erase=False):
    totals = defaultdict(float)
    by_world = {}
    trace = []
    for world, p in roster.items():
        is_impasse = "impasse" in TRUTH[world]
        mass_certified = 0.
        totals["impasse_mass"] += p * is_impasse
        for (col, pay), a in zip(ACTIONS, weights["first", world[0]], strict=True):
            if not a:
                continue
            first = message(world, 0, col)
            totals["peer_sends"] += p * a * pay
            mass_a = DELIVER * bool(verify(first, None)[1])
            totals["warrant_after_first"] += p * a * mass_a
            for seen, chance in observations(first, pay):
                local = weights["second", world[1], None if erase else seen]
                for slot, b in enumerate(local):
                    if not b:
                        continue
                    second = message(world, 1, slot)
                    for delivered, receipts, possible, certified in decisions(first, second):
                        local_mass = a * chance * b * delivered
                        m = p * local_mass
                        assert world in possible and certified <= TRUTH[world]
                        totals["mass"] += m
                        totals["agreement"] += m * bool(certified) * (not is_impasse)
                        totals["impasse"] += m * bool(certified) * is_impasse
                        mass_certified += local_mass * bool(certified)
                        trace.append({"world": world, "receipts": receipts, "possible": possible,
                                      "warranted": sorted(certified), "mass": m, "peer_paid": pay})
        by_world[world] = mass_certified
    assert abs(totals.pop("mass") - 1.) < 1e-9
    totals["net"] = totals["agreement"] + totals["impasse"] - FEE * totals["peer_sends"]
    totals["agreement_rate"] = totals["agreement"] / (1 - totals["impasse_mass"])
    totals["impasse_rate"] = totals["impasse"] / totals["impasse_mass"]
    return dict(totals), by_world, trace


def run():
    case = json.loads((HERE / "case.json").read_text())
    menu = {card["id"]: card for card in case["options"] if card["id"] in PACKAGES}
    assert list(menu) == list(PACKAGES)
    states, paths, outcomes, mass = compile_train()
    history, fitted = fit(states, paths, outcomes, mass)
    learned = {key: fitted["joint_learned"][start:start + size].tolist() for key, (start, size) in states.items()}
    projections = {}
    retained_trace = None
    frozen_script = optimal(prior("balanced"), True)[1]
    for kind in ("balanced", "uniform", "correlated"):
        roster = prior(kind)
        upper, oracle = optimal(roster, True)
        floor, independent = optimal(roster, False)
        options = {"learned": (learned, False), "learned_peer_masked": (learned, True),
                   "frozen_balanced_script": (frozen_script, False), "known_prior_script": (oracle, False),
                   "known_prior_independent": (independent, False), "top_grade": (first_priority(), False)}
        projection = {}
        for name, (weights, erase) in options.items():
            totals, per_world, trace = replay(weights, roster, erase)
            projection[name] = totals | {"by_world": [{"world": world, "certified": prob}
                                                       for world, prob in per_world.items()]}
            if kind == "balanced" and name == "learned":
                retained_trace = trace
        assert abs(projection["known_prior_script"]["net"] - upper) < 1e-9
        assert abs(projection["known_prior_independent"]["net"] - floor) < 1e-9
        assert all(upper + 1e-9 >= p["net"] for p in projection.values())
        projections[kind] = projection
    assert abs(projections["balanced"]["learned"]["net"] - history[-1]["record_reward"]) < 1e-9
    bounds = []
    for world, true in TRUTH.items():
        pairs = [(i, j) for i, j in product(range(3), repeat=2)
                 if verify(message(world, 0, i), message(world, 1, j))[1]]
        bounds.append({"world": world, "best": sorted(true), "certificate_columns": pairs})
    return {"scope": "Fictional three-seat grades on three outer-space workshop packages. "
                     "A decision requires a common winning disposition across every completion of received "
                     "truthful grades. A learned message action itself conveys no inferred hidden preference. "
                     "Both emitting seats are fitted jointly. The public third seat and verifier are fixed.",
            "packages": menu, "public_grades": PUBLIC, "public_domains": [CARDS_A, CARDS_B],
            "links": {"to_chair": DELIVER, "peer": PEER, "peer_fee": FEE},
            "steps": STEPS, "trajectory_rows": len(paths), "learning": history,
            "capacity": bounds, "results": projections,
            "learned_policy": [{"state": key, "probabilities": values} for key, values in learned.items()],
            "balanced_traces": retained_trace}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
