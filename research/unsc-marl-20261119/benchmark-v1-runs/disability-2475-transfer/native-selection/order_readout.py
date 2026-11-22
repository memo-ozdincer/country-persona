"""Check whether pooling every ordering of the same passage set changes selection."""
from collections import defaultdict
from itertools import product
from math import exp, fsum, log
from pathlib import Path

from compose_notes import GOLD, MENUS, render
from select_notes import HERE, OUT, READ, frozen, prior


def run():
    data = READ(HERE / "verified.json")["selections"]
    tests = prior.wire.n.lines(OUT / "likelihood.jsonl")
    choices = {}
    for row in tests:
        key = row["request"]["id"]
        groups = defaultdict(list)
        for candidate in row["selection"]["alternatives"]:
            groups[tuple(sorted(candidate["ids"]))].append(candidate["log_mass"])
        mass = {}
        for ids, values in sorted(groups.items()):
            peak = max(values)
            mass[ids] = peak + log(fsum(exp(value - peak) for value in values))
        selected = max(mass, key=mass.get)
        eligible = data[key]
        choices[key] = {"selected_by_set_mass": list(selected),
                        "ordered_message_set": sorted(eligible["native"]),
                        "canonical_message_set": sorted(eligible["canonical"]),
                        "first_message_set": sorted(eligible["first"]),
                        "gold": GOLD[int(key.split("/")[-1])],
                        "mass_by_set": {" ".join(k): v for k, v in mass.items()}}
    banks = {}
    for order in ("normal", "reversed"):
        groups = [choices[f"{order}/{i}"]["selected_by_set_mass"] for i in range(len(MENUS))]
        banks[order] = [render(groups, mask)["score"]["released_70"] for mask in range(8)]
    comparison = {}
    for mode in ("selected_by_set_mass", "ordered_message_set", "canonical_message_set", "first_message_set"):
        comparison[mode] = {
            "correct_local_sets": sum(row[mode] == row["gold"] for row in choices.values()),
            "sets_preserved_under_reversal": sum(choices[f"normal/{i}"][mode] == choices[f"reversed/{i}"][mode]
                                                  for i in range(len(MENUS))),
        }
    assert len(choices) == 6
    return {"comparison": comparison, "banks": banks, "choices": choices,
            "sha256": {p.name: prior.digest(p) for p in (Path(__file__), OUT / "likelihood.jsonl", HERE / "verified.json")}}


if __name__ == "__main__":
    frozen.emit(run())
