"""Exact bounded-contact decision benchmark with hidden, synthetic source rosters."""
from itertools import combinations, product
import json

import corroboration as archive
from scoped_relay import QUESTION_COST, REPLY_COST

KEYS = archive.KEYS
WORLDS = tuple(product(archive.PAIRS, repeat=2))
SCENARIOS = tuple((target, anchor) for target in combinations(range(len(KEYS)), 3) for anchor in target)
LINK = .9
RECEIPT = LINK ** 2


def prior(predicate):
    worlds = [world for world in WORLDS if predicate(*world)]
    return {world: 1 / len(worlds) for world in worlds}


PRIORS = {
    "independent": prior(lambda a, b: True),
    "identical": prior(lambda a, b: a == b),
    "complementary": prior(lambda a, b: not set(a) & set(b)),
    "one_shared": prior(lambda a, b: len(set(a) & set(b)) == 1),
}
DESIGN = {world: sum(p.get(world, 0) for p in PRIORS.values()) / len(PRIORS) for world in WORLDS}


def assembly(task, target, packets):
    allowed = {KEYS[index] for index in target}
    received = {packet["key"] for packet in packets if archive.admit(packet, allowed)}
    passages = [archive.PASSAGES[key] for key in KEYS if key in received]
    comparison = archive.REQUIRED["shared"] <= received
    if comparison and len(" ".join(passages + [archive.COMPARISON]).split()) <= 85:
        passages.append(archive.COMPARISON)
    supplement = " ".join(passages)
    assert len(supplement.split()) <= 85
    record = task["public_record"] + " " + supplement
    proof = {key: list(archive.PROOF[key]) for key, required in archive.REQUIRED.items()
             if required <= received and all(span in record for span in archive.PROOF[key])}
    return {"received": sorted(received), "complete": allowed <= received,
            "missing": sorted(allowed - received), "supplement_words": len(supplement.split()),
            "final_record": record, "proof": proof, "final_record_score": 35 + 7 * len(proof)}


def transitions(belief, pending, contact):
    branches = {}
    fees = 0.
    for world, mass in belief.items():
        held = pending.intersection(world[contact])
        receipt = min(held, default=None)
        fees += mass * (QUESTION_COST + LINK * REPLY_COST * bool(held))
        outcomes = ((None, 1.),) if receipt is None else ((receipt, RECEIPT), (None, 1 - RECEIPT))
        for seen, probability in outcomes:
            branches.setdefault(seen, {})[world] = mass * probability
    return fees, branches


def plan(belief, pending, budget, terminal, schedule=None):
    """Compare unnormalized expected values; branch mass carries the posterior."""
    best = terminal(pending) * sum(belief.values()), (None, {})
    if budget == 0 or not pending:
        return best
    for contact in (range(2) if schedule is None else schedule[:1]):
        fee, observations = transitions(belief, pending, contact)
        score = -fee
        children = {}
        for seen, posterior in observations.items():
            value, tree = plan(posterior, pending - {seen}, budget - 1, terminal,
                               None if schedule is None else schedule[1:])
            score += value
            children[seen] = tree
        if score > best[0] + 1e-10:
            best = score, (contact, children)
    return best


def evaluate(tree, belief, pending, anchor, records):
    contact, children = tree
    if contact is None:
        mass = sum(belief.values())
        return mass * (not pending), 0., 0., mass * records[pending | {anchor}]["final_record_score"]
    fees, observations = transitions(belief, pending, contact)
    completion = 0.
    attempts = sum(belief.values())
    quality = 0.
    for seen, posterior in observations.items():
        values = evaluate(children[seen], posterior, pending - {seen}, anchor, records)
        completion += values[0]
        fees += values[1]
        attempts += values[2]
        quality += values[3]
    return completion, fees, attempts, quality


def policy_json(tree):
    contact, children = tree
    if contact is None:
        return {"action": "stop"}
    return {"action": "AB"[contact], "on": {
        "no_receipt" if seen is None else KEYS[seen]: policy_json(child) for seen, child in children.items()
    }}


def metrics(values):
    completion, costs, attempts, quality = values
    return dict(completion=completion, cost=costs, attempts=attempts,
                reward=28 * completion - costs, final_record_score=quality,
                record_reward=quality - 35 - costs)


def run():
    task = archive.load()
    rows = []
    for target, anchor in SCENARIOS:
        pending = frozenset(target) - {anchor}
        records = {frozenset(missing) | {anchor}: assembly(
            task, target, [archive.packet(index) for index in sorted(set(target) - set(missing))])
            for size in range(3) for missing in combinations(sorted(pending), size)}
        for outstanding, record in records.items():
            assert record["complete"] == (outstanding == {anchor})
        def completion(pending):
            return 28 * (not pending)

        def record_score(pending):
            return records[pending | {anchor}]["final_record_score"] - 35

        options = {}
        for budget in (2, 3):
            for objective, terminal in (("complete", completion), ("record", record_score)):
                prefix = f"{budget}_{objective}"
                value, adaptive = plan(DESIGN, pending, budget, terminal)
                fixed_value, fixed = max(
                    (plan(DESIGN, pending, budget, terminal, route)
                     for route in product(range(2), repeat=budget)), key=lambda item: item[0])
                assert value + 1e-9 >= fixed_value
                for name, tree, expected in (("adaptive", adaptive, value), ("fixed", fixed, fixed_value)):
                    options[f"{prefix}_{name}"] = tree
                    result = metrics(evaluate(tree, DESIGN, pending, anchor, records))
                    measured = (result["reward"] if objective == "complete"
                                else result["final_record_score"] - 35 - result["cost"])
                    assert abs(measured - expected) < 1e-9
        results = {label: {name: metrics(evaluate(tree, unc, pending, anchor, records))
                           for name, tree in options.items()}
                   for label, unc in {**PRIORS, "design_mixture": DESIGN}.items()}
        rows.append({"target": [KEYS[i] for i in target], "anchor": KEYS[anchor],
                     "policy": {k: policy_json(t) for k, t in options.items()},
                     "results": results, "record_examples": list(records.values())})
    aggregates = {
        label: {name: {key: round(sum(row["results"][label][name][key] for row in rows) / len(rows), 8)
                       for key in rows[0]["results"][label][name]}
                for name in rows[0]["results"][label]}
        for label in rows[0]["results"]
    }
    return {"assumptions": {"independent_delivery_per_leg": LINK, "completion_reward": 28,
                            "request_cost": QUESTION_COST, "reply_cost": REPLY_COST,
                            "contact_budgets": [2, 3], "supplement_word_limit": 85,
                            "design_prior": "uniform mixture of the four declared synthetic priors"},
            "averages": aggregates, "scenarios": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
