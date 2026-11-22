"""Measure the rendered source-bound briefs under the existing receipt policies."""
import argparse
import csv
import json
from pathlib import Path

import facilitator_bound_fields as bound
import facilitator_fresh_brief_score as grade

study = bound.prior
FRESH = bound.HERE / "facilitator-fresh-brief-evidence/results.json"


def semantic_review(directory, rows):
    with (directory / "review.tsv").open(newline="") as f:
        reviews = list(csv.DictReader(f, delimiter="\t"))
    indexed = {r["id"]: r for r in reviews}
    assert indexed.keys() == rows.keys() and len(reviews) == len(rows)
    for key, mark in indexed.items():
        raw = rows[key]["output"]
        assert mark["supported_span"] in raw and mark["issue_span"] in raw
        assert bool(mark["issue_span"]) == bool(mark["reason"])
    return indexed


def render(fields, reviews):
    outputs, notes = {}, {}
    for panel, _, _, _, seen, actions, _ in study.fixtures():
        case, _ = panel.rsplit("/", 1)
        family = case.rsplit("-", 1)[0]
        speakers = [speaker for speaker, _ in study.transfer.packets()[family]]
        spans, parts, faults = [], [], []
        format_ok = True
        for i, speaker in enumerate(speakers):
            if i not in seen:
                unavailable = f"The available evidence does not establish the position of {speaker}."
                parts.append(unavailable)
                spans.append(unavailable)
                continue
            sid = f"S{i+1}"
            key = f"{case}/{sid}"
            row, mark = fields[key], reviews[key]
            text = row["output"]
            part = f"{text} [{sid}]"
            parts.append(part)
            spans.append(part if mark["supported_span"] else "")
            format_ok &= row["ended"] and len(text.split()) <= 21 and bool(text) and "\n" not in text
            if mark["issue_span"]:
                faults.append([mark["issue_span"], mark["reason"]])
        for action in set(actions.values()) - {None}:
            key = study.request_id(panel, action)
            outputs[key] = {"output": f"{action} | {' '.join(parts)}", "ended": bool(format_ok)}
            issue, reason = faults[0] if faults else ("", "")
            notes[key] = {"s1": spans[0], "s2": spans[1], "issue": issue, "reason": reason}
    annotations = [{"id": alias, **notes[key]} for alias, key in grade.blind(outputs).items()]
    return outputs, grade.checks(outputs, annotations)


def run(directory):
    launch_script = directory / "launch-script.py"
    source = bound.read(directory, launch_script if launch_script.exists() else None)
    reviews = semantic_review(directory, source)
    outputs, scored = render(source, reviews)
    original = study.load(FRESH)
    assert original["grades"].keys() == (scored | {
        k: v for k, v in original["grades"].items() if k.endswith("/pooled")
    }).keys()
    pooled = {k: v for k, v in original["grades"].items() if k.endswith("/pooled")}
    results = grade.replay(pooled | scored)
    return {"scope": "New independent source-field generations, deterministic rendering and existing receipt weights. "
                     "Archived pooled outputs are retained. The same assistant reviews each generated field.",
            "fields": reviews, "rendered": {k: r["output"] for k, r in sorted(outputs.items())},
            "grades": dict(sorted(scored.items())), "replay": results,
            "inputs_sha256": {p.name: study.runner.digest(p) for p in
                              (FRESH, directory / "review.tsv", directory / "transcript.jsonl")}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(run(p.parse_args().directory), ensure_ascii=False, indent=2))
