"""Fit and evaluate a guarded speech policy with differently behaving partners."""

from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from random import Random

import budget_policy as budget

core = budget.core
ROOT = core.HERE.parents[1]
REFERENCE = ROOT/"reports/council-workshop-budget-policy-20261123/results.json"
EPISODES = 8192
SEED = core.SEED+204
TRAIN_PARTNERS = ("checked", "eager", "closer")
TEST_PARTNERS = ("checked", "eager", "current_only", "silent")
CAP = 9


def select(rows, feats, weights, rng=None):
    available = [i for i, action in enumerate(rows) if action[0] != "accept" or feats[i][1]]
    prob = core.policy([rows[i] for i in available], [feats[i] for i in available], weights)
    index = rng.choices(range(len(prob)), weights=prob, k=1)[0] if rng is not None else max(
        range(len(prob)), key=prob.__getitem__)
    output = [0.] * len(rows)
    for slot, value in zip(available, prob, strict=True):
        output[slot] = value
    return rows[available[index]], output


def partner(style, rows, selected, public, seat, feats):
    if style == "checked":
        return core.scripted(rows, selected, public, seat), None
    if style == "closer":
        return budget.close_first(rows, selected, public, seat, feats)
    if style == "eager":
        return ("accept", selected), None
    if style == "current_only":
        if ("rule_out", selected) in rows:
            return ("rule_out", selected), None
        if ("declare_impasse", selected) in rows:
            return ("declare_impasse", selected), None
        if feats[0][1] and selected not in public["exclusions"] and seat not in public["accepted"]:
            return ("accept", selected), None
    return ("yield_floor", selected), None


def train(pool, initial, mixed):
    weights = [row.copy() for row in initial]
    worlds, actions, assignment = (Random(SEED+i) for i in (1, 2, 3))
    average = 0.
    block = Counter()
    trace = []
    for episode in range(EPISODES):
        instance = core.world(worlds, worlds.choice(pool[episode % 2]), 3)
        seats = instance[0]
        fixed = assignment.choice(seats)
        style = assignment.choice(TRAIN_PARTNERS)
        cap = assignment.choice(budget.TRAIN_CAPS)

        def choose(rows, selected, public, seat, feats):
            if mixed and seat == fixed:
                return partner(style, rows, selected, public, seat, feats)
            return select(rows, feats, weights, actions)

        result, observed = core.rollout(instance, choose, True, turn_cap=cap, context=budget.budget_features)
        trainable = [entry for entry in observed if entry[-1] is not None]
        reward = result["reward"]
        if trainable:
            core.policy_update(weights, trainable, reward-average, 0.035/(1+episode/EPISODES)**0.5)
        average += .02*(reward-average)
        block[result["outcome"]] += 1
        block["learner_decisions"] += len(trainable)
        if (episode+1) % 1024 == 0:
            trace.append({"episodes": episode+1, "outcomes": dict(sorted(block.items()))})
            block.clear()
    return {"weights": weights, "trace": trace}


def reachable_diagnostic(style, instance, fixed):
    mandates = instance[2]
    feasible = set(mandates.options).intersection(*mandates.allowed.values())
    if style == "silent" and feasible:
        return "partner_never_signs"
    if style in {"eager", "silent"} and not feasible:
        others = (mandates.allowed[s] for s in instance[0] if s != fixed)
        if set(mandates.options).intersection(*others):
            return "partner_holds_required_exclusion"
    return "no_identified_obstruction"


def evaluate(cohorts, weights):
    report = {}
    for cohort, worlds in cohorts.items():
        if cohort == "new_3_seat":
            continue
        report[cohort] = {}
        for style in (*TEST_PARTNERS, "homogeneous"):
            total = {name: {"feasible": Counter(), "infeasible": Counter()} for name in weights}
            paired = {name: Counter() for name in weights if name != "frozen"}
            obstructions = Counter()
            for instance in worlds:
                seats, _, mandates = instance
                feasible = bool(set(mandates.options).intersection(*mandates.allowed.values()))
                slots = seats if style != "homogeneous" else [None]
                for fixed in slots:
                    obstruction = reachable_diagnostic(style, instance, fixed)
                    obstructions[obstruction] += 1
                    prior = None
                    for name, policy_weights in weights.items():
                        def choose(rows, selected, public, seat, feats):
                            if seat == fixed:
                                return partner(style, rows, selected, public, seat, feats)
                            return select(rows, feats, policy_weights)

                        result, _ = core.rollout(instance, choose, turn_cap=CAP,
                                                 context=budget.budget_features)
                        group = "feasible" if feasible else "infeasible"
                        total[name][group][result["outcome"]] += 1
                        total[name][group]["speeches"] += result["turns"]
                        if obstruction != "no_identified_obstruction":
                            assert not result["reward"]
                        if name == "frozen":
                            prior = result["reward"]
                        else:
                            paired[name]["wins" if result["reward"] > prior else
                                         "losses" if result["reward"] < prior else "ties"] += 1
            report[cohort][style] = {
                "methods": {name: {g: dict(sorted(v.items())) for g, v in panels.items()}
                            for name, panels in total.items()},
                "vs_frozen": {name: dict(sorted(counts.items())) for name, counts in paired.items()},
                "obstructions": dict(sorted(obstructions.items())),
            }
    return report


def run():
    initial = json.loads(REFERENCE.read_text())["training"]["variable_budget_aware"]["weights"]
    pool, held = core.pools()
    fits = {"self_play": train(pool, initial, False), "mixed": train(pool, initial, True)}
    cohort_seed = SEED+5
    cohorts = core.held_worlds(held, cohort_seed)
    policies = {"frozen": initial, **{name: row["weights"] for name, row in fits.items()}}
    pins = (Path(__file__), REFERENCE, Path(core.__file__), Path(budget.__file__),
            core.HERE/"meeting.py", core.HERE/"mandates.py")
    return {"plan": {"episodes_per_arm": EPISODES, "seed": SEED, "cohort_seed": cohort_seed,
                     "train_partners": TRAIN_PARTNERS, "test_partners": TEST_PARTNERS,
                     "speech_cap": CAP,
                     "pins": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                              for path in pins}},
            "fits": fits, "evaluation": evaluate(cohorts, policies)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
