"""Fit a chair and two delegates with one paid request for another grade."""
from collections import defaultdict
from functools import lru_cache
from itertools import product
import json
from pathlib import Path

import numpy as np

import three_seat_decision as base

HERE = Path(__file__).resolve().parent
FEE = .08
REPLY = base.DELIVER ** 2
QUESTIONS = tuple(product(range(2), range(len(base.PACKAGES))))


@lru_cache(None)
def actions(receipts):
    return (None, *(q for q in QUESTIONS if receipts[q[0]] is None or receipts[q[0]][0] != q[1]))


@lru_cache(None)
def next_evidence(receipts, question, grade):
    possible, _ = base.verify(*receipts)
    survivors = [world for world in possible if base.message(world, *question)[1] == grade]
    assert survivors
    winners = frozenset.intersection(*(base.TRUTH[world] for world in survivors))
    return tuple(survivors), winners


@lru_cache(None)
def q_gain(world, receipts, q):
    _, prior = base.verify(*receipts)
    if prior:
        return 1.
    if q is None:
        return 0.
    received = base.message(world, *q)[1]
    _, possible = next_evidence(receipts, q, received)
    return REPLY * bool(possible)


def events(weights, roster):
    for world, p in roster.items():
        for i, a in enumerate(weights["first", world[0]]):
            if not a:
                continue
            col, paid = base.ACTIONS[i]
            first = base.message(world, 0, col)
            for seen, chance in base.observations(first, paid):
                for j, b in enumerate(weights["second", world[1], seen]):
                    if not b:
                        continue
                    second = base.message(world, 1, j)
                    for delivered, receipts, possible, certified in base.decisions(first, second):
                        assert world in possible and certified <= base.TRUTH[world]
                        yield p * a * chance * b * delivered, world, receipts, paid, bool(certified)


def build():
    states, paths = {}, defaultdict(float)
    offset = 0

    def add(key, size, choice):
        nonlocal offset
        if key not in states:
            states[key] = offset, size
            offset += size
        return states[key][0] + choice

    for world, p in base.prior("balanced").items():
        for i, (pos, paid) in enumerate(base.ACTIONS):
            first = base.message(world, 0, pos)
            a = add(("first", world[0]), len(base.ACTIONS), i)
            for seen, chance in base.observations(first, paid):
                for j in range(len(base.PACKAGES)):
                    second = base.message(world, 1, j)
                    b = add(("second", world[1], seen), len(base.PACKAGES), j)
                    for mass, receipts, _, certified in base.decisions(first, second):
                        if certified:
                            paths[(a, b, -1), base.FEE * paid, 1.] += p * chance * mass
                            continue
                        menu = actions(receipts)
                        for k, q in enumerate(menu):
                            c = add(("chair", receipts), len(menu), k)
                            cost = base.FEE * paid + FEE * (q is not None)
                            paths[(a, b, c), cost, q_gain(world, receipts, q)] += p * chance * mass
    ids = np.array([path for path, _, _ in paths])
    outcomes = np.array([(cost, 0., 35. + gain, 2.) for _, cost, gain in paths])
    return states, ids, outcomes, {"design_mixture": np.array(list(paths.values()))}


def optimize_chair(fixed, roster):
    scores = defaultdict(list)
    for mass, world, shown, _, certified in events(fixed, roster):
        if certified:
            continue
        menu = actions(shown)
        if not scores[shown]:
            scores[shown] = [0.] * len(menu)
        for k, q in enumerate(menu):
            scores[shown][k] += mass * (q_gain(world, shown, q) - FEE * (q is not None))
    return {("chair", shown): base.onehot(int(np.argmax(values)), len(values))
            for shown, values in scores.items()}


def chair_moves(chair, shown, certified):
    if certified:
        return ((None, 1.),)
    menu = actions(shown)
    return tuple(zip(menu, chair.get(("chair", shown), base.onehot(0, len(menu))), strict=True))


def replay(emitters, chair, roster):
    outcome = defaultdict(float)
    per_world = defaultdict(float)
    hist = defaultdict(lambda: [0., 0.])
    for mass, world, shown, paid, ready in events(emitters, roster):
        outcome["mass"] += mass
        outcome["peer_rate"] += mass * paid
        outcome["before_question"] += mass * ready
        for q, probability in chair_moves(chair, shown, ready):
            if not probability:
                continue
            weight = mass * probability
            gain = q_gain(world, shown, q)
            cost = FEE * (q is not None)
            per_world[world] += weight * gain / roster[world]
            outcome["net"] += weight * (gain - cost - base.FEE * paid)
            outcome["requests"] += weight * (q is not None)
            outcome["agreement"] += weight * gain * ("impasse" not in base.TRUTH[world])
            outcome["impasse"] += weight * gain * ("impasse" in base.TRUTH[world])
            if q is not None:
                hist[shown][0] += weight
                hist[shown][1] += weight * gain
    assert abs(outcome.pop("mass") - 1.) < 1e-9
    impasse_mass = sum(p for world, p in roster.items() if "impasse" in base.TRUTH[world])
    outcome["agreement_rate"] = outcome["agreement"] / (1 - impasse_mass)
    outcome["impasse_rate"] = outcome["impasse"] / impasse_mass
    outcome["added_by_question"] = outcome["agreement"] + outcome["impasse"] - outcome["before_question"]
    return dict(outcome) | {
        "worlds": [{"world": world, "certified": probability} for world, probability in per_world.items()],
        "queried_views": [{"receipts": shown, "mass": row[0], "successful_certification_mass": row[1]}
                          for shown, row in hist.items()],
    }


