"""Test the frozen timing policy on all two-missing-sign versions of these mandates."""
from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path
import runpy

study = runpy.run_path(str(Path(__file__).with_name("study.py")))
CARDS, EXPECTED, LETTERS, LOCK, POLICY = (study[k] for k in ("CARDS", "EXPECTED", "LETTERS", "LOCK", "POLICY"))
authored_masks, deferral, hashes, load, truth_bits = (
    study[k] for k in ("authored_masks", "deferral", "hashes", "load", "truth_bits")
)


def evaluate():
    assert load(LOCK)["source_hashes"] == hashes()
    policy = deferral.restore(load(POLICY))
    width = len(LETTERS)
    full = (1 << width) - 1
    pairs = [sum(1 << i for i in ix) for ix in combinations(range(width), 2)]
    counts = Counter()
    expected = authored_masks()

    def rotate(mask, offset):
        return ((mask << offset) | (mask >> (width - offset))) & full

    for family in CARDS[1:]:
        roles = ("japan", family)
        for offset in range(width):
            gold = tuple(rotate(expected[role], offset) for role in roles)
            for original in product(*(EXPECTED[role] for role in roles)):
                left, right = (rotate(truth_bits(letter), offset) for letter in original)
                opening = (left, 0, right, 0)
                for removed in product(pairs, repeat=2):
                    observed = tuple((mask & ~missing, ~mask & ~missing & full)
                                     for mask, missing in zip(gold, removed, strict=True))
                    row = width, gold, observed, opening
                    old, old_cost, old_calls = deferral.play(row, {})
                    new, new_cost, new_calls = deferral.play(row, policy)
                    counts[family, "paired", str(old), str(new)] += 1
                    for arm, result, slots, checks in (("script", old, old_cost, old_calls),
                                                       ("learned", new, new_cost, new_calls)):
                        for key, value in (("correct", result), ("slots", slots), ("checks", checks)):
                            counts[family, arm, key] += value
    return {"/".join(key): value for key, value in sorted(counts.items())}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
