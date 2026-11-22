"""Review source-bound notes and chair records with exact spans and matched histories."""
import argparse
import csv
import json
from pathlib import Path
import re
from unittest.mock import patch

import facilitator_deliberation as study
import facilitator_fresh_brief_score as score

# Warrant targets keep the named institution, actor and force separate.
WARRANTS = {
    "bosnia-0": (
        "Tie the affirmative vote to renewal of EUFOR-Althea or resolution 2757.",
        "Tie the affirmative vote to renewal of EUFOR-Althea or resolution 2757.",
    ),
    "bosnia-1": (
        "Say the High Representative helps uphold the Dayton Peace Agreement.",
        "Explain that Russia considered the Office's functions exhausted or wanted closure promptly.",
    ),
    "afghanistan-0": (
        "Preserve the one-year period and distinguish China's welcome from Council adoption.",
        "Preserve the one-year period and distinguish Pakistan's affirmative vote from Council adoption.",
    ),
    "afghanistan-1": (
        "Separate China's February initiation of consultations or March cooperation with Denmark from circulation of the draft.",
        "Distinguish China and Pakistan's initial circulation from Denmark's facilitation as Council President.",
    ),
}
RELATIONS = {"retain": ("supports", "supports"), "revise": ("supports", "contradicts"),
             "withhold": ("unknown", "supports")}


def grade_fixtures():
    for panel, proposal, _, target, _, cards in study.fixtures():
        sources = {f"S{i+1}": c[1] for i, c in enumerate(cards)}
        for arm in study.ARMS:
            yield f"{panel}/{arm}", proposal, sources, RELATIONS[target], frozenset({0, 1}), {}, {}


def review(rows):
    chair, notes = {}, {}
    panels = {r[0]: r for r in study.fixtures()}
    for key, row in rows.items():
        target = chair if key.endswith("/final") else notes
        target[key] = row
    final_packet = score.review_inputs(chair)
    for row in final_packet:
        row.pop("working_notes")
    note_packet = []
    for alias, key in score.blind(notes).items():
        row = notes[key]
        panel, _, phase = key.split("/")
        source_index = int(phase[-1]) - 1
        _, _, _, _, rubric, cards = panels[panel]
        note_packet.append({"id": alias, "speaker": cards[source_index][0], "source": cards[source_index][1],
                            "required_position": rubric[source_index], "warrant_target": WARRANTS[panel][source_index],
                            "response": row["output"], "finished": row["ended"]})
    return {"finals": final_packet, "notes": note_packet}


def annotations(directory, name):
    with (directory / name).open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def grade_notes(raw, notes):
    ids = score.blind(raw)
    marks = {row["id"]: row for row in notes}
    assert ids.keys() == marks.keys() and len(notes) == len(marks)
    output = {}
    for alias, key in ids.items():
        row = raw[key]
        record = marks[alias]
        assert all(record[k] in row["output"] for k in ("point", "warrant", "issue"))
        assert bool(record["issue"]) == bool(record["reason"])
        output[key] = {"review_id": alias, "meets_point": bool(record["point"]) and not record["issue"],
                       "meets_warrant": bool(record["warrant"]) and not record["issue"],
                       "critical_error": bool(record["issue"]), "within_limit": row["ended"] and len(row["output"].split()) <= 21,
                       "annotation": record}
    return output


