"""Grade discrimination and source-specific reasoning on fixed-witness pairs."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

import facilitator_witness_contrast as study
from facilitator_scope_rules import inspect
import facilitator_vote_witness_rule as vote


DERIVED = ("compare_strip", "typed_compare")


def answer(row, arm, strip_separator=False):
    output = row["output"]
    sections = output.split("|")
    if len(sections) != 2:
        return None, False, output
    verdict, proof = (s.strip() for s in (sections if arm == "direct" else sections[::-1]))
    verdict = verdict.casefold()
    valid = (row["ended"] and verdict in ("open", "conflict") and 0 < len(proof.split()) <= 25
             and "\n" not in (proof + verdict if strip_separator else output))
    return verdict if verdict in ("open", "conflict") else None, valid, proof


def review(directory, rows):
    with (directory / "review.tsv").open(newline="") as f:
        items = list(csv.DictReader(f, delimiter="\t"))
    marks = {row["id"]: row for row in items}
    assert len(marks) == len(items) and marks.keys() == rows.keys()
    for key, row in marks.items():
        assert row["grounding"] in ("yes", "no")
        assert row["span"] and row["span"] in rows[key]["output"]
        assert (row["grounding"] == "no") == bool(row["issue"])
    return marks


def score(directory):
    rows = study.verify(directory)
    marks = review(directory, rows)
    reads, groups, pairs = {}, {}, {}
    vote.tests()
    summary = {arm: Counter() for arm in (*study.ARMS, *DERIVED, "always_open", "bounded_rule")}
    for key, expected, inputs in study.cases():
        family = key.split("/", 1)[0]
        proof = inspect(inputs["assertion"], inputs["cited_words"], inputs["official_card"])
        for arm in summary:
            name = f"{key}/{arm}"
            if arm == "always_open":
                verdict, valid, reason, mark = "open", True, "", {"grounding": "no"}
            elif arm == "bounded_rule":
                verdict, valid, reason = (proof and proof["decision"]), proof is not None, ""
                mark = {"grounding": "yes" if proof else "no"}
            else:
                original = arm if arm in study.ARMS else "compare_first"
                requested = f"{key}/{original}"
                row = rows[requested]
                verdict, valid, reason = answer(row, original, arm in DERIVED)
                mark = marks[requested]
                if arm == "typed_compare":
                    typed = vote.check(inputs["assertion"], inputs["cited_words"], inputs["official_card"])
                    if typed:
                        verdict, valid, reason = typed, True, ""
                        mark = {"grounding": "yes", "rule": "same actor and resolution"}
            admitted = verdict if valid else None
            grounded = mark["grounding"] == "yes"
            reads[name] = {"expected": expected, "proposed": verdict, "admitted": admitted,
                           "valid": valid, "proof": reason, "grounded": grounded, "review": mark}
            quantities = {"items": 1, "correct": admitted == expected, "raw_label_correct": verdict == expected,
                          "sound_correct": admitted == expected and grounded, "invalid": not valid,
                          "false_conflict": expected == "open" and admitted == "conflict",
                          "missed_conflict": expected == "conflict" and admitted != "conflict",
                          "true_conflict": expected == admitted == "conflict"}
            summary[arm].update(quantities)
            groups.setdefault(f"{family}/{arm}", Counter()).update(quantities)
            prefix = key.rsplit("/", 1)[0]
            pairs.setdefault(f"{prefix}/{arm}", {})[expected] = reads[name]
    paired = {}
    for key, items in pairs.items():
        assert items.keys() == {"open", "conflict"}
        arm = key.rsplit("/", 1)[1]
        passed = all(r["expected"] == r["admitted"] for r in items.values())
        grounded = passed and all(r["grounded"] for r in items.values())
        paired[key] = {"matched_pair_pass": passed, "grounded_pair_pass": grounded}
        summary[arm].update({"matched_pair_pass": passed, "grounded_pair_pass": grounded})
    files = (Path(__file__), Path(vote.__file__), study.PACK, directory / "review.tsv", directory / "transcript.jsonl")
    return {"scope": "Fixed-source and fixed-witness contrasts on two public meetings new to this facilitator test. "
                     "Compare-first changes instruction and output order. Whitespace and typed vote repairs are retrospective. "
                     "Source reasoning was reviewed by the same assistant. No policy fitting.",
            "verified_generations": len(rows), "overall": summary, "by_family": groups, "paired": paired,
            "checks": reads, "sha256": {p.name: study.earlier.runner.digest(p) for p in files}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(score(parser.parse_args().directory), indent=2, ensure_ascii=False))
