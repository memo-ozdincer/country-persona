"""Evaluate frozen archived routing policies with role-dependent hidden holdings."""
from collections import defaultdict
from itertools import product
import json

from verified_transfer import HERE, compile_bank, runner, transfer

relay = transfer.relay
TRAIN_STRENGTH = 3.0
CONDITIONS = {
    "original": (1., 0, None),
    "weak_specialist_A": (1.7, 0, None),
    "strong_specialist_B": (6., 1, None),
    "separate_desk_specialties": (4., 0, "split"),
    "mislabelled_specialist_B": (6., 1, "wrong_hint"),
}


def distribution(pending, strength, specialist, mode=None):
    a, b = sorted(pending)
    scored = {}
    for world, base in relay.DESIGN.items():
        preferred = world[specialist]
        if mode == "split":
            hits = int(a in preferred) + int(b in world[1 - specialist])
        else:
            hits = len(set(preferred) & {a, b})
        scored[world] = base * strength ** hits
    total = sum(scored.values())
    return {world: value / total for world, value in scored.items()}


def datasets():
    archived, _ = transfer.named_sources()
    mappings = transfer.read(transfer.HERE / "adaptive-align-results.json")["families"]
    for family, deck in archived.items():
        yield family, tuple(deck[0]), transfer.record_bank(deck), mappings[family]
    ids, bank = compile_bank()
    yield "colombia", ids, bank, transfer.read(HERE / "verified-transfer.json")["aligned"]


def actor_policy():
    payload = transfer.read(transfer.FROZEN)
    return {transfer.immutable(row["local_state"]): row["probabilities"] for row in payload["policy"]}


def remap(policy, roster, target, anchor, entry, order, canonical=False):
    pending = [i for i in target if i != anchor]
    omitted, = set(range(4)) - set(target)
    out = defaultdict(lambda: [0., 0., 0.])
    contexts = entry["matched_training_views"]
    for context in contexts:
        old_anchor, left, right = (relay.KEYS.index(name) for name in context)
        old_target = tuple(sorted((old_anchor, left, right)))
        old_omitted, = set(range(4)) - set(old_target)
        actual = dict(zip((old_anchor, left, right, old_omitted), (anchor, *pending, omitted), strict=True))
        inverse = {real: label for label, real in actual.items()}
        priors = {tuple(tuple(sorted(inverse[i] for i in world[desk])) for desk in order): mass
                  for world, mass in roster.items()}
        assert len(priors) == len(roster) and abs(sum(priors.values()) - 1) < 1e-9
        for missing, row in transfer.outcomes(policy, old_target, old_anchor, priors, canonical).items():
            remaining = frozenset(actual[i] for i in missing)
            for index, value in enumerate(row):
                out[remaining][index] += value / len(contexts)
    assert abs(sum(values[0] for values in out.values()) - 1) < 1e-9
    return out


def score(ids, bank, target, anchor, roster, routed):
    unanswered = frozenset(target) - {anchor}
    start = bank[frozenset({ids[anchor]})]["record_points"]

    def final(pending):
        return bank[frozenset(ids[i] for i in target if i not in pending)]["record_points"]

    records = {pending | {anchor}: {"final_record_score": final(pending)}
               for pending in (frozenset(), *(frozenset({i}) for i in unanswered), unanswered)}
    out = {}
    for name, receipts in routed.items():
        out[name] = relay.metrics((
            sum(row[0] for pending, row in receipts.items() if not pending),
            sum(row[1] for row in receipts.values()), sum(row[2] for row in receipts.values()),
            sum(row[0] * final(pending) for pending, row in receipts.items()),
        ))
    value, adaptive = relay.plan(roster, unanswered, 3, final)
    _, fixed = max((relay.plan(roster, unanswered, 3, final, route)
                    for route in product(range(2), repeat=3)), key=lambda entry: entry[0])
    out["known_prior_fixed"] = relay.metrics(relay.evaluate(fixed, roster, unanswered, anchor, records))
    out["known_prior_adaptive"] = relay.metrics(relay.evaluate(adaptive, roster, unanswered, anchor, records))
    assert abs(out["known_prior_adaptive"]["record_reward"] + 35 - value) < 1e-9
    for item in out.values():
        item.pop("reward")
        item["net_gain_over_anchor"] = item.pop("record_reward") + 35 - start
    return out


def evaluate(policies=None, conditions=CONDITIONS):
    old = actor_policy()
    policies = policies or {}
    suite = {}
    for family, ids, bank, mapping in datasets():
        aligned = {(row["anchor"], *row["other_cards"]): row for row in mapping["rows"]}
        cases = {}
        for condition, (strength, specialist, mode) in conditions.items():
            rows = []
            for target, anchor in relay.SCENARIOS:
                pending = [i for i in target if i != anchor]
                keys = (ids[anchor], *(ids[i] for i in pending))
                context = aligned[keys]
                roster = distribution(pending, strength, specialist, mode)
                guess = 1 - specialist if mode == "wrong_hint" else specialist
                order = (guess, 1 - guess)
                router = {"frozen_aligned": remap(old, roster, target, anchor, context, (0, 1)),
                          "frozen_aligned_with_desk_hint": remap(old, roster, target, anchor, context, order)}
                for name, (policy, canonical) in policies.items():
                    router[name] = remap(policy, roster, target, anchor, context, order, canonical)
                rows.append({"protected": keys[0], "missing": list(keys[1:]),
                             "metrics": score(ids, bank, target, anchor, roster, router)})
            cases[condition] = {"mean": transfer.mean([item["metrics"] for item in rows]), "rows": rows}
        if "original" in cases:
            actual = cases["original"]["mean"]["frozen_aligned"]
            expected = mapping["average"]["aligned_joint"]
            for field in actual:
                assert abs(actual[field] - expected[field]) < 1e-9, (family, field)
        suite[family] = cases
    return suite


if __name__ == "__main__":
    print(json.dumps({"scope": "Shift simulations with fixed authored record scoring. The fixed and adaptive controls "
                               "receive the true inventory prior, including for the deliberately wrong hint. "
                               "Only the inferred desk order, never its roster, is exposed to the learned team.",
                      "conditions": CONDITIONS, "families": evaluate()}, indent=2))
