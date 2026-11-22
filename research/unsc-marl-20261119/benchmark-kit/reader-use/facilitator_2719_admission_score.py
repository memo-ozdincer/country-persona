"""Render eligible notes and audit semantic evidence admission."""
import argparse
import json
from pathlib import Path

import facilitator_2719_admission as study

CHAINS = {
    "A": {"doc", "vote"},
    "U": {"us_read", "us_reason"},
    "F": {"fr_gap", "fr_support", "fr_levels"},
    "AF": {"fr_vote", "fr_gap"},
    "AUF": {"doc", "vote", "fr_vote", "us_reason", "fr_gap"},
}
TEXT = {
    "doc": "The US submitted amendment S/2023/1023.",
    "vote": "The amendment passed by nine votes to none, with six abstentions, before unanimous adoption of the final resolution.",
    "fr_vote": "France abstained on the amendment and voted for the amended resolution.",
    "us_read": "The United States read the original draft as excluding full UN financing.",
    "us_reason": "It sought an explicit ceiling to remove ambiguity and help enable timely deployment.",
    "fr_gap": "France withheld support for the amendment because it did not clarify how funding outside assessed contributions would be made predictable.",
    "fr_support": "France reaffirmed support for assessed UN funding for AU-led operations.",
    "fr_levels": "France was prepared to discuss different contribution levels from the UN and the EU.",
}
WEIGHTS = {r["id"]: r["points"] for r in study.old.packet()["criteria"]}
MASK = {name: 1 << owner for name, owner, _ in study.CLAIMS}


def compose(selected):
    sentences = []
    for name, text in TEXT.items():
        if name not in selected:
            continue
        if name == "us_reason" and "us_read" not in selected:
            text = text.replace("It sought", "The United States sought")
        sentences.append(text)
    if CHAINS["AUF"] <= selected:
        sentences.append("The amendment passed despite France's concern about the remainder, distinct from the US demand for an explicit ceiling.")
    record = " ".join(sentences)
    assert len(record.split()) <= 154
    return record


def points(atoms):
    return 42 + sum(WEIGHTS[k] for k, required in CHAINS.items() if required <= atoms)


def run(directory):
    outputs = json.loads((directory / "admission.json").read_text())
    gold = json.loads((directory / "gold.json").read_text())
    review = json.loads((directory / "witness-review.json").read_text())
    assert outputs.keys() == gold.keys() == review.keys()
    report = {}
    for name, fields in outputs.items():
        selected = {k for k, row in fields.items() if row["status"] == "admitted"}
        expected = set(gold[name])
        support = review[name]
        assert set(support) == selected
        for key, mark in support.items():
            assert mark[0] in ("entailed", "unentailed", "uncertain")
            if mark[0] == "entailed":
                assert key in expected
        admitted = {key for key, mark in support.items() if mark[0] == "entailed"}
        mistaken = sorted(selected - admitted)
        supplement = compose(selected)
        full = " ".join(study.old.packet()["public"]) + ("\n\n" + supplement if supplement else "")
        report[name] = {"expected": sorted(expected), "admitted": sorted(selected),
                        "supported_admissions": sorted(admitted), "invalid_or_uncertain_admissions": mistaken,
                        "missed": sorted(expected - admitted), "supplement": supplement, "record": full,
                        "material_points": points(admitted),
                        "release_points": points(admitted) if not mistaken else 0,
                        "release": not mistaken,
                        "role_erasure_material_points": [
                            points({k for k in admitted if MASK[k] & mask}) for mask in range(8)],
                        "audit": support}
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(run(p.parse_args().directory), ensure_ascii=False, indent=2))
