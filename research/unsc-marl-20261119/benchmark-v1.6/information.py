"""Enumerate the decision value of each role's information on the four-world workshop grids."""
from collections import defaultdict
from itertools import product

import evaluate as e


def audit():
    families = defaultdict(list)
    for row in e.cases().values():
        if row["track"] == "workshop":
            families[row["family"]].append(row)
    results = {}
    for family, worlds in sorted(families.items()):
        # Each of the authored worlds has equal mass in this audit.
        first = worlds[0]
        assert all(w["public"] == first["public"] and w["task"] == first["task"]
                   and w["roles"] == first["roles"] and w["options"] == first["options"]
                   for w in worlds)
        profiles = [tuple(e.checksum(desk) for desk in world["owned"]) for world in worlds]
        assert len(profiles) == len(set(profiles)) == 4
        assert all(len({view[side] for view in profiles}) == 2 for side in (0, 1))
        visibility = {}
        for sides in product((False, True), repeat=2):
            partitions = defaultdict(list)
            for world in worlds:
                view = e.checksum([world["owned"][side] for side, seen in enumerate(sides) if seen])
                partitions[view].append(set(world["gold"]))
            scores = [max(sum(action in gold for gold in cell) for action in set.union(*cell))
                      for cell in partitions.values()]
            visibility["".join("1" if seen else "0" for seen in sides)] = sum(scores) / len(worlds)
        results[family] = {"worlds": len(worlds), "oracle_accuracy_by_visibility": visibility}
    return results


if __name__ == "__main__":
    e.emit(audit())
