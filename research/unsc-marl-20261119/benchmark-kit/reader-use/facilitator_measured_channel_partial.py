"""Measure documentary credit lost by rejecting incomplete cards as a whole."""
import argparse
import json

import facilitator_measured_channel_fit as study

REQUIRES = {
    "A": {(1, 0), (1, 1), (1, 2)},
    "U": {(2, 0), (2, 1)},
    "F": {(3, 0), (3, 1), (3, 2)},
    "AF": {(1, 1), (3, 0)},
    "AUF": {(1, 0), (1, 1), (2, 1), (3, 0)},
}


def records(held):
    criteria = study.study.dossier.packet()["criteria"]
    weights = {c["id"]: c["points"] for c in criteria}
    def value(atoms):
        return 42 + sum(weights[k] for k, needed in REQUIRES.items() if needed <= atoms)

    def contents(mask):
        return {(c, i) for c in range(1, 4) if mask & (1 << (c - 1)) for i in range(3)}

    assert [value(contents(mask)) for mask in range(8)] == study.rubric.ceilings(criteria)
    out = {}
    for key, row in held["replies"].items():
        c = int(key[-1])
        review = row["assessment"]
        eligible = row["ended"] and row["words"] <= 52 and not review["errors"]
        units = {(c, i) for i, spans in enumerate(review["required"]) if eligible and spans}
        before_after = []
        for mask in range(8):
            if mask & (1 << (c - 1)):
                continue
            before = contents(mask)
            if row["passed"]:
                assert len(units) == 3
                strict_gain = value(before | units) - value(before)
            else:
                strict_gain = 0
            atom_gain = value(before | units) - value(before)
            before_after.append({"opening": mask, "full_card_gain": strict_gain, "supported_atom_gain": atom_gain})
        out[key] = {"safe_fields": sorted(i for _, i in units), "whole_card_pass": row["passed"],
                    "opening_replays": before_after}
    return out


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    held = study.read(study.EVIDENCE / "admission.json")
    print(json.dumps(records(held), indent=2))
