"""Score repaired questions and track source-supported answer atoms to the record."""
import argparse
import json
from pathlib import Path
import re

import peer_question_repair as trial
from peer_question_score import verified_spans

TARGETS = {
    "unifil": {"qualification", "free_operation"},
    "haiti": {"represented_members", "haiti_request"},
}


def score(directory):
    raw = trial.replay(directory)
    review = trial.read(directory / "annotations.json")
    assert review["transcript_sha256"] == trial.runner.digest(directory / "transcript.jsonl")
    assert raw.keys() == review["rows"].keys()
    earlier = trial.archived()
    prior = trial.read(trial.SOURCE / "results.json")
    rules = {"unifil": {v["id"] for v in trial.read(trial.base.UNIFIL)["rubric"]},
             "haiti": set(trial.read(trial.base.HAITI)["rules"])}
    output = {}
    for case, vote, public, national in trial.base.fixtures():
        fixed = {"procedure", "disposition"} if case == "unifil" else {"procedure"}
        source_ids = {key.casefold() for key in public.keys() | national.keys()}
        first = earlier[f"{case}/shared/open"]
        endpoints = {}
        for arm in trial.ARMS:
            reply, final = (raw[f"{case}/{arm}/{stage}"] for stage in ("reply", "final"))
            reply_review, final_review = (review["rows"][row["id"]] for row in (reply, final))
            answers = verified_spans(reply_review["targets"], reply["output"], TARGETS[case])
            retained = verified_spans(final_review["targets"], final["output"], TARGETS[case])
            covered = verified_spans(final_review["met"], final["output"], rules[case] - fixed)
            for row, annotation in ((reply, reply_review), (final, final_review)):
                assert all(span and span in row["output"] and reason for span, reason in annotation["issues"])
            groups = re.findall(r"\[([A-Za-z0-9, ]+)\]", final["output"])
            cited = {s.strip().casefold() for group in groups for s in group.split(",")}
            length = len(final["output"].split())
            form = length <= 140 and source_ids <= cited <= source_ids | {"vote"}
            endpoints[arm] = {
                "reply": reply["output"], "supplement": final["output"], "record": vote + "\n\n" + final["output"],
                "answered": answers, "retained": retained, "retained_from_reply": sorted(answers.keys() & retained.keys()),
                "met": covered, "points": (len(covered) + len(fixed)) * 7,
                "reply_issues": reply_review["issues"], "record_issues": final_review["issues"],
                "words": length, "missing_source_ids": sorted(source_ids - cited), "complete": final["ended"],
                "strict": form and final["ended"] and not final_review["issues"] and covered.keys() | fixed == rules[case],
                "input_tokens_including_reused_opening": sum(len(r["input_ids"]) for r in (first, reply, final)),
                "output_tokens_including_reused_opening": sum(len(r["output_ids"]) for r in (first, reply, final)),
            }
        answerable = endpoints["answerable"]
        contrast = {}
        for control in ("original", "no_question"):
            control_row = endpoints[control]
            contrast[control] = {
                "additional_supported_answers": sorted(answerable["answered"].keys() - control_row["answered"].keys()),
                "additional_answers_retained": sorted(set(answerable["retained_from_reply"]) - set(control_row["retained_from_reply"])),
                "points_delta": answerable["points"] - control_row["points"],
            }
        previous_reply = earlier[f"{case}/interactive/reply"]
        previous_final = earlier[f"{case}/interactive/final"]
        output[case] = {"same_batch": endpoints, "answerable_minus": contrast,
                        "archived_original_reply_exact": previous_reply["output"] == endpoints["original"]["reply"],
                        "archived_original_final_exact": previous_final["output"] == endpoints["original"]["supplement"],
                        "archived_independent_points": prior["families"][case]["criteria"]["independent"]["points"]}
    return {"review": review["scope"], "cases": output}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
