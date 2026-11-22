"""Learn when to pay to expose the first excerpt to the second desk."""
from collections import defaultdict
from functools import lru_cache
from itertools import product
import json
from pathlib import Path

import numpy as np

import payload_policy as base
import payload_writer_contract_score as synthesis

HERE = Path(__file__).resolve().parent
FEES = (.25, 1.5, 4.)
ACTIONS = tuple(product((0, 1), (False, True)))
OBSERVATIONS = (None, *range(4))
OPENINGS = np.array(list(product(range(len(ACTIONS)), repeat=len(base.PAIRS))), dtype=int)
TABLE_PATH = HERE / "payload-writer-contract-evidence/results.json"
PARENT_POLICY = HERE / "evidence/payload-policy.json"


@lru_cache(None)
def outcome(first, second):
    return tuple(base.delivery(first, second))


@lru_cache(None)
def payoff(first, second, focus):
    return sum(p * base.value(held, focus) for held, p in outcome(first, second))


def peer_events(first, pay):
    if pay:
        return ((None, 1 - base.PEER), (first, base.PEER))
    return ((None, 1.),)


def train_paths():
    states, paths = {}, defaultdict(float)
    dim = 0

    def action(key, choice, count):
        nonlocal dim
        if key not in states:
            states[key] = dim, count
            dim += count
        return states[key][0] + choice

    for fee, focus in product(FEES, base.PAIRS):
        for (left, right), mass in base.roster("training").items():
            for i, (select, pay) in enumerate(ACTIONS):
                first = left[select]
                a = action(("sender", fee, focus, left), i, len(ACTIONS))
                for observed, chance in peer_events(first, pay):
                    for j, second in enumerate(right):
                        b = action(("recipient", fee, focus, right, observed), j, 2)
                        points = payoff(first, second, focus)
                        paths[(a, b), fee * pay, points] += mass * chance / (len(FEES) * len(base.PAIRS))
    ids = np.array([actions for actions, _, _ in paths], dtype=int)
    outcomes = np.array([(cost, 0, score + 35, 2) for _, cost, score in paths])
    return states, ids, outcomes, {"design_mixture": np.array(list(paths.values()))}


def exact_script(focus, prior, fee):
    """Maximize over all first-desk strategies and best local replies."""
    groups = len(base.PAIRS)
    contributions = np.zeros((groups, len(ACTIONS), groups, len(OBSERVATIONS), 2))
    charges = np.zeros((groups, len(ACTIONS)))
    for i, left in enumerate(base.PAIRS):
        for j, right in enumerate(base.PAIRS):
            mass = prior[left, right]
            for q, (choice, pay) in enumerate(ACTIONS):
                first = left[choice]
                charges[i, q] += mass * fee * pay
                for observed, chance in peer_events(first, pay):
                    k = OBSERVATIONS.index(observed)
                    contributions[i, q, j, k] += [
                        mass * chance * payoff(first, second, focus) for second in right]
    masses = contributions[np.arange(groups), OPENINGS].sum(axis=1)
    costs = charges[np.arange(groups), OPENINGS].sum(axis=1)
    totals = masses.max(axis=-1).sum(axis=(1, 2)) - costs
    best = int(np.argmax(totals))
    chosen = OPENINGS[best]
    reply = masses[best].argmax(axis=-1)
    weights = {("sender", fee, focus, holding): one_hot(int(choice), len(ACTIONS))
               for holding, choice in zip(base.PAIRS, chosen, strict=True)}
    weights.update({("recipient", fee, focus, holding, seen): one_hot(int(reply[j, k]), 2)
                    for j, holding in enumerate(base.PAIRS) for k, seen in enumerate(OBSERVATIONS)})
    return float(totals[best]), weights


def one_hot(index, count):
    return tuple(float(index == i) for i in range(count))


def lift(weights, focus, fee, pay):
    """Adapt earlier always-send or independent rules to the same action API."""
    result = {}
    for (who, target, *state), prob in weights.items():
        if target != focus:
            continue
        if who == "sender":
            prob = [prob[i] if flag == pay else 0. for i, flag in ACTIONS]
        result[who, fee, focus, *state] = prob
    return result


def restore(path):
    def freeze(obj):
        return tuple(map(freeze, obj)) if isinstance(obj, list) else obj

    saved = json.loads(path.read_text())
    return {freeze(row["state"]): row["probabilities"] for row in saved["policy"]}