def outcomes(directory, rows):
    chair = {k: v for k, v in rows.items() if k.endswith("/final")}
    drafts = {k: v for k, v in rows.items() if k not in chair}
    note_marks = grade_notes(drafts, annotations(directory, "note-review.tsv"))
    with patch.object(score.study, "fixtures", grade_fixtures):
        chair_marks = score.checks(chair, annotations(directory, "final-review.tsv"))
    trajectory = {}
    for panel, _, _, _, _, _ in study.fixtures():
        trajectory[panel] = {}
        for arm in study.ARMS:
            start = "solo" if arm == "solo" else "private"
            opening = [f"{panel}/{start}/opening{i+1}" for i in range(2)]
            revised = [f"{panel}/{arm}/revision{i+1}" for i in range(2)]
            final = f"{panel}/{arm}/final"
            trace = [*opening, *revised, final]
            coverage = [{metric: sum(note_marks[k][metric] for k in stage) for metric in ("meets_point", "meets_warrant", "critical_error")}
                        for stage in (opening, revised)]
            pairs = []
            for first, latest in zip(opening, revised, strict=True):
                notes = note_marks[first], note_marks[latest]
                pairs.append({"opening": first, "revision": latest, "changed": drafts[first]["output"] != drafts[latest]["output"],
                              "point_delta": int(notes[1]["meets_point"]) - int(notes[0]["meets_point"]),
                              "warrant_delta": int(notes[1]["meets_warrant"]) - int(notes[0]["meets_warrant"])})
            trajectory[panel][arm] = {"calls": len(trace), "caps": sum(rows[k]["cap"] for k in trace),
                                      "input_tokens": sum(len(rows[k]["input_ids"]) for k in trace),
                                      "output_tokens": sum(len(rows[k]["output_ids"]) for k in trace),
                                      "peer_messages_visible": 2 if arm == "peer" else 0,
                                      "local_coverage": coverage, "changes": pairs, "final": chair_marks[final]}
    comparison = {}
    for arm in study.ARMS:
        data = [item[arm] for item in trajectory.values()]
        comparison[arm] = {k: sum(row[k] for row in data) for k in ("calls", "input_tokens", "output_tokens")}
        comparison[arm].update({"mean_final_points": sum(r["final"]["points"] for r in data) / len(data),
                                "strict": sum(r["final"]["strict"] for r in data),
                                "false_action": sum(r["final"]["false_action"] for r in data),
                                "correct_printed_heading": sum(
                                    printed_heading(chair[f"{panel}/{arm}/final"]["output"]) == lanes[arm]["final"]["expected"]
                                    for panel, lanes in trajectory.items()),
                                "revised_points_recovered": sum(r["local_coverage"][1]["meets_point"] for r in data),
                                "revised_warrants_preserved": sum(r["local_coverage"][1]["meets_warrant"] for r in data)})
    paired = {}
    for panel in trajectory:
        note_changes = []
        for i in (1, 2):
            independent = f"{panel}/independent/revision{i}"
            peer = f"{panel}/peer/revision{i}"
            note_changes.append({"side": i, "same_text": drafts[independent]["output"] == drafts[peer]["output"],
                                 "point_delta": int(note_marks[peer]["meets_point"]) - int(note_marks[independent]["meets_point"]),
                                 "warrant_delta": int(note_marks[peer]["meets_warrant"]) - int(note_marks[independent]["meets_warrant"])})
        paired[panel] = {"revision_pairs": note_changes,
                         "same_final_text": chair[f"{panel}/independent/final"]["output"] == chair[f"{panel}/peer/final"]["output"],
                         "final_point_delta": trajectory[panel]["peer"]["final"]["points"] - trajectory[panel]["independent"]["final"]["points"]}
    return {"scope": "Matched five-call paths with documented peer text visibility and same-assistant arm-hidden review. "
                     "Source cards are author paraphrases. The chair sees both cards. No learned policy or acknowledgment "
                     "router operates in this language-only experiment.",
            "summary": comparison, "paired_peer_intervention": paired, "trajectories": trajectory, "notes": note_marks,
            "inputs_sha256": {name: study.runner.digest(directory / name)
                              for name in ("transcript.jsonl", "note-review.tsv", "final-review.tsv")}}


def printed_heading(text):
    first = re.match(r"(retain|revise|withhold)\b", text, re.IGNORECASE)
    return first[1].casefold() if first else None


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("review", "score"))
    p.add_argument("directory", type=Path)
    args = p.parse_args()
    rows = study.read(args.directory)
    output = review(rows) if args.mode == "review" else outcomes(args.directory, rows)
    print(json.dumps(output, ensure_ascii=False, indent=2))
