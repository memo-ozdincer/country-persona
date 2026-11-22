"""Render a sourced record from the majority decision and admitted local sentences."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

import facilitator_attribution_extracts as study
import facilitator_verified_brief_score as brief

BOTH = frozenset({0, 1})


def accept(row, source):
    text = row["output"].strip()
    for opening, closing in (('"', '"'), ('“', '”')):
        if text.startswith(opening) and text.endswith(closing):
            text = text[len(opening):-len(closing)]
            break
    # Recheck the complete sentence after stripping only a matched wrapper.
    return (text if row["ended"] and text.endswith(".") and
            text in re.split(r"(?<=\.)\s+", source) else None)


def render(panel, selected, witnesses):
    council = panel["council"].partition(". ")[0].removesuffix(".") + ". [S0]"
    evidence, states = {}, []
    for i, source in enumerate(panel["sources"], 1):
        sid = f"S{i}"
        exact = witnesses.get(sid)
        actor = source["actor"]
        if actor.startswith("The "):
            actor = "the " + actor[4:]
        if exact is not None and selected[sid] != "unknown":
            evidence[sid] = f"The card for {actor} records “{exact}” [{sid}]."
            states.append(selected[sid])
        else:
            evidence[sid] = f"The evidence leaves open whether {actor} {panel['predicate']} [{sid}]."
            states.append("unknown")
    heading = study.first.transfer.chair.base.decision(tuple(states), BOTH)
    return f"{heading} | {council} {evidence['S1']} {evidence['S2']}", council, evidence, states


def score(directory):
    rows = study.verify(directory)
    notes = brief.table(directory / "review.tsv")
    assert notes.keys() == rows.keys()
    votes = study.majority()
    checks, finals, summary = {}, {}, Counter()
    archived = study.archived()
    readings = study.first.readings(archived)
    order_correct = [0, 0, 0]
    for name, scenario in study.first.panels():
        reached = {}
        selected = {f"S{i}": votes[f"{name}/S{i}"] for i in (1, 2)}
        for i, source in enumerate(scenario["sources"], 1):
            sid = f"S{i}"
            key = f"{name}/{sid}"
            if key in rows:
                review = notes[key]
                row = rows[key]
                accepted = accept(row, source["card"])
                assert review["excerpt"] == (accepted or "")
                assert review["grounded"] in ("yes", "no") and bool(review["issue"]) == (review["grounded"] == "no")
                if review["grounded"] == "yes":
                    assert accepted is not None
                if accepted is not None:
                    reached[sid] = accepted
                checks[key] = {"accepted": accepted, "raw": row["output"], "review": review}
                summary.update({"witness_calls": 1, "admitted_witnesses": accepted is not None,
                                "adequate_witnesses": review["grounded"] == "yes"})
        text, council, bodies, stated = render(scenario, selected, reached)
        marks = {"council": council, "issue": "", "reason": ""}
        for i, truth in enumerate(scenario["expected"], 1):
            sid = f"S{i}"
            key = f"{name}/{sid}"
            for n, result in enumerate(readings[key]["observations"]):
                order_correct[n] += result == truth
            accurate = stated[i-1] == truth and (truth == "unknown" or
                       (key in notes and notes[key]["grounded"] == "yes"))
            marks[f"s{i}"] = bodies[sid] if accurate else ""
        grade = brief.grade({"output": text, "ended": True}, marks, scenario["expected"])
        finals[name] = {"selected": selected, "composed_relations": stated, **grade}
        summary.update({"records": 1, "strict": grade["strict"], "points": grade["points"],
                        "right_disposition": grade["disposition"] == grade["expected"],
                        "majority_correct": sum(selected[f"S{i}"] == truth
                                                for i, truth in enumerate(scenario["expected"], 1))})
    files = (Path(__file__), directory / "review.tsv", directory / "transcript.jsonl")
    return {"scope": "Post hoc majority selection, source-local witness generation, and template assembly. "
                     "The Council card and precise gap are deterministic. The model sees the authored report options "
                     "and a local source. Adequacy of the accepted sentences was reviewed by the same assistant.",
             "verified_generations": len(rows), "summary": summary, "witnesses": checks, "records": finals,
            "single_order_correct": order_correct,
            "sha256": {p.name: study.runner.digest(p) for p in files}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(score(p.parse_args().directory), indent=2, ensure_ascii=False))
