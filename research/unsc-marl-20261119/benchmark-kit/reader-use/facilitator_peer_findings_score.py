"""Measure whether separate source findings improve the matched peer pipeline."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_fresh_brief_score as rubric
import facilitator_peer_findings as study
import facilitator_peer_quote_repair as repair


def annotations(directory, rows):
    with (directory / "review.tsv").open(newline="") as f:
        items = list(csv.DictReader(f, delimiter="\t"))
    marks = {item["id"]: item for item in items}
    assert len(marks) == len(items) and marks.keys() == rows.keys()
    for key, row in marks.items():
        output = rows[key]["output"]
        assert all(row[f] in output for f in ("s1", "s2", "issue", "span"))
        assert bool(row["issue"]) == bool(row["reason"])
        assert (row["witness"] == "final") == key.endswith("/final")
    return marks


def final_grades(rows, marks):
    finals = {k: r for k, r in rows.items() if k.endswith("/final")}
    reviews = [{"id": alias, **{f: marks[key][f] for f in ("s1", "s2", "issue", "reason")}}
               for alias, key in rubric.blind(finals).items()]

    def fixtures():
        for panel, claim, _, truth, cards, _, _ in study.panels():
            source = {sid: c["passage"] for sid, c in cards.items()}
            for arm in study.ARMS:
                yield f"{panel}/{arm}", claim, source, truth, frozenset({0, 1}), {}, {}

    with patch.object(rubric.study, "fixtures", fixtures):
        return rubric.checks(finals, reviews)


def episode(panel, arm, truth, cards, first, second, rows, marks, grades):
    opened = f"{panel}/{'solo' if arm == 'solo' else 'desk'}/opening"
    replied = f"{panel}/{arm}/reply"
    final = f"{panel}/{arm}/final"
    keys = (opened, replied, final)
    findings = study.notes(panel, arm, rows, cards, first, second)
    local = {}
    for sid, key in zip((first, second), (opened, replied), strict=True):
        expected = truth[int(sid[1:]) - 1]
        admitted = findings[sid]
        review = marks[key]
        span = admitted["excerpt"]
        assert review["span"] == (span or "")
        assert review["witness"] in ("adequate", "inadequate", "unadmitted")
        assert (review["witness"] == "unadmitted") == (span is None)
        raw = rows[key]["output"]
        well_formed = span is not None or (rows[key]["ended"] and raw == "unknown")
        local[sid] = {"key": key, "expected": expected, "admitted": admitted, "well_formed": well_formed,
                      "witness": review["witness"], "raw": raw}
    mechanical = rubric.study.base.decision(tuple(findings[k]["relation"] for k in ("S1", "S2")), frozenset({0, 1}))
    return {"steps": keys, "local": local, "mechanical_disposition": mechanical,
            "grade": grades[final], "inputs": sum(len(rows[k]["input_ids"]) for k in keys),
            "outputs": sum(len(rows[k]["output_ids"]) for k in keys)}


def check_pair(panel, rows):
    def payload(key):
        return json.loads(rows[key]["messages"][1]["content"])
    a, b = (payload(f"{panel}/{arm}/reply") for arm in ("peer", "independent"))
    assert a.pop("prior_finding") == rows[f"{panel}/desk/opening"]["output"] and a == b
    a, b = (payload(f"{panel}/{arm}/final") for arm in ("peer", "independent"))
    del a["working_notes"], b["working_notes"]
    assert a == b


def evaluate(rows, marks):
    grades = final_grades(rows, marks)
    summaries, episodes, differences = {}, {}, {}
    for panel, _, _, truth, cards, first, second in study.panels():
        check_pair(panel, rows)
        for arm in study.ARMS:
            item = episode(panel, arm, truth, cards, first, second, rows, marks, grades)
            episodes[f"{panel}/{arm}"] = item
            score = item["grade"]
            update = summaries.setdefault(arm, Counter())
            update.update({
                "panels": 1, "strict": score["strict"], "points": score["points"],
                "final_right": score["disposition"] == score["expected"],
                "mechanical_right": item["mechanical_disposition"] == score["expected"],
                "writer_heading_changed": score["disposition"] != item["mechanical_disposition"],
                "wrong_admitted": sum(f["admitted"]["relation"] not in ("unknown", f["expected"]) for f in item["local"].values()),
                "local_right": sum(f["admitted"]["relation"] == f["expected"] for f in item["local"].values()),
                "well_formed_local": sum(f["well_formed"] for f in item["local"].values()),
                "adequate_witnesses": sum(f["witness"] == "adequate" for f in item["local"].values()),
                "input_tokens": item["inputs"], "output_tokens": item["outputs"],
            })
        a, b = (episodes[f"{panel}/{arm}"] for arm in ("peer", "independent"))
        finals = [rows[f"{panel}/{arm}/final"] for arm in ("peer", "independent")]
        prompt_differs = finals[0]["input_ids"] != finals[1]["input_ids"]
        differences[panel] = {"final_prompt_differs": prompt_differs,
                              "final_output_differs": finals[0]["output_ids"] != finals[1]["output_ids"],
                              "points_delta": a["grade"]["points"] - b["grade"]["points"],
                              "answered_local_change": a["local"][second]["admitted"] != b["local"][second]["admitted"],
                              "peer_witness": a["local"][second]["witness"], "independent_witness": b["local"][second]["witness"]}
    return {"summary": summaries, "episodes": episodes, "peer_vs_independent": differences, "reviews": marks}


def score(directory, repaired=False):
    if repaired:
        changed = repair.verify(directory)
        rows = repair.old_rows() | changed
        with patch.object(study, "findings", repair.wrapped_base):
            evaluated = evaluate(rows, annotations(directory, rows))
        verified = len(changed)
    else:
        rows = study.verify(directory)
        evaluated = evaluate(rows, annotations(directory, rows))
        verified = len(rows)
    paths = (Path(__file__), directory / "review.tsv", directory / "transcript.jsonl")
    return {"scope": "Three matched calls and output caps per arm, unequal input tokens, three exposed source families, "
                     "same-assistant span reviews, zero optimization. Mechanical disposition uses admitted label fields "
                     "without the semantic witness judgments, and is diagnostic only.",
            "verified_generations": verified, "repaired_final_only": repaired, **evaluated,
            "sha256": {path.name: study.runner.digest(path) for path in paths}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--repaired", action="store_true")
    args = p.parse_args()
    print(json.dumps(score(args.directory, args.repaired), indent=2, ensure_ascii=False))
