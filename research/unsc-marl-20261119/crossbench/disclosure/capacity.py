"""Audit the information budget and scripted policies across all four-option worlds."""
from collections import Counter
from itertools import combinations, product
import json

from protocol import readout, script, truthful_disclosure

MENU = frozenset("ABCD")
ROLES = ("first", "second")


def exclusions(menu, cap):
    options = sorted(MENU - menu)
    return [frozenset(combo) for n in range(cap + 1) for combo in combinations(options, n)]


def main():
    menus = [frozenset(combo) for size in range(1, 5) for combo in combinations(sorted(MENU), size)]
    comparisons = {key: Counter() for key in ("support_first", "exclusion_first", "public_A_probe")}
    counts = Counter()
    ceilings = {cap: Counter() for cap in (1, 2, 3)}
    blocked = Counter()
    for left, right in product(menus, repeat=2):
        is_possible = bool(left & right)
        kind = "agreement" if is_possible else "impasse"
        counts[kind] += 1
        reference = {"allowed_by_role": [sorted(left), sorted(right)], "joint_packages": sorted(left & right)}
        for arm, tally in comparisons.items():
            outcome = script(ROLES, reference, arm)
            tally[kind] += outcome["clean_correct"]
        for cap, tally in ceilings.items():
            if is_possible:
                selected = min(left & right)
                sets = [{"accepts": [selected]}, {"accepts": [selected]}]
            else:
                witness = next(((a, b) for a, b in product(exclusions(left, cap), exclusions(right, cap))
                                if a | b == MENU), None)
                if witness is None:
                    if cap == 2:
                        blocked[f"{len(left)}-vs-{len(right)}"] += 1
                    continue
                sets = [{"excludes": sorted(a)} for a in witness]
            claims = [{**record, "role": role, "id": f"oracle-{i}"}
                      for i, (role, record) in enumerate(zip(ROLES, sets))]
            assert all(truthful_disclosure(c, menu) for c, menu in zip(claims, (left, right)))
            observed = readout(sorted(MENU), ROLES, claims)["state"]
            assert observed == ("AGREEMENT_POSSIBLE" if is_possible else "IMPASSE")
            tally[kind] += 1
    print(json.dumps({
        "scope": "Three label-order policies use local and permitted public information. Capacity assumes an oracle knows both private menus.",
        "worlds": len(menus) ** 2, "denominators": dict(counts),
        "scripted_correct_by_class": {k: dict(v) for k, v in comparisons.items()},
        "claim_budget_capacity_by_role": {cap: dict(v) for cap, v in ceilings.items()},
        "impasse_unreachable_with_two_claims_per_role": dict(blocked),
    }, indent=2))


if __name__ == "__main__":
    main()
