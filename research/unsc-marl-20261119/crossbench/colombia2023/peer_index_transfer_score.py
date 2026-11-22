"""Score generated questions, source-supported responses, and final-record retention."""
import argparse
import json
from pathlib import Path
import re

import peer_index_transfer as trial
from peer_question_score import verified_spans


VOTE_RULES = {"colombia": {"procedure"}, "unami": {"vote", "tally"}}


def score(directory):
    rows = trial.replay(directory)
    annotations = trial.read(directory / "annotations.json")
    assert annotations["transcript_sha256"] == trial.runner.digest(directory / "transcript.jsonl")
    inventory_path = trial.HERE / "peer-index-inventory.json"
    locked_inventory = trial.read(inventory_path)
    assert annotations["inventory_sha256"] == trial.runner.digest(inventory_path)
    output = {}
    for family, vote, public, first, second in trial.fixtures():
        rubric = trial.read(trial.CASES[family])["rules"]
        fixed = VOTE_RULES[family]
        notes = annotations["cases"][family]
        inventory = locked_inventory[family]
        source = public | first | second
        for key, (source_id, quote) in inventory.items():
            assert source_id in second and quote in source[source_id], key
        idea_keys = set(inventory)
        opening = rows[f"{family}/common/open"]
        assert all(span and span in opening["output"] and why for span, why in notes["opening_issues"])
        arms = {}
        for arm in trial.ARMS:
            reply = rows[f"{family}/{arm}/reply"]
            final = rows[f"{family}/{arm}/final"]
            review = notes["arms"][arm]
            supplied = set()
            if arm != "no_question":
                question = rows[f"{family}/{arm}/question"]
                assessment = review["question"]
                assert assessment["span"] in question["output"]
                assert assessment["reason"] and assessment["answerability"] in {"full", "partial", "none"}
                supplied = set(assessment["answerable_from_second_desk"])
                assert supplied <= idea_keys
                assert (assessment["answerability"] == "none") == (not supplied)
            else:
                assert review["question"] is None
            replied = verified_spans(review["reply"]["ideas"], reply["output"], idea_keys)
            retained = verified_spans(review["final"]["ideas"], final["output"], idea_keys)
            points = verified_spans(review["final"]["met"], final["output"], rubric.keys() - fixed)
            for row, annotation in ((reply, review["reply"]), (final, review["final"])):
                assert all(span and span in row["output"] and why for span, why in annotation["issues"])
            cited = {value.strip() for group in re.findall(r"\[([A-Z, ]+)\]", final["output"])
                     for value in group.split(",")}
            missing = source.keys() - cited
            extra = cited - source.keys() - {"VOTE"}
            words = len(final["output"].split())
            complete = final["ended"]
            trail = [rows[uid] for uid in reply["seen"]] + [rows[f"{family}/common/open"], reply, final]
            arms[arm] = {
                "question": review["question"], "asked_and_answered": sorted(supplied & replied.keys()),
                "asked_answered_and_retained": sorted(supplied & replied.keys() & retained.keys()),
                "reply_ideas": replied, "retained_ideas": retained, "retained_from_reply": sorted(replied.keys() & retained.keys()),
                "reply_issues": review["reply"]["issues"], "record_issues": review["final"]["issues"],
                "record_points": 7 * (len(points) + len(fixed)), "met": points, "record": vote + "\n\n" + final["output"],
                "complete": complete, "words": words, "missing_ids": sorted(missing), "unknown_ids": sorted(extra),
                "strict": complete and words <= trial.LIMITS[family] and not missing and not extra
                and not review["final"]["issues"] and points.keys() | fixed == rubric.keys(),
                "total_calls": len(trail), "output_tokens": sum(len(row["output_ids"]) for row in trail),
                "input_tokens": sum(len(row["input_ids"]) for row in trail),
            }
        indexed = arms["indexed"]
        output[family] = {"arms": arms, "recipient_idea_sources": inventory,
                          "shared_opening": opening["output"], "shared_opening_issues": notes["opening_issues"],
                          "indexed_vs_controls": {control: {
                              "new_reply_ideas": sorted(indexed["reply_ideas"].keys() - other["reply_ideas"].keys()),
                              "new_retained_ideas": sorted(set(indexed["retained_from_reply"]) - set(other["retained_from_reply"])),
                              "lost_retained_ideas": sorted(set(other["retained_from_reply"]) - set(indexed["retained_from_reply"])),
                              "points_delta": indexed["record_points"] - other["record_points"],
                          } for control, other in arms.items() if control != "indexed"}}
    return {"review": annotations["scope"], "dockets": output}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    a = parser.parse_args()
    print(json.dumps(score(a.directory), ensure_ascii=False, indent=2))
