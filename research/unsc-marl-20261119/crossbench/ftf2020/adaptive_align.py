"""Map a frozen policy to public receipt payoff shapes, with no new optimization."""
from functools import lru_cache
import json
from pathlib import Path

import adaptive_transfer as transfer

relay = transfer.relay
HERE = Path(__file__).resolve().parent


def shape(bank, names):
    anchor, left, right = names

    def score(ids):
        return bank[frozenset(ids)]["record_points"]

    baseline = score({anchor})
    raw = (score({anchor, left}) - baseline, score({anchor, right}) - baseline,
           score({anchor, left, right}) - baseline)
    scale = max(1, *map(abs, raw))
    return raw, tuple(value / scale for value in raw)


def enrich(policy=None, training_bank=None):
    if policy is None:
        fitted = transfer.read(transfer.FROZEN)
        policy = {transfer.immutable(row["local_state"]): row["probabilities"] for row in fitted["policy"]}
    bank = transfer.ftf_bank() if training_bank is None else training_bank
    catalogue = []
    for target, anchor in relay.SCENARIOS:
        a, b = (k for k in target if k != anchor)
        for first, second in ((a, b), (b, a)):
            keys = [relay.KEYS[k] for k in (anchor, first, second)]
            _, profile = shape(bank, keys)
            catalogue.append((target, anchor, first, second, profile))

    @lru_cache(None)
    def choose(profile):
        distance = [sum((x - y) ** 2 for x, y in zip(entry[-1], profile, strict=True)) for entry in catalogue]
        best = min(distance)
        return best, [entry[:4] for entry, d in zip(catalogue, distance, strict=True) if abs(d - best) < 1e-12]

    @lru_cache(None)
    def rollout(target, anchor, canonical):
        return transfer.outcomes(policy, target, anchor, relay.DESIGN, canonical)

    def evaluate(bank, ids):
        rows = []
        for target, anchor in relay.SCENARIOS:
            a, b = (k for k in target if k != anchor)
            names = [ids[k] for k in (anchor, a, b)]
            raw, profile = shape(bank, names)
            distance, choices = choose(profile)
            distributions = {}
            for canonical in (False, True):
                merged = {}
                for origin, protected, first, second in choices:
                    mapping = {first: a, second: b}
                    for pending, values in rollout(origin, protected, canonical).items():
                        renamed = tuple(sorted(mapping[i] for i in pending))
                        previous = merged.get(renamed, (0., 0., 0.))
                        merged[renamed] = tuple(old + new / len(choices)
                                                for old, new in zip(previous, values, strict=True))
                assert abs(sum(row[0] for row in merged.values()) - 1.) < 1e-9
                name = "aligned_canonical" if canonical else "aligned_joint"
                distributions[name] = merged
            rows.append({"anchor": names[0], "other_cards": names[1:], "payoff_shape": raw,
                         "distance": distance, "matched_training_views": [
                             [relay.KEYS[protected], relay.KEYS[first], relay.KEYS[second]] for
                             _, protected, first, second in choices],
                         "metrics": transfer.policy_compare(target, anchor, ids, bank, distributions)})
        return {"average": transfer.mean([row["metrics"] for row in rows]), "rows": rows}

    dossiers, _ = transfer.named_sources()
    results = {}
    # The registry order does not favor a particular mapping. Reversing
    # the card labels must leave expected aligned metrics invariant.
    for family, deck in dossiers.items():
        bank = transfer.record_bank(deck)
        checked = evaluate(bank, tuple(deck[0]))
        reversed_ids = evaluate(bank, tuple(reversed(deck[0])))
        for route in ("aligned_joint", "aligned_canonical"):
            for field, value in checked["average"][route].items():
                assert abs(value - reversed_ids["average"][route][field]) < 1e-9
        results[family] = checked
    train_contexts = evaluate(bank=transfer.ftf_bank() if training_bank is None else training_bank, ids=relay.KEYS)
    return {"scope": "Posthoc transfer intervention. The public mapping compares reward shapes, not realized target outcomes. "
                     "Joint weights and learned observations over message histories are unchanged. "
                     "The transfer dockets were not used for fitting. The public rubric and anchor fix a shared alias mapping.",
            "families": results,
            "training_docket_shape_check": train_contexts}


if __name__ == "__main__":
    print(json.dumps(enrich(), indent=2, ensure_ascii=False))
