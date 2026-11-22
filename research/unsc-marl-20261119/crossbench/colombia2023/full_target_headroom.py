"""Bound strict record release under the three-contact sourcing protocol."""
from collections import defaultdict
from functools import lru_cache
from itertools import product
import json
from pathlib import Path

import receipt_outcomes as parent

HERE = parent.HERE
relay = parent.relay
roster = parent.roster
RELEASE_VALUE = 28
OBSERVED = HERE / "unifil-field-transfer-evidence/results.json"


def solve(target, anchor, prior, can_release, pay):
    """Choose a desk and reply priority at each public receipt history."""
    unresolved = frozenset(target) - {anchor}

    @lru_cache(None)
    def search(belief, pending, left):
        mass = sum(weight for _, weight in belief)
        success = mass * (not pending and can_release)
        best = (RELEASE_VALUE * success, success, 0., 0., (None, {}))
        if not pending or not left or not can_release:
            return best
        for desk, prefer_high in product(range(2), range(2) if len(pending) == 2 else (0,)):
            branches = defaultdict(list)
            fee = 0.
            for world, weight in belief:
                choices = pending.intersection(world[desk])
                fee += weight * (relay.QUESTION_COST + relay.LINK * relay.REPLY_COST * bool(choices))
                if choices:
                    choice = (max if prefer_high else min)(choices)
                    branches[choice].append((world, weight * relay.RECEIPT))
                    branches[None].append((world, weight * (1 - relay.RECEIPT)))
                else:
                    branches[None].append((world, weight))
            rate, cost, contacts = 0., fee, mass
            children = {}
            for receipt, posterior in branches.items():
                _, new_rate, new_cost, new_contacts, tree = search(tuple(posterior), pending - {receipt}, left - 1)
                rate += new_rate
                cost += new_cost
                contacts += new_contacts
                children[receipt] = tree
            score = RELEASE_VALUE * rate - pay * cost
            if (score, -cost) > (best[0] + 1e-10, -best[2]) or (
                    abs(score - best[0]) <= 1e-10 and cost < best[2] - 1e-10):
                best = score, rate, cost, contacts, ((desk, prefer_high), children)
        return best

    objective, success, fees, contacts, tree = search(tuple(prior.items()), unresolved, 3)
    audit = replay(tree, prior, unresolved)
    actual = (success, fees, contacts)
    expected = (audit[0] * can_release, *audit[1:])
    assert all(abs(a - b) < 1e-9 for a, b in zip(actual, expected, strict=True))
    return {"objective": objective, "full_target_release": success, "cost": fees, "contacts": contacts,
            "strict_net": RELEASE_VALUE * success - fees, "tree": tree}


def replay(tree, prior, pending):
    """Walk the fixed tree with explicit independent request and reply losses."""
    def play(node, world, needed):
        action, steps = node
        if action is None:
            return float(not needed), 0., 0.
        desk, high = action
        held = needed.intersection(world[desk])
        outcomes = [(None, 1 - relay.LINK, relay.QUESTION_COST)]
        if held:
            card = (max if high else min)(held)
            fee = relay.QUESTION_COST + relay.REPLY_COST
            outcomes.extend(((card, relay.LINK ** 2, fee), (None, relay.LINK * (1 - relay.LINK), fee)))
        else:
            outcomes.append((None, relay.LINK, relay.QUESTION_COST))
        acc = [0., 0., 1.]
        for seen, p, fee in outcomes:
            success, cost, contacts = play(steps[seen], world, needed - {seen})
            acc[0] += p * success
            acc[1] += p * (fee + cost)
            acc[2] += p * contacts
        return acc

    worlds = [(weight, play(tree, world, pending)) for world, weight in prior.items()]
    return tuple(sum(weight * result[i] for weight, result in worlds) for i in range(3))


def run():
    seen = roster.transfer.read(OBSERVED)
    _, ids, _, _ = next(row for row in roster.datasets() if row[0] == "unifil")
    cases = []
    for row_index, (target, anchor) in enumerate(relay.SCENARIOS):
        prior = roster.distribution(set(target) - {anchor}, *roster.CONDITIONS["strong_specialist_B"])
        names = ",".join(sorted(ids[i] for i in target))
        attainable = [packets[names]["releasable"] for packets in seen["packets"].values()]
        assert len(set(attainable)) == 1
        row = {
            "target": names,
            "anchor": ids[anchor],
            "writer_can_release_with_every_card": attainable[0],
            "all_cards_ceiling": solve(target, anchor, prior, True, False),
            "release_ceiling": solve(target, anchor, prior, attainable[0], False),
            "release_net_oracle": solve(target, anchor, prior, attainable[0], True),
        }
        for writer, records in seen["routes"].items():
            actual = records["rows"][row_index]
            row[writer] = {}
            for route, result in actual.items():
                metric = result["metrics"]
                strict = metric["full_target_release_probability"]
                row[writer][route] = {"full_target_release": strict, "cost": metric["cost"],
                                      "contacts": metric["contacts"],
                                      "strict_net": RELEASE_VALUE * strict - metric["cost"]}
                if route != "pooled":
                    assert strict <= row["release_ceiling"]["full_target_release"] + 1e-9
                    assert row[writer][route]["strict_net"] <= row["release_net_oracle"]["strict_net"] + 1e-9
        cases.append(row)
    averages = {}
    for key in ("all_cards_ceiling", "release_ceiling", "release_net_oracle"):
        averages[key] = {col: sum(row[key][col] for row in cases) / len(cases)
                         for col in ("full_target_release", "cost", "contacts", "strict_net")}
    for key in seen["routes"]:
        averages[key] = roster.transfer.mean([row[key] for row in cases])
    return {"full_release_value": RELEASE_VALUE, "source_digest": parent.writer.runner.digest(OBSERVED),
            "scope": "Exact upper bound with request-specific reply priority and known roster prior. "
                     "The strict net oracle sees full-packet writer feasibility, but never realized private holdings. "
                     "Full-target receipt, writer feasibility, and strict released outcomes are separate.",
            "averages": averages, "scenarios": cases}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
