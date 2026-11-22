"""Audit the question, received witness and final brief as separate steps."""
import argparse
import csv
import json
from pathlib import Path
import re
from unittest.mock import patch

import facilitator_clarification as study
import facilitator_deliberation_score as rubric
import facilitator_fresh_brief_score as grade


def fixtures():
    for panel, proposal, _, expected, _, cards, _, _, _ in study.source_inputs():
        sources = {f"S{i+1}": card[1] for i, card in enumerate(cards)}
        for arm in study.ARMS:
            yield f"{panel}/{arm}", proposal, sources, rubric.RELATIONS[expected], frozenset({0, 1}), {}, {}


def split(rows):
    return tuple({key: row for key, row in rows.items() if key.endswith(suffix)}
                 for suffix in ("/question", "/answer", "/final"))


def review(rows):
    questions, answers, finals = split(rows)
    packet = grade.review_inputs(finals)
    for item in packet:
        for field in ("working_notes", "question", "answering_speaker", "working_answer"):
            item.pop(field)
    notes = []
    for name, key in grade.blind(answers).items():
        row = answers[key]
        payload = json.loads(row["messages"][1]["content"])
        payload.pop("peer_question", None)
        notes.append({"id": name, **payload, "response": row["output"], "finished": row["ended"]})
    public_questions = [{"case": key.split("/")[0], "response": row["output"],
                         "visible_to_asker": json.loads(row["messages"][1]["content"])}
                        for key, row in questions.items()]
    return {"question_review": public_questions, "reply_review": notes, "final_review": packet}


def audited_answers(raw, references):
    by_id = grade.blind(raw)
    marks = {m["id"]: m for m in references}
    assert by_id.keys() == marks.keys() and len(marks) == len(references)
    scenarios = {r[0]: r for r in study.source_inputs()}
    result = {}
    for alias, key in by_id.items():
        row = raw[key]
        raw_label, delimiter, excerpt = row["output"].partition("|")
        label = raw_label.strip().casefold()
        excerpt = excerpt.strip()
        case = scenarios[key.split("/")[0]]
        _, _, _, expected, _, cards, _, target, _ = case
        answer_key = rubric.RELATIONS[expected][target]
        within_card = bool(excerpt and excerpt in cards[target][1])
        parsed = (bool(row["ended"] and delimiter) and
                  (within_card if label in ("supports", "contradicts") else label == "unknown" and (not excerpt or within_card)))
        mark = marks[alias]
        decisive = mark["decisive_span"]
        assert decisive in row["output"]
        assert not parsed or not decisive or decisive in excerpt
        assert bool(mark["issue"]) == bool(mark["reason"])
        assert mark["issue"] in row["output"]
        soft_label = re.match(r"(supports|contradicts|unknown)\b", row["output"], re.IGNORECASE)
        soft_relation = soft_label[1].casefold() if soft_label else None
        cited = excerpt[1:-1] if excerpt and excerpt[0] == excerpt[-1] == '"' else excerpt
        result[key] = {"printed_relation": label if delimiter else None, "expected_relation": answer_key,
                       "relation_before_format_check": soft_relation,
                       "literal_excerpt_ignoring_outer_quotes": bool(cited and cited in cards[target][1]),
                       "format_and_provenance": parsed,
                       "correct_relation": label == answer_key,
                       "usable": parsed and label == answer_key and bool(decisive) and not mark["issue"],
                       "semantically_usable": soft_relation == answer_key and bool(decisive) and not mark["issue"],
                       "review": mark}
    return result


def outcomes(directory, rows):
    questions, answers, finals = split(rows)
    with patch.object(grade.study, "fixtures", fixtures):
        final_grades = grade.checks(finals, rubric.annotations(directory, "final-review.tsv"))
    reply_grades = audited_answers(answers, rubric.annotations(directory, "reply-review.tsv"))
    question_grades = {row["case"]: row for row in rubric.annotations(directory, "question-review.tsv")}
    assert question_grades.keys() == {k.split("/")[0] for k in questions}
    for case, judgement in question_grades.items():
        assert judgement["target_span"] and judgement["target_span"] in questions[f"{case}/question"]["output"]
    episodes = {}
    for panel, _, _, expected, _, _, _, target, _ in study.source_inputs():
        q = questions[f"{panel}/question"]
        episodes[panel] = {}
        for arm in study.ARMS:
            key = f"{panel}/{arm}"
            final = finals[f"{key}/final"]
            gradebook = final_grades[f"{key}/final"]
            reply = reply_grades.get(f"{key}/answer")
            path = [q, final] if reply is None else [q, answers[f"{key}/answer"], final]
            episodes[panel][arm] = {
                "question": q["output"], "reply": reply,
                "correct_printed_heading": rubric.printed_heading(final["output"]) == expected,
                "answering_side_in_final": gradebook["criteria"][f"side_{target+1}"] == 12,
                "final": gradebook, "calls": len(path), "input_tokens": sum(len(r["input_ids"]) for r in path),
                "output_tokens": sum(len(r["output_ids"]) for r in path),
            }
    summary = {}
    for arm in study.ARMS:
        records = [x[arm] for x in episodes.values()]
        summary[arm] = {"mean_final_points": sum(x["final"]["points"] for x in records) / len(records),
                        "strict": sum(x["final"]["strict"] for x in records),
                        "correct_printed_heading": sum(x["correct_printed_heading"] for x in records),
                        "answering_side_in_final": sum(x["answering_side_in_final"] for x in records),
                        "usable_reply": sum(bool(x["reply"] and x["reply"]["usable"]) for x in records),
                        "semantically_usable_reply": sum(bool(x["reply"] and x["reply"]["semantically_usable"]) for x in records),
                        **{m: sum(x[m] for x in records) for m in ("calls", "input_tokens", "output_tokens")}}
    paired = {panel: {"same_reply": answers[f"{panel}/asked/answer"]["output"] == answers[f"{panel}/independent/answer"]["output"],
                      "same_chair_messages": finals[f"{panel}/asked/final"]["messages"] == finals[f"{panel}/independent/final"]["messages"],
                      "same_chair_token_ids": finals[f"{panel}/asked/final"]["input_ids"] == finals[f"{panel}/independent/final"]["input_ids"],
                      "same_final": finals[f"{panel}/asked/final"]["output"] == finals[f"{panel}/independent/final"]["output"],
                      "asked_minus_independent_points": arms["asked"]["final"]["points"] - arms["independent"]["final"]["points"]}
              for panel, arms in episodes.items()}
    return {"scope": "Four exposed dossiers with fixed question recipient, unchanged private cards and same-assistant arm-hidden "
                     "review. The paired arms deliver the same question to the chair and vary its visibility at the answering desk. "
                     "The no-reply control uses fewer calls. No policy or model weight updates.",
            "summary": summary, "paired": paired, "questions": question_grades, "episodes": episodes,
            "inputs_sha256": {p: study.runner.digest(directory / p)
                              for p in ("transcript.jsonl", "question-review.tsv", "reply-review.tsv", "final-review.tsv")}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("review", "score"))
    p.add_argument("directory", type=Path)
    args = p.parse_args()
    rows = study.read(args.directory)
    result = review(rows) if args.mode == "review" else outcomes(args.directory, rows)
    print(json.dumps(result, indent=2, ensure_ascii=False))
