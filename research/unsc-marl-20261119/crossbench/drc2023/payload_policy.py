"""Fit two decentralized extract selectors on the written-vote source task."""
from collections import defaultdict
from itertools import combinations, product
import json
from pathlib import Path

import numpy as np

import private_payload as channel
from receipt_feedback import optimizer, relay

HERE = Path(__file__).resolve().parent
PAIRS = tuple(combinations(range(4), 2))
WORLDS = tuple(product(PAIRS, repeat=2))
PEER = .8
CHAIR = .9
PEER_FEE = .25


def roster(label):
    weight = {}
    for world in WORLDS:
        common = len(set(world[0]) & set(world[1]))
        weight[world] = {"training": 1., "overlap": 2. ** common,
                         "split": 2. ** (2 - common)}[label]
    total = sum(weight.values())
    return {world: value / total for world, value in weight.items()}


def value(selected, focus):
    return 7 * len(selected) + 7 * len(selected & set(focus)) + 14 * (set(focus) <= selected)


def delivery(first, second):
    return ((frozenset(i for i, received in zip((first, second), flags, strict=True) if received),
             np.prod([CHAIR if received else 1 - CHAIR for received in flags]))
            for flags in product((False, True), repeat=2))


def expected(first, second, focus):
    return sum(prob * value(cards, focus) for cards, prob in delivery(first, second))


def train_paths():
    states, counts = {}, defaultdict(float)
    dimension = 0

    def action(key, choice):
        nonlocal dimension
        if key not in states:
            states[key] = dimension, 2
            dimension += 2
        return states[key][0] + choice

    for focus in PAIRS:
        for (left, right), world_p in roster("training").items():
            for i, first in enumerate(left):
                a = action(("sender", focus, left), i)
                for observation, seen_p in ((None, 1 - PEER), (first, PEER)):
                    for j, second in enumerate(right):
                        b = action(("recipient", focus, right, observation), j)
                        score = expected(first, second, focus)
                        counts[(a, b), score] += world_p * seen_p / len(PAIRS)
    traces = np.array([actions for actions, _ in counts], dtype=int)
    outcomes = np.array([(PEER_FEE, 0., score + 35, 2.) for _, score in counts], dtype=float)
    return states, traces, outcomes, {"design_mixture": np.array(list(counts.values()))}


def choose_probability(policies, who, focus, holding, observation=None):
    key = (who, focus, holding) if who == "sender" else (who, focus, holding, observation)
    return tuple(zip(holding, policies[key], strict=True))


def best_script(focus, prior, peer):
    """Optimize decentralized deterministic rules under the known tested prior."""
    best, policy = -1., None
    for opening in product((0, 1), repeat=len(PAIRS)):
        select_a = {holding: holding[i] for holding, i in zip(PAIRS, opening, strict=True)}
        payoff_b = defaultdict(lambda: [0., 0.])
        for (left, right), p in prior.items():
            first = select_a[left]
            for seen, chance in ((None, 1 - peer), (first, peer)):
                if not chance:
                    continue
                for i, second in enumerate(right):
                    payoff_b[right, seen][i] += p * chance * expected(first, second, focus)
        decision = {key: int(scores[1] > scores[0] + 1e-12) for key, scores in payoff_b.items()}
        points = sum(scores[decision[key]] for key, scores in payoff_b.items())
        if points > best + 1e-12:
            best = points
            policy = {("sender", focus, holding): tuple(float(i == selected) for i in holding)
                      for holding, selected in select_a.items()}
            policy.update({("recipient", focus, holding, seen): (float(i == 0), float(i == 1))
                           for (holding, seen), i in decision.items()})
    return best, policy


def greedy(focus):
    weights = {}
    for held in PAIRS:
        ranked = sorted(held, key=lambda j: (j not in focus, j))
        weights["sender", focus, held] = tuple(float(j == ranked[0]) for j in held)
        for seen in (None, *range(4)):
            pick = min(held, key=lambda j: (j == seen, j not in focus, j))
            weights["recipient", focus, held, seen] = tuple(float(j == pick) for j in held)
    return weights


def replay(weights, focus, prior, peer):
    out = defaultdict(float)
    for (left, right), p in prior.items():
        for first, a in choose_probability(weights, "sender", focus, left):
            for seen, link in ((None, 1 - peer), (first, peer)):
                if not link or not a:
                    continue
                for second, b in choose_probability(weights, "recipient", focus, right, seen):
                    mass = p * a * link * b
                    out["duplicate_attempts"] += mass * (first == second)
                    for cards, delivery_p in delivery(first, second):
                        m = mass * delivery_p
                        out["mass"] += m
                        out["expected_verified_cards"] += m * len(cards)
                        out["both_requested"] += m * (set(focus) <= cards)
                        out["score"] += m * value(cards, focus)
    assert abs(out.pop("mass") - 1.) < 1e-9
    out["net"] = out["score"] - (PEER_FEE if peer else 0.)
    return dict(out)


def observed_weights(states, vector):
    return {state: vector[start:start + width].tolist() for state, (start, width) in states.items()}


def run():
    # Reuse the verified accession of the original written-vote docket.
    relay.archive.load()
    states, paths, outcomes, mass = train_paths()
    history, trained = optimizer.fit(states, paths, outcomes, mass)
    learned = observed_weights(states, trained["joint_learned"])
    initial = observed_weights(states, trained["initial_uniform"])
    regimes = {}
    for label in ("training", "overlap", "split"):
        prior = roster(label)
        rows = []
        for focus in PAIRS:
            known, optimized = best_script(focus, prior, PEER)
            independent_score, independent = best_script(focus, prior, 0.)
            candidate = {
                "uniform": replay(initial, focus, prior, PEER),
                "learned": replay(learned, focus, prior, PEER),
                "learned_no_peer": replay(learned, focus, prior, 0.),
                "greedy": replay(greedy(focus), focus, prior, PEER),
                "best_independent": replay(independent, focus, prior, 0.),
                "best_interactive": replay(optimized, focus, prior, PEER),
            }
            assert abs(candidate["best_interactive"]["score"] - known) < 1e-9
            assert abs(candidate["best_independent"]["score"] - independent_score) < 1e-9
            assert known + 1e-9 >= max(row["score"] for row in candidate.values())
            rows.append({"focus": focus, "metrics": candidate})
        regimes[label] = {"cases": rows,
                          "mean": {name: {key: float(np.mean([r["metrics"][name][key] for r in rows]))
                                          for key in values}
                                   for name, values in rows[0]["metrics"].items()}}
    assert abs(regimes["training"]["mean"]["learned"]["net"] - history[-1]["record_reward"]) < 1e-9
    return {
        "scope": "One exact joint policy fit on the four written-vote source slots. The committee "
                 "requests a public pair, and each desk privately holds two candidate sources. "
                 "The verified endpoint scores available clauses, independent of prose generation.",
        "fit": history, "trajectory_rows": len(paths), "source_ids": relay.KEYS,
        "channels": {"peer": PEER, "chair": CHAIR, "peer_fee": PEER_FEE},
        "inventories": regimes,
        "policy": [{"state": key, "probabilities": p} for key, p in learned.items()],
        "pins": {path.name: channel.runner.digest(path) for path in (
            Path(__file__), Path(optimizer.__file__), Path(relay.archive.__file__),
            Path(relay.archive.__file__).with_name("task.json"))},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
