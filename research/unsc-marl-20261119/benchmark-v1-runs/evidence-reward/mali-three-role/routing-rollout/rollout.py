"""Improve a frozen policy using exact branch returns and its own continuations."""
from collections import Counter
from functools import cache
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import experiment as game

MODES = ("fixed", "learned", "greedy_rollout", "fixed_rollout", "rollout", "exact")


def policies(menu, belief_rates, tree):
    exact, _ = game.solver(menu, belief_rates)

    @cache
    def frozen(state, left):
        return game.select("learned", state, left, menu, belief_rates, exact, tree)

    def branches(state, left, role, continuation):
        chance = belief_rates[role]
        success = sum(continuation(game.write_bit(state, role, bit), left - 1) for bit in (0, 1)) / 2
        return chance * success + (1 - chance) * continuation(state, left - 1) - game.FEE

    @cache
    def baseline_value(base, state, left):
        role = (frozen(state, left) if base == "learned" else
                game.select(base, state, left, menu, belief_rates, exact, tree))
        if role is None:
            return game.terminal(menu, state)[1]

        def value(successor, budget):
            return baseline_value(base, successor, budget)

        return branches(state, left, role, value)

    @cache
    def improved(base, state, left):
        best = game.terminal(menu, state)[1]
        role = None
        def value_at(successor, budget):
            return baseline_value(base, successor, budget)

        if left:
            for i, bit in enumerate(state):
                if bit != -1:
                    continue
                value = branches(state, left, i, value_at)
                if value > best + game.TOL:
                    best, role = value, i
        return role

    def choose(mode, state, left):
        if mode in ("rollout", "greedy_rollout", "fixed_rollout"):
            base = "learned" if mode == "rollout" else mode.removesuffix("_rollout")
            return improved(base, state, left)
        if mode == "learned":
            return frozen(state, left)
        return game.select(mode, state, left, menu, belief_rates, exact, tree)

    def visited():
        return baseline_value.cache_info().currsize

    return choose, visited


def replay(menu, delivery, choose, mode, steps):
    def world_return(truth):
        target = game.terminal(menu, truth)[0]

        @cache
        def visit(state, left):
            role = choose(mode, state, left)
            if role is None:
                action, credit = game.terminal(menu, state)
                assert action == target or action == "UNRESOLVED"
                return credit, float(action == target), 0.
            assert left and state[role] == -1
            delivered = visit(game.write_bit(state, role, truth[role]), left - 1)
            dropped = visit(state, left - 1)
            rate = delivery[role]
            return tuple(rate * a + (1 - rate) * b + increment
                         for a, b, increment in zip(delivered, dropped, (0., 0., 1.), strict=True))

        return visit(game.EMPTY, steps)

    trial = [world_return(truth) for truth in game.WORLDS]
    credit, accuracy, questions = [sum(values) / len(trial) for values in zip(*trial, strict=True)]
    return {"net": credit - game.FEE * questions, "accuracy": accuracy,
            "questions": questions, "opening_desk": choose(mode, game.EMPTY, steps)}


def compare(menu, tree, true_rates, belief_rates, budget):
    choose, visited = policies(menu, belief_rates, tree)
    rows = {mode: replay(menu, true_rates, choose, mode, budget) for mode in MODES}
    return {"scores": rows, "cached_baseline_states": visited()}


def run():
    case_path = HERE.parent / "case.json"
    policy_path = HERE.parent / "experiment.json"
    menu = tuple(tuple(x) for x in game.read(case_path)["packages"].values())
    tree = game.read(policy_path)["learned_tree"]
    profiles = sorted({p for base in (*game.HELD, (.96, .57, .12)) for p in permutations(base)})
    verified = {}
    wins = Counter()
    regret = Counter()
    for rates in profiles:
        for budget in (1, 2, 3):
            row = compare(menu, tree, rates, rates, budget)
            results = row["scores"]
            net = {mode: item["net"] for mode, item in results.items()}
            assert net["rollout"] + game.TOL >= net["learned"]
            assert net["exact"] + game.TOL >= max(net.values())
            for mode, value in net.items():
                regret[mode] = max(regret[mode], net["exact"] - value)
            wins["beats_learned"] += net["rollout"] > net["learned"] + game.TOL
            for ablation in ("fixed_rollout", "greedy_rollout"):
                wins[f"beats_{ablation}"] += net["rollout"] > net[ablation] + game.TOL
                wins[f"loses_to_{ablation}"] += net["rollout"] + game.TOL < net[ablation]
            wins["ties_exact"] += abs(net["rollout"] - net["exact"]) <= game.TOL
            verified[f"{rates}/{budget}"] = row
    mismatch = {}
    for rates in game.HELD[1:]:
        weaker = min(range(3), key=rates.__getitem__)
        belief = tuple(.9 if i == weaker else p for i, p in enumerate(rates))
        for budget in (2, 3):
            mismatch[f"{rates}/{budget}"] = {"assumed_delivery": belief,
                **compare(menu, tree, rates, belief, budget)}
    fingerprints = (Path(__file__), HERE / "protocol.md", case_path, policy_path, HERE.parent / "experiment.py")
    return {"profiles": len(profiles), "conditions": len(verified), "rollout_comparisons": wins,
            "maximum_exact_regret": regret,
            "maximum_cached_baseline_states": max(row["cached_baseline_states"] for row in verified.values()),
            "matched_delivery": verified, "mismatched_delivery": mismatch,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in fingerprints}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
