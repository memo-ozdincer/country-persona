"""Locate missed or harmful admissions in the measured role-local channel."""
from fractions import Fraction
from pathlib import Path

import team

HERE = team.HERE


def audit(rows):
    possible = []
    errors = []
    for row in rows:
        for order, view in row["orders"].items():
            local, peer, truth = view["first"], view["second"], row["truth"]
            if local == truth and truth != "unknown":
                possible.append([row["key"], order])
            if local == peer and local not in (truth, "unknown"):
                errors.append([row["key"], order, local, truth])
    n = sum(len(row["orders"]) for row in rows)
    return {"contexts": n, "truthful_first_labels": possible, "unanimous_wrong_labels": errors,
            "local_action_oracle_net": str(Fraction(19 * len(possible), 20 * n))}


def run():
    held = team.read(HERE / "results.json")["held_rows"]
    train = team.read(HERE / "fit.json")["archive_rows"]
    result = {"held": audit(held),
              "archive_by_family": {family: audit([r for r in train if r["family"] == family])
                                    for family in sorted({r["family"] for r in train})}}
    inputs = (HERE / "results.json", HERE / "fit.json", Path(__file__))
    return result | {"sha256": {p.name: team.pin(p) for p in inputs}}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
