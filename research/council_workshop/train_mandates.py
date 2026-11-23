"""Train a shared decentralized speech policy on exact workshop rewards."""

import argparse
from collections import Counter
from itertools import combinations_with_replacement, permutations
import json
from math import exp
from random import Random

from mandates import Mandates
from meeting import Meeting
from run import HERE


TRAIN_EPISODES = 16384
TURN_CAP = 9
SEED = 20261123
KINDS = ("accept", "propose", "rule_out", "declare_impasse", "yield_floor", "walk_away")
FEATURES = ("bias", "target_allowed", "target_excluded", "target_is_draft",
            "already_accepted", "accepted_fraction", "remaining_fraction")


def signature(masks):
    """Group profiles under both seat permutations and package relabeling."""
    return min(tuple(sorted(sum(1 << perm[i] for i in range(3) if mask & (1 << i))
                            for mask in masks)) for perm in permutations(range(3)))


def intersection(masks, options):
    common = (1 << options) - 1
    for mask in masks:
        common &= mask
    return common


def pools():
    signatures = sorted({signature(p) for p in combinations_with_replacement(range(1, 8), 3)})
    rng = Random(SEED)
    train, held = [[], []], [[], []]
    for feasible in (False, True):
        selected = [p for p in signatures if bool(intersection(p, 3)) == feasible]
        rng.shuffle(selected)
        n = max(1, len(selected)//4)
        train[feasible] = selected[n:]
        held[feasible] = selected[:n]
        assert train[feasible] and held[feasible]
    return train, held


def world(rng, masks, packages):
    seats = [f"seat-{i+1}" for i in range(len(masks))]
    labels = [f"package-{i+1}" for i in range(packages)]
    options = {label: f"Fictional proposed clause {label}." for label in labels}
    perm = rng.sample(range(packages), packages)
    allowed = {country: frozenset(labels[perm[i]] for i in range(packages) if mask & (1 << i))
               for country, mask in zip(seats, rng.sample(list(masks), len(masks)), strict=True)}
    return seats, options[rng.choice(labels)], Mandates(options, allowed)


def candidates(public, country, allowed):
    options = public["options"]
    excluded = public["exclusions"]
    selected = next(label for label, draft in options.items() if draft == public["draft"])
    rows = [("accept", selected), ("yield_floor", selected), ("walk_away", selected)]
    rows += [("propose", label) for label in options if label != selected]
    rows += [("rule_out", label) for label in options if label not in allowed and label not in excluded]
    if excluded.keys() == options.keys():
        rows.append(("declare_impasse", selected))
    return rows, selected


def features(rows, selected, public, country, allowed, seats):
    accepted = public["accepted"]
    excluded = public["exclusions"]
    remaining = 1-len(excluded)/len(public["options"])
    return [(1., float(label in allowed), float(label in excluded), float(label == selected),
             float(country in accepted), len(accepted)/seats, remaining) for _, label in rows]


def policy(rows, feats, weights):
    logits = [sum(w*x for w, x in zip(weights[KINDS.index(kind)], row, strict=True))
              for (kind, _), row in zip(rows, feats, strict=True)]
    highest = max(logits)
    exps = [exp(value-highest) for value in logits]
    partition = sum(exps)
    return [item/partition for item in exps]


def scripted(rows, selected, public, country):
    left = sorted(public["options"].keys() - public["exclusions"].keys())
    vetoes = [row for row in rows if row[0] == "rule_out"]
    if vetoes:
        return next((row for row in vetoes if row[1] == selected), vetoes[0])
    if not left:
        return "declare_impasse", selected
    if selected not in left:
        return "propose", left[0]
    if country in public["accepted"]:
        return "yield_floor", selected
    return "accept", selected


def rollout(instance, choose, collect=False):
    seats, draft, mandates = instance
    meeting = Meeting(seats, draft, mandates=mandates)
    observations = []
    for turn in range(TURN_CAP):
        seat = seats[turn % len(seats)]
        public, allowed = meeting.view(), mandates.allowed[seat]
        rows, selected = candidates(public, seat, allowed)
        feats = features(rows, selected, public, seat, allowed, len(seats))
        choice, probabilities = choose(rows, selected, public, seat, feats)
        kind, label = choice
        if collect:
            observations.append((rows, feats, choice, probabilities))
        text = label if kind in {"propose", "rule_out"} else kind
        meeting.apply(seat, {"action": kind, "version": meeting.version, "text": text})
        if meeting.status != "open":
            break
    if meeting.status == "open":
        meeting.status = "turn_cap"
    score = mandates.score(meeting.status, meeting.draft)
    return score | {"status": meeting.status, "turns": len(meeting.history)}, observations


def train(train_pools, objective):
    world_rng, action_rng = Random(SEED+1), Random(SEED+2)
    weights = [[0.]*len(FEATURES) for _ in KINDS]
    mean = 0.
    trace = []
    block = Counter()
    for episode in range(TRAIN_EPISODES):
        instance = world(world_rng, world_rng.choice(train_pools[episode % 2]), 3)

        def choose(rows, selected, public, seat, feats):
            p = policy(rows, feats, weights)
            return action_rng.choices(rows, weights=p, k=1)[0], p

        end, log = rollout(instance, choose, True)
        reward = end["reward"] if objective == "verified" else int(end["status"] == "unanimous_acceptance")
        advantage = reward - mean
        mean += 0.02*(reward - mean)
        step = 0.05 / (1 + episode/TRAIN_EPISODES)**0.5
        for rows, feats, choice, probs in log:
            for row, feat, prob in zip(rows, feats, probs, strict=True):
                delta = step*advantage*(int(row == choice)-prob)/len(log)
                w = weights[KINDS.index(row[0])]
                for i, value in enumerate(feat):
                    w[i] += delta*value
        block[end["outcome"]] += 1
        if (episode+1) % 1024 == 0:
            trace.append({"through_episode": episode+1, "outcomes": dict(sorted(block.items()))})
            block.clear()
    return {"weights": weights, "trace": trace}


def held_worlds(held):
    rng = Random(SEED+3)
    cohorts = {name: [] for name in ("new_3_seat", "new_5_seat", "four_packages")}
    for feasible in (False, True):
        for _ in range(64):
            cohorts["new_3_seat"].append(world(rng, rng.choice(held[feasible]), 3))
            for key, seats, packages in (("new_5_seat",5,3), ("four_packages",5,4)):
                while True:
                    masks = [rng.randrange(1, 1 << packages) for _ in range(seats)]
                    if bool(intersection(masks, packages)) == feasible:
                        break
                cohorts[key].append(world(rng, masks, packages))
    for key in ("feasible", "impasse"):
        case = json.loads((HERE/f"climate-packages-{key}.json").read_text())
        seats = list(case["delegations"])
        cohorts.setdefault("climate", []).append((seats, case["draft"], Mandates.from_case(case, seats)))
    return cohorts


def evaluate(cohorts, fits):
    def choose(name, rows, selected, public, seat, feats):
        if name == "script":
            return scripted(rows, selected, public, seat), None
        if name == "always_accept":
            return ("accept", selected), None
        p = policy(rows, feats, fits[name]["weights"])
        return rows[max(range(len(p)), key=p.__getitem__)], None

    outputs = {}
    for key, instances in cohorts.items():
        outputs[key] = {}
        for name in (*fits, "script", "always_accept"):
            phases = {key:Counter() for key in ("feasible", "infeasible")}
            for instance in instances:
                score, _ = rollout(instance, lambda *args: choose(name, *args))
                kind = "feasible" if score["feasible_packages"] else "infeasible"
                phases[kind][score["outcome"]] += 1
                phases[kind]["speeches"] += score["turns"]
            outputs[key][name] = {part: dict(sorted(counts.items())) for part, counts in phases.items()}
    return outputs


def run():
    train_pools, held = pools()
    fits = {key:train(train_pools, key) for key in ("verified", "unanimity_proxy")}
    outcomes = evaluate(held_worlds(held), fits)
    return {"plan": {"seed": SEED, "training_episodes_per_arm": TRAIN_EPISODES, "speech_cap": TURN_CAP,
                     "train_profiles": train_pools, "held_three_seat_profiles": held,
                     "features": FEATURES, "action_kinds": KINDS},
            "fits": fits, "held": outcomes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(run(), indent=2))
