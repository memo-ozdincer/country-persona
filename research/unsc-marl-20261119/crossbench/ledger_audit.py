"""Independently enumerate the hidden completions of every partial disclosure."""
from itertools import product
import json

from decision_ledger import readout, truthful_disclosure

OPTIONS = tuple("ABCD")
ROLES = ("left", "right")


def branch(state):
    accepts = [o for o, value in zip(OPTIONS, state) if value == 1]
    excludes = [o for o, value in zip(OPTIONS, state) if value == -1]
    completions = []
    for bits in product((0, 1), repeat=len(OPTIONS)):
        menu = {o for o, b in zip(OPTIONS, bits) if b}
        if set(accepts) <= menu and not (menu & set(excludes)):
            completions.append(menu)
    return accepts, excludes, completions


def check():
    branches = [branch(state) for state in product((-1, 0, 1), repeat=len(OPTIONS))]
    counts = {"inputs": 0, "admissible_pair_completions": 0, "complete_profiles": 0,
              "AGREEMENT_POSSIBLE": 0, "IMPASSE": 0, "UNRESOLVED": 0}
    for left, right in product(branches, repeat=2):
        evidence = [dict(id=f"d-{i}", role=role, accepts=item[0], excludes=item[1])
                    for i, (role, item) in enumerate(zip(ROLES, (left, right)))]
        value = readout(OPTIONS, ROLES, evidence)
        overlap = [a & b for a, b in product(left[2], right[2])]
        necessarily_available = set.intersection(*overlap)
        possibly_available = set.union(*overlap)
        assert set(value["verified_options"]) == necessarily_available
        assert set(value["blocked_options"]) == set(OPTIONS) - possibly_available
        assert set(value["unresolved_options"]) == possibly_available - necessarily_available
        assert value["unique_verified"] == (len(necessarily_available) == len(possibly_available) == 1)
        assert value["state"] == ("AGREEMENT_POSSIBLE" if necessarily_available else "UNRESOLVED" if possibly_available else "IMPASSE")
        assert all(truthful_disclosure(e, m) for e, item in zip(evidence, (left, right)) for m in item[2])
        counts["inputs"] += 1
        counts["admissible_pair_completions"] += len(overlap)
        counts[value["state"]] += 1
        counts["complete_profiles"] += len(overlap) == 1
    collision = [dict(id="x", role=ROLES[0], accepts=["A"]), dict(id="y", role=ROLES[0], excludes=["A"])]
    invalid = readout(OPTIONS, ROLES, collision)
    assert invalid == {"state": "CONTRADICTORY_DISCLOSURE", "conflicts": [
        {"option": "A", "role": ROLES[0], "accepts": ["x"], "excludes": ["y"]}]}
    assert not truthful_disclosure(collision[0], set())
    assert not truthful_disclosure(collision[1], {"A"})
    for invalid in ([collision[0], collision[0]], [dict(id="x", role="left", accepts=[{}])], [{}]):
        try:
            readout(OPTIONS, ROLES, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed disclosure accepted")
    a = readout(OPTIONS, ROLES, [dict(id="x", role="left", accepts=["A"]),
                                dict(id="y", role="right", accepts=["A"])])
    b = readout(OPTIONS, ROLES, [dict(id="x", role="left", accepts=["A"]),
                                dict(id="y", role="right", accepts=["A"]),
                                dict(id="z", role="right", accepts=["A"])])
    assert a["state"] == b["state"] == "AGREEMENT_POSSIBLE"
    assert set(a["verified_options"]) == set(b["verified_options"]) == {"A"}
    assert not a["unique_verified"] and not b["unique_verified"]
    assert b["verified_options"]["A"]["right"] == ["y", "z"]
    return {**counts, "same_owner_conflict_guard": True, "private_truth_audit": True,
            "malformed_disclosure_rejected": True, "duplicate_id_rejected": True,
            "repeated_claim_preserves_decision_and_provenance": True}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