def best_response(fixed, chair, roster, seat):
    openings = {key: values for key, values in fixed.items() if key[0] in ("first", "second")}
    moves = defaultdict(lambda: np.zeros(len(base.ACTIONS) if seat == "first" else len(base.PACKAGES)))
    for world, p in roster.items():
        first_key = ("first", world[0])
        first_probs = np.ones(len(base.ACTIONS)) if seat == "first" else openings[first_key]
        for i, ((pos, paid), a) in enumerate(zip(base.ACTIONS, first_probs, strict=True)):
            if not a:
                continue
            first = base.message(world, 0, pos)
            for seen, chance in base.observations(first, paid):
                second_key = ("second", world[1], seen)
                second_probs = np.ones(len(base.PACKAGES)) if seat == "second" else openings[second_key]
                for j, b in enumerate(second_probs):
                    if not b:
                        continue
                    second = base.message(world, 1, j)
                    mass = p * a * b * chance
                    for delivered, shown, _, certified in base.decisions(first, second):
                        gain = sum(qp * (q_gain(world, shown, q) - FEE * (q is not None))
                                   for q, qp in chair_moves(chair, shown, bool(certified)))
                        key, choice = (first_key, i) if seat == "first" else (second_key, j)
                        moves[key][choice] += mass * delivered * (gain - base.FEE * paid)
    openings.update({key: base.onehot(int(np.argmax(values)), len(values)) for key, values in moves.items()})
    return openings


def scripted(frozen, roster):
    # Initialize unseen second-seat states so first-seat alternatives can be evaluated.
    second_defaults = {("second", j, seen): base.onehot(0, len(base.PACKAGES))
                       for j in range(len(base.CARDS_B))
                       for seen in (None, *(base.message(world, 0, i) for world in base.WORLDS
                                            for i in range(len(base.PACKAGES))))}
    emitters = second_defaults | frozen
    chair = optimize_chair(emitters, roster)
    gain = replay(emitters, chair, roster)["net"]
    for _ in range(3):
        for role in ("second", "first"):
            emitters = best_response(emitters, chair, roster, role)
            chair = optimize_chair(emitters, roster)
            current = replay(emitters, chair, roster)["net"]
            assert current + 1e-9 >= gain
            gain = current
    return emitters, chair


def capacity():
    witnesses = []
    for world in base.WORLDS:
        candidates = []
        sufficient_starts = 0
        for i, j in product(range(len(base.PACKAGES)), repeat=2):
            shown = (base.message(world, 0, i), base.message(world, 1, j))
            _, sufficient = base.verify(*shown)
            sufficient_starts += bool(sufficient)
            for question in actions(shown):
                if sufficient or question is None:
                    continue
                answer = base.message(world, *question)[1]
                remaining, warranted = next_evidence(shown, question, answer)
                if warranted:
                    candidates.append({"receipts": shown, "extra": question, "answer": answer,
                                       "remaining_worlds": remaining, "certified": sorted(warranted)})
        assert sufficient_starts or candidates
        witnesses.append({"world": world, "sufficient_opening_pairs": sufficient_starts,
                          "newly_sufficient_examples": candidates})
    return witnesses


def run():
    states, ids, outcomes, mass = build()
    history, fitted = base.fit(states, ids, outcomes, mass)
    learned = {key: fitted["joint_learned"][start:start + size].tolist() for key, (start, size) in states.items()}
    trained_emitters = {key: value for key, value in learned.items() if key[0] != "chair"}
    trained_chair = {key: value for key, value in learned.items() if key[0] == "chair"}
    previous = json.loads((HERE / "evidence/three-seat-decision.json").read_text())

    def immutable(key):
        return tuple(map(immutable, key)) if isinstance(key, list) else key
    frozen = {immutable(row["state"]): row["probabilities"] for row in previous["learned_policy"]}
    frozen_script = scripted(frozen, base.prior("balanced"))
    results = {}
    for label in ("balanced", "uniform", "correlated"):
        roster = base.prior(label)
        shifted_script = scripted(frozen, roster)
        systems = {
            "prior_emitters_without_followup": (frozen, {}),
            "prior_emitters_with_optimal_chair": (frozen, optimize_chair(frozen, roster)),
            "joint_without_followup": (trained_emitters, {}),
            "joint": (trained_emitters, trained_chair),
            "joint_with_optimal_chair": (trained_emitters, optimize_chair(trained_emitters, roster)),
            "frozen_balanced_script": frozen_script,
            "adapted_script": shifted_script,
        }
        results[label] = {name: replay(em, chair, roster) for name, (em, chair) in systems.items()}
        prior_result = previous["results"][label]["learned"]["net"]
        assert abs(results[label]["prior_emitters_without_followup"]["net"] - prior_result) < 1e-9
        assert results[label]["joint_with_optimal_chair"]["net"] + 1e-9 >= results[label]["joint"]["net"]
    assert abs(results["balanced"]["joint"]["net"] - history[-1]["record_reward"]) < 1e-9
    return {
        "scope": "One exact three-policy fit on the existing authored world grid. A chair can pay "
                 "for one additional truthful grade, with independently lossy request and reply. "
                 "Known-prior chair optimization is exact for fixed emitters. "
                 "The alternating joint script is a baseline, without a global optimality claim.",
        "fee": FEE, "reply_success": REPLY, "steps": base.STEPS, "trajectory_rows": len(ids),
        "history": history, "capacity": capacity(), "results": results,
        "policy": [{"state": state, "probabilities": values} for state, values in learned.items()],
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
