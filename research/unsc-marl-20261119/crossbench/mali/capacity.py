"""Bound the evidence available to each replay before attributing misses to routing."""
import argparse
from itertools import combinations
import json
from pathlib import Path

import runpy

STUDY = runpy.run_path(str(Path(__file__).with_name("transfer.py")))
CASE, MENUS, load = (STUDY[key] for key in ("CASE", "MENUS", "load"))


def audit(result):
    case = load(CASE)
    routes = result["paths"]
    options = {p["id"] for p in case["options"]}
    signs = result["package_predictions"]
    answer = {}
    for variant in ("france-overlap", "france-impasse"):
        cards = (variant, "russia")
        common = MENUS[cards[0]] & MENUS[cards[1]]
        for method, sets in result["published_scope_candidates"].items():
            scope_masks = {
                card: {p["id"] for p in case["options"] if p["scope"] in sets[card]}
                for card in cards
            }
            scope_masks = {card: mask if not (mask & MENUS[card]) else set()
                           for card, mask in scope_masks.items()}
            exclusions = {label for label in options if any(
                signs[card][label]["sign"] is False and label not in MENUS[card] for card in cards)}
            availability = {}
            for key, path in routes.items():
                if not key.startswith(f"{variant}/{method}/strong/"):
                    continue
                opening = key.rsplit("/", 1)[1]
                if common:
                    candidates = []
                    for label in common:
                        if all(signs[card][label]["sign"] is True for card in cards):
                            sent = sum(o == label for o in opening)
                            candidates.append(2 - sent)
                else:
                    candidates = []
                    for use in range(3):
                        for subset in combinations(cards, use):
                            blocks = set().union(*(scope_masks[card] for card in subset))
                            if blocks | exclusions == options:
                                candidates.append(2 * use + len(options - blocks))
                minimum = min(candidates, default=None)
                availability[opening] = {"minimum_continuation_slots": minimum,
                                         "certificate": path["public"]["state"]}
                if path["public"]["state"] in ("AGREEMENT_POSSIBLE", "IMPASSE"):
                    assert minimum is not None and minimum <= path["slots"]
            answer[f"{variant}/{method}"] = {
                "initial_truthful_exclusions": sorted(exclusions),
                "validated_scope_exclusions": {card: sorted(mask) for card, mask in scope_masks.items()},
                "per_opening": availability,
            }
    return {"scope": "Clairvoyant observer with all admitted evidence. The slot bound ignores speaker order and is not a policy.",
            "variants": answer}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics", type=Path)
    print(json.dumps(audit(load(p.parse_args().metrics)), indent=2))
