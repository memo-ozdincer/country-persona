"""Fit evidence delivery for supported publication and contradiction repair."""
from collections import defaultdict
from itertools import product
import json
from pathlib import Path

import numpy as np

import routed_common_ground as endpoint

HERE = endpoint.HERE
base = endpoint.delivery.route.base
CITATIONS = HERE / "facilitator-citation-evidence/results.json"
RELATIONS = ("supports", "contradicts", "unknown")
TARGETS = frozenset((0, 1))
PASS = None
FEE = .10


def relation(world, card):
    return world[card] if card in TARGETS else "unknown"


def local(holding, readings, observed=PASS):
    return tuple((i, relation(readings, i)) for i in holding), observed


def observation(card, readings, acknowledged):
    return (card, relation(readings, card)) if acknowledged else PASS


def events(attempt):
    if attempt is None:
        return ((False, False, 1.),)
    return ((True, True, base.CHAIR * base.PEER), (True, False, base.CHAIR * (1-base.PEER)),
            (False, False, 1-base.CHAIR))


def paid(first, second):
    return FEE * (int(first is not None) + int(second is not None))


def delivered(first, ok, second, end_ok):
    return frozenset({first if ok else None, second if end_ok else None}) & TARGETS


def decision(status, seen):
    return endpoint.compose([status[i] for i in sorted(seen)])


def utility(published, gold):
    if published == "withhold":
        return 0.
    return 1. if published == gold else -1.


def trajectories(case_mass=None):
    states, paths = {}, defaultdict(float)
    width = 0

    def slot(role, view, action):
        nonlocal width
        key = (role, view)
        if key not in states:
            states[key] = width, 3
            width += 3
        return states[key][0] + action

    for status in product(RELATIONS, repeat=2):
        for (left, right), prob in base.roster("training").items():
            for a, first in enumerate((*left, PASS)):
                i = slot("first", local(left, status), a)
                for ok, ack, link in events(first):
                    seen = observation(first, status, ack)
                    for b, second in enumerate((*right, PASS)):
                        j = slot("second", local(right, status, seen), b)
                        value = 0.
                        for end_ok, second_p in ((True, base.CHAIR), (False, 1-base.CHAIR)):
                            snapshot = delivered(first, ok, second, end_ok)
                            value += second_p * utility(decision(status, snapshot), decision(status, TARGETS))
                        weight = prob * link / 9 if case_mass is None else prob * link * case_mass[status]
                        paths[i, j, paid(first, second), value] += weight
    actions = np.array([(a, b) for a, b, _, _ in paths], dtype=int)
    outcomes = np.array([(cost, 0., 35 + value, 0.) for _, _, cost, value in paths])
    return states, actions, outcomes, {"design_mixture": np.array(list(paths.values()))}


def greedy(holding, readings, seen):
    eligible = [i for i in holding if relation(readings, i) != "unknown" and (seen is None or i != seen[0])]
    if seen is not None and seen[1] == "contradicts":
        eligible = []
    return min(eligible, key=lambda i: (relation(readings,i) != "contradicts", i)) if eligible else PASS


def choice(name, learned, role, holding, readings, seen):
    if name.startswith("learned"):
        values = learned[role, local(holding, readings, seen)]
        return tuple(zip((*holding, PASS), values, strict=True))
    if name.startswith("greedy"):
        return ((greedy(holding, readings, seen), 1.),)
    raise ValueError(name)


def distribution(name, learned, prior, truth, reads):
    metrics, masks = defaultdict(float), defaultdict(float)
    for (left, right), p in prior.items():
        for first, a in choice(name, learned, "first", left, reads, PASS):
            for ok, ack, link in events(first):
                seen = observation(first, reads, ack and not name.endswith("erased"))
                for second, b in choice(name, learned, "second", right, reads, seen):
                    for end_ok, end in ((True, base.CHAIR), (False, 1-base.CHAIR)):
                        weight = p * a * link * b * end
                        receipt = delivered(first, ok, second, end_ok)
                        masks[receipt] += weight
                        gold = decision(truth, TARGETS)
                        result = decision(reads, receipt)
                        metrics["retain"] += weight * (gold == result == "retain")
                        metrics["revise"] += weight * (gold == result == "revise")
                        metrics["unsupported_decisions"] += weight * (result not in ("withhold", gold))
                        metrics["cost"] += weight * paid(first, second)
                        metrics["net"] += weight * (utility(result, gold) - paid(first, second))
    assert abs(sum(masks.values())-1.) < 1e-9
    return dict(metrics), masks


def cases():
    keys = endpoint.inputs()["keys"]
    read = endpoint.delivery.load(HERE / "routed-common-ground-evidence/results.json")["relations"]
    usable = {r["id"]: r for r in endpoint.delivery.load(CITATIONS)["rows"]}
    for group in range(6):
        key = keys[group*4+3]
        trace = read[str(group)]
        assert tuple(trace) == tuple(key["source_relations"])
        truth = tuple(key["source_relations"].values())
        seen = tuple(endpoint.stable(c["votes"]) or "unknown" for c in trace.values())
        yield (truth, seen, [usable[group*4+i] for i in range(4)])


def replay(learned):
    targets = list(cases())
    result = {}
    for inventory in ("overlap", "split"):
        for source in ("gold", "model"):
            prior = base.roster(inventory)
            expansions = {}
            for name in ("learned", "learned_erased", "greedy", "greedy_erased"):
                records = []
                for truth, measured, briefs in targets:
                    observed = truth if source == "gold" else measured
                    row, masks = distribution(name, learned, prior, truth, observed)
                    for writer in ("frozen_source_reader", "reviewed_oracle"):
                        row[writer+"_actionable"] = sum(
                            mass for received, mass in masks.items()
                            if briefs[int(0 in received)*2+int(1 in received)]["arms"][writer]["strict"]
                            and briefs[int(0 in received)*2+int(1 in received)]["expected_disposition"] != "withhold")
                    records.append(row)
                expansions[name] = {"mean": {key: sum(row[key] for row in records)/len(records)
                                              for key in records[0]}, "proposals": records}
            result[f"{inventory}/{source}"] = expansions
    return result


def run():
    states, actions, outcomes, masses = trajectories()
    history, fit = base.optimizer.fit(states, actions, outcomes, masses)
    learned = base.observed_weights(states, fit["joint_learned"])
    train = sum(distribution("learned", learned, base.roster("training"), status, status)[0]["net"]
                for status in product(RELATIONS, repeat=2))/9
    assert abs(train-history[-1]["record_reward"])<1e-9
    return {"scope":"One exact policy-gradient fit on nine synthetic source-relation pairs. No historical outcomes train the weights. "
                    "Frozen facilitator briefs and local relation readings are replayed afterward. "
                    "The sender may pass and the recipient may observe an actual delivery. Both pay a fixed simulated send cost.",
            "message_fee": FEE, "updates":base.optimizer.STEPS, "states":len(states), "trajectories":len(actions),
            "training":history, "replay":replay(learned),
            "policy":[{"state":key,"probabilities":p} for key,p in learned.items()]}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
