"""Score full brief quality and trace relevant ideas across three calls."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_fresh_brief_score as rubric
import facilitator_live_peers as study

ALL = frozenset({0, 1})
UNIT_KEYS = {
    "guinea": ("Ghana_compromise", "Ghana_gap", "China_treaty_limit"),
    "libya": ("UK_elections", "UK_gap", "Algeria_withdrawal", "Algeria_A3plus"),
}


def read_annotations(directory, rows):
    with (directory / "review.tsv").open(newline="") as f:
        marks = list(csv.DictReader(f, delimiter="\t"))
    indexed = {r["id"]: r for r in marks}
    assert len(marks) == len(indexed) and indexed.keys() == rows.keys()
    for key, mark in indexed.items():
        raw = rows[key]["output"]
        for field in ("s1", "s2", "issue", "question"):
            assert mark[field] in raw
        assert bool(mark["issue"]) == bool(mark["reason"])
        assert not (mark["s1"] or mark["s2"]) or key.endswith("/final")
        assert not mark["question"] or key.endswith("/opening")
    with (directory / "units.tsv").open(newline="") as f:
        units = list(csv.DictReader(f, delimiter="\t"))
    registry = {key: {} for key in rows}
    for item in units:
        key, unit, span = item["id"], item["unit"], item["span"]
        family = key.split("-", 1)[0]
        assert unit in UNIT_KEYS[family] and unit not in registry[key]
        assert span and span in rows[key]["output"]
        registry[key][unit] = span
    return indexed, registry


def grade(rows, marks):
    selected = {k: r for k, r in rows.items() if k.endswith("/final")}
    def fixtures():
        for panel, claim, _, truth, cards, _, _ in study.panels():
            sources = {sid: record["passage"] for sid, record in cards.items()}
            for arm in study.ARMS:
                yield f"{panel}/{arm}", claim, sources, truth, ALL, {}, {}

    # Existing rubric keys use a packet then a writer suffix.
    keyed = {f"{k.removesuffix('/final')}/record": row for k, row in selected.items()}
    annotations = [
        {"id": key, **{field: marks[k.removesuffix("/record") + "/final"][field]
                       for field in ("s1", "s2", "issue", "reason")}}
        for key, k in rubric.blind(keyed).items()
    ]
    with patch.object(rubric.study, "fixtures", fixtures):
        scores = rubric.checks(keyed, annotations)
    return {f"{k.removesuffix('/record')}/final": row for k, row in scores.items()}


def episode_keys(panel, arm):
    desk = "solo" if arm == "solo" else "desk"
    return f"{panel}/{desk}/opening", f"{panel}/{arm}/reply", f"{panel}/{arm}/final"


def trace_episode(panel, arm, rows, marks, units, grades):
    opening, reply, final = episode_keys(panel, arm)
    new = units[reply].keys() - units[opening].keys()
    retained = new & units[final].keys()
    return {"final_grade": grades[final], "inputs": [opening, reply, final],
            "question": marks[opening]["question"],
            "opening_source_error": bool(marks[opening]["issue"]), "reply_source_error": bool(marks[reply]["issue"]),
            "reply_new_units": sorted(new),
            "unique_units_by_pass": [len(units[key]) for key in (opening, reply, final)],
            "retained_new_units": sorted(retained), "output_tokens": sum(len(rows[k]["output_ids"]) for k in (opening, reply, final)),
            "input_tokens": sum(len(rows[k]["input_ids"]) for k in (opening, reply, final)),
            "calls": 3, "max_output_tokens": study.OPEN_CAP + study.REPLY_CAP + study.FINAL_CAP}


def matched_pair(panel, rows):
    shared, peer_reply, peer_final = episode_keys(panel, "peer")
    independent_open, independent_reply, independent_final = episode_keys(panel, "independent")
    assert shared == independent_open

    def inputs(peer, independent):
        a, b = rows[peer], rows[independent]
        assert a["cap"] == b["cap"] and a["messages"][0] == b["messages"][0]
        return (json.loads(row["messages"][1]["content"]) for row in (a, b))

    treated, control = inputs(peer_reply, independent_reply)
    assert treated.pop("working_note_and_question") == rows[shared]["output"] and treated == control
    treated, control = inputs(peer_final, independent_final)
    peer_notes = treated.pop("working_notes")
    independent_notes = control.pop("working_notes")
    assert treated == control and peer_notes.keys() == independent_notes.keys()
    first, second = peer_notes
    assert peer_notes[first] == independent_notes[first] == rows[shared]["output"]
    assert peer_notes[second] == rows[peer_reply]["output"]
    assert independent_notes[second] == rows[independent_reply]["output"]


def score(directory):
    rows = study.verify(directory)
    marks, units = read_annotations(directory, rows)
    grades = grade(rows, marks)
    details, summaries, changes = {}, {}, {}
    for panel, *_ in study.panels():
        matched_pair(panel, rows)
        for arm in study.ARMS:
            episode = trace_episode(panel, arm, rows, marks, units, grades)
            details[f"{panel}/{arm}"] = episode
            group = summaries.setdefault(arm, Counter())
            g = episode["final_grade"]
            group.update({"episodes": 1, "strict": g["strict"], "points": g["points"],
                          "correct_disposition": g["disposition"] == g["expected"],
                          "material_guard_failures": bool(g["review"]["issue"]),
                          "questions": bool(episode["question"]),
                          "opening_source_errors": episode["opening_source_error"],
                          "reply_source_errors": episode["reply_source_error"],
                          "reply_new_units": len(episode["reply_new_units"]),
                          "retained_new_units": len(episode["retained_new_units"]),
                          "output_tokens": episode["output_tokens"], "input_tokens": episode["input_tokens"]})
        _, their_reply, their_final = episode_keys(panel, "peer")
        _, control_reply, control_final = episode_keys(panel, "independent")
        introduced = units[their_reply].keys() - units[control_reply].keys()
        new_in_final = units[their_final].keys() - units[control_final].keys()
        improvements = introduced & new_in_final
        preserved = units[their_reply].keys() & units[control_reply].keys() & new_in_final
        losses = units[control_final].keys() - units[their_final].keys()
        changes[panel] = {"peer_only_reply_units": sorted(introduced),
                          "peer_only_final_units_from_reply": sorted(improvements),
                          "shared_reply_units_retained_only_by_peer": sorted(preserved),
                          "units_lost_against_independent": sorted(losses),
                          "points_delta": grades[their_final]["points"] - grades[control_final]["points"]}
    files = (Path(__file__), Path(rubric.__file__), directory / "transcript.jsonl", directory / "review.tsv", directory / "units.tsv")
    return {
        "scope": "Two previously exposed source families and both desk orders. Live peer notes use isolated cards, solo "
                 "uses both cards every pass, and all final prompts include both cards. Calls and output caps match. "
                 "Input token counts differ. Exact-span evidence maps are authored by the same assistant. A carried "
                 "unit is paired with an independent counterfactual, while direct source access remains possible.",
        "verified_generations": len(rows), "verified_treatment_pairs": len(changes), "summary": summaries, "episodes": details, "peer_vs_independent": changes,
        "review": marks, "units": units, "sha256": {p.name: study.runner.digest(p) for p in files},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(score(parser.parse_args().directory), indent=2, ensure_ascii=False))
