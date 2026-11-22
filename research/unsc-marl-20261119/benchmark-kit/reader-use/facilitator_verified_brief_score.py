"""Score the transferred verifier and the final record without editing its text."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re

import facilitator_verified_brief as study

TAG = re.compile(r"\[([A-Za-z0-9-]+)\]")
DESCRIPTORS = ("council", "s1", "s2", "issue")


def table(path):
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    index = {r["id"]: r for r in rows}
    assert len(rows) == len(index)
    return index


def token_counts(row):
    return len(row["input_ids"]), len(row["output_ids"])


def grade(row, notes, truth):
    text = row["output"]
    assert all(notes[key] in text for key in DESCRIPTORS)
    assert bool(notes["issue"]) == bool(notes["reason"])
    expected = study.common.chair.base.decision(tuple(truth), frozenset({0, 1}))
    heading, delimiter, body = text.partition("|")
    got = heading.strip().casefold() if delimiter else None
    tags = set(TAG.findall(body))
    sourced = tags <= {"S0", "S1", "S2"} and "[S0]" in notes["council"] and all(
        f"[S{i+1}]" in notes[f"s{i+1}"] for i, relation in enumerate(truth) if relation != "unknown"
    )
    compliant = row["ended"] and bool(body.strip()) and len(body.split()) <= 75 and (
        "\n" not in text and "|" not in body and got in ("retain", "revise", "withhold")
    )
    points = {"disposition": 14 * (got == expected), "council": 12 * bool(notes["council"]),
              "s1": 10 * bool(notes["s1"]), "s2": 10 * bool(notes["s2"]), "citation": 8 * sourced,
              "fidelity": 10 * (not notes["issue"]), "format": 6 * compliant}
    total = sum(points.values())
    return {"expected": expected, "disposition": got, "points": total, "criteria": points,
            "strict": total == 70, "review": notes, "text": text}


def compare(rows, panel):
    base = rows[f"{panel}/pooled/final"]
    direct = rows[f"{panel}/direct/final"]
    hybrid = rows[f"{panel}/hybrid/final"]
    packets = [json.loads(r["messages"][1]["content"]) for r in (base, direct, hybrid)]
    checks = [r.pop("witness_checks", None) for r in packets]
    assert packets[0] == packets[1] == packets[2]
    assert checks[0] is None and checks[1] is not None and checks[2] is not None
    assert base["cap"] == direct["cap"] == hybrid["cap"]
    return {"direct_labels": checks[1], "hybrid_labels": checks[2],
            "direct_hybrid_prompt_differs": direct["input_ids"] != hybrid["input_ids"],
            "direct_hybrid_output_differs": direct["output_ids"] != hybrid["output_ids"]}


def score(directory):
    rows = study.verify(directory)
    reviews = table(directory / "review.tsv")
    reasons = table(directory / "checks-review.tsv")
    assert reviews.keys() == {k for k in rows if k.endswith("/final")}
    assert reasons.keys() == rows.keys() - reviews.keys()
    local, finals, comparisons = {}, {}, {}
    by_gate, by_system = {}, {}
    checks = study.checks(rows)
    for panel, _, item, _ in study.panels():
        comparisons[panel] = compare(rows, panel)
        for i, truth in enumerate(item["expected"], 1):
            expected = "conflict" if truth == "contradicts" else "open"
            for arm, name in zip(study.previous.ARMS, ("direct", "hybrid"), strict=True):
                key = f"{panel}/S{i}/{arm}"
                evidence = checks[key]
                notes = reasons[key]
                assert notes["span"] and notes["span"] in rows[key]["output"]
                assert notes["grounded"] in ("yes", "no")
                assert bool(notes["issue"]) == (notes["grounded"] == "no")
                grounded = evidence["bound_vote_rule"] or notes["grounded"] == "yes"
                gate = by_gate.setdefault(name, Counter())
                gate.update({"checks": 1, "correct": evidence["verdict"] == expected,
                             "raw_proposed_correct": evidence["proposed"] == expected,
                             "supported_correct": evidence["verdict"] == expected and grounded,
                             "false_conflict": evidence["verdict"] == "conflict" and expected != "conflict",
                             "rules_applied": evidence["bound_vote_rule"]})
                local[key] = evidence | {"expected": expected, "review": notes, "grounded": grounded}
        for arm in study.FAMILIES:
            key = f"{panel}/{arm}/final"
            item_grade = grade(rows[key], reviews[key], item["expected"])
            finals[key] = item_grade
            summary = by_system.setdefault(arm, Counter())
            used = [rows[key]]
            if arm != "pooled":
                gate_name = "direct" if arm == "direct" else "compare_first"
                used.extend(rows[f"{panel}/S{i}/{gate_name}"] for i in (1, 2))
            cost = list(zip(*(token_counts(row) for row in used), strict=True))
            summary.update({"records": 1, "strict": item_grade["strict"],
                            "correct_disposition": item_grade["expected"] == item_grade["disposition"],
                            "points": item_grade["points"], "council_complete": bool(item_grade["criteria"]["council"]),
                            "fidelity_errors": bool(item_grade["review"]["issue"]),
                            "calls": len(used), "input_tokens": sum(cost[0]), "output_tokens": sum(cost[1])})
    files = (Path(__file__), directory / "review.tsv", directory / "checks-review.tsv", directory / "transcript.jsonl")
    return {"scope": "The verifier prompt, allowed separator whitespace and vote rule are carried over unchanged. "
                     "Direct and hybrid use matched call counts. Pooled is a one-call reference. These are normalized "
                     "source cards and a same-assistant evaluation with a full-evidence final writer.",
            "verified_generations": len(rows), "gate_summary": by_gate, "record_summary": by_system,
            "checks": local, "finals": finals, "paired_input_audit": comparisons,
            "sha256": {path.name: study.runner.digest(path) for path in files}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(score(p.parse_args().directory), indent=2, ensure_ascii=False))
