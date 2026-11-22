"""Recheck the one local priority change motivated by the failed fit."""
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from priority_audit import policy
from public_planner import HORIZON, apply, states, terminal
from voluntary_bound import reachable


def scores():
    baseline = policy((0, 2, 3, 1))
    single_open = policy((0, 1, 2, 3))
    counts = Counter()
    changes = Counter()
    for world, opening in states():
        outcome = "agreement" if world[0] & world[1] else "impasse"
        certified = {}
        for arm in ("base", "singleton_first"):
            state = opening
            for step in range(HORIZON):
                if terminal(state):
                    break
                i = (step + 1) % 2
                chooser = single_open if arm == "singleton_first" and step == 0 and world[i].bit_count() == 1 else baseline
                option = chooser(world, state, i)
                if option:
                    state = apply(state, i, option, bool(world[i] & option))
            certified[arm] = terminal(state)
            counts[(arm, outcome)] += certified[arm]
        capacity = reachable(world, opening) is not None
        counts[("omniscient_capacity", outcome)] += capacity
        assert not certified["singleton_first"] or capacity
        changes[(outcome, str(certified["base"]), str(certified["singleton_first"]))] += 1
    return {"certificates": {"/".join(k): v for k, v in counts.items()},
            "paired_outcomes": {"/".join(k): v for k, v in changes.items()}}


if __name__ == "__main__":
    print(json.dumps(scores(), indent=2))