def replay(weights, fee, focus, prior, writer, blind=False):
    out = defaultdict(float)
    for (left, right), p in prior.items():
        for (i, pay), a in zip(ACTIONS, weights["sender", fee, focus, left], strict=True):
            if not a:
                continue
            first = left[i]
            for seen, chance in peer_events(first, pay):
                seen = None if blind else seen
                for second, b in zip(right, weights["recipient", fee, focus, right, seen], strict=True):
                    if not b:
                        continue
                    mass = p * a * chance * b
                    out["peer_attempt_rate"] += mass * pay
                    out["duplicate_rate"] += mass * (first == second)
                    for held, delivered in outcome(first, second):
                        m = mass * delivered
                        reviewed = writer[held]["separate_clause_writer"]
                        out["mass"] += m
                        out["delivery_net"] += m * (base.value(held, focus) - fee * pay)
                        exact = {synthesis.contract.previous.SOURCE_IDS.index(key) for key in reviewed["exact_fields"]}
                        out["record_net"] += m * (base.value(exact, focus) - fee * pay)
                        out["preserved_facts"] += m * len(reviewed["facts"])
                        out["both_requested"] += m * (set(focus) <= held)
    assert abs(out.pop("mass") - 1.) < 1e-9
    return dict(out)


def run():
    states, paths, outcomes, mass = train_paths()
    history, fitted = base.optimizer.fit(states, paths, outcomes, mass)
    learned = base.observed_weights(states, fitted["joint_learned"])
    baseline = restore(PARENT_POLICY)
    source_ids = synthesis.contract.previous.SOURCE_IDS
    writer = {}
    for key, table in json.loads(TABLE_PATH.read_text())["terminal_records"].items():
        held = frozenset() if key == "public" else frozenset(source_ids.index(value) for value in key.split(","))
        writer[held] = table
    conditions = {}
    for label in ("training", "overlap", "split"):
        prior = base.roster(label)
        for fee in FEES:
            records = []
            for focus in base.PAIRS:
                maximum, script = exact_script(focus, prior, fee)
                _, no_peer = base.best_script(focus, prior, 0.)
                _, mandatory_peer = base.best_script(focus, prior, base.PEER)
                variants = {
                    "optional_fit": learned,
                    "older_mandatory_fit": lift(baseline, focus, fee, True),
                    "known_prior_optional": script,
                    "known_prior_mandatory": lift(mandatory_peer, focus, fee, True),
                    "known_prior_independent": lift(no_peer, focus, fee, False),
                }
                rows = {name: replay(weights, fee, focus, prior, writer) for name, weights in variants.items()}
                rows["optional_fit_peer_erased"] = replay(learned, fee, focus, prior, writer, blind=True)
                assert abs(rows["known_prior_optional"]["delivery_net"] - maximum) < 1e-9
                assert all(maximum + 1e-9 >= score["delivery_net"] for score in rows.values())
                records.append({"focus": focus, "metrics": rows})
            means = {variant: {key: float(np.mean([r["metrics"][variant][key] for r in records]))
                               for key in values} for variant, values in records[0]["metrics"].items()}
            conditions[f"{label}/{fee}"] = {"mean": means, "cases": records}
    verification = np.mean([conditions[f"training/{fee}"]["mean"]["optional_fit"]["delivery_net"] for fee in FEES])
    assert abs(verification - history[-1]["record_reward"]) < 1e-9
    return {
        "scope": "One written-vote fit over three public communication prices, with independent private rosters. "
                 "The first desk can pay to expose its excerpt to the second, before either learns which "
                 "excerpts reached the chair. The known-prior optimized scripts use the same observations. "
                 "DRC final scores replay the fixed, reviewed separate-clause outputs.",
        "channel_fees": FEES, "fit": history, "trajectories": len(paths), "opening_rules_enumerated": len(OPENINGS),
        "conditions": conditions,
        "policy": [{"state": state, "probabilities": prob} for state, prob in learned.items()],
        "pins": {p.name: synthesis.contract.runner.digest(p) for p in (
            Path(__file__), TABLE_PATH, PARENT_POLICY, Path(base.__file__), Path(base.optimizer.__file__))},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
