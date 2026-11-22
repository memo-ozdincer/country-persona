"""Score a small question-action table using frozen source rubrics and exact spans."""
import argparse
import json
from pathlib import Path
import re

import field_question_actions as experiment
from peer_index_transfer_score import VOTE_RULES
from peer_question_score import verified_spans

baseline = experiment.baseline
TARGETS = {
    "colombia": {"actor": {"speaker"}, "scope": {"ethnic"}},
    "unami": {"actor": {"review_actor", "review_recipient", "review_deadline"},
              "scope": {"consult_iraq", "consult_kuwait", "consult_other"}},
}


def score(directory):
    raw = experiment.replay(directory)
    label = baseline.read(directory / "annotations.json")
    assert label["transcript_sha256"] == experiment.runner.digest(directory / "transcript.jsonl")
    assert raw.keys() == label["records"].keys()
    inv = baseline.read(baseline.HERE / "peer-index-inventory.json")
    output = {}
    for family, vote, public, first, second in baseline.fixtures():
        rules = set(baseline.read(baseline.CASES[family])["rules"])
        fixed = VOTE_RULES[family]
        assert all(span in second[card] for card, span in inv[family].values())
        source_ids = public.keys() | first.keys() | second.keys()
        choices = {}
        for arm in experiment.ARMS:
            reply, record = (raw[f"{family}/{arm}/{stage}"] for stage in ("reply", "final"))
            first_read, final_read = (label["records"][row["id"]] for row in (reply, record))
            reply_ideas = verified_spans(first_read["ideas"], reply["output"], inv[family].keys())
            final_ideas = verified_spans(final_read["ideas"], record["output"], inv[family].keys())
            met = verified_spans(final_read["met"], record["output"], rules - fixed)
            for row, observed in ((reply, first_read), (record, final_read)):
                assert all(quote and quote in row["output"] and reason for quote, reason in observed["issues"])
            targets = TARGETS[family].get(arm, set())
            shared = reply_ideas.keys() & final_ideas.keys()
            cited = {s.strip() for group in re.findall(r"\[([A-Z, ]+)\]", record["output"])
                     for s in group.split(",")}
            words = len(record["output"].split())
            choices[arm] = {
                "question": experiment.ACTIONS[family].get(arm), "requested": sorted(targets),
                "reply": reply["output"], "record": vote + "\n\n" + record["output"],
                "reply_ideas": reply_ideas, "final_ideas": final_ideas, "reply_ideas_retained": sorted(shared),
                "requested_answered": sorted(targets & reply_ideas.keys()),
                "requested_retained": sorted(targets & shared),
                "reply_issues": first_read["issues"], "record_issues": final_read["issues"],
                "final_criteria": met, "points": 7 * len(fixed | met.keys()),
                "missing_source_ids": sorted(source_ids - cited),
                "complete": record["ended"], "reply_complete": reply["ended"], "words": words,
                "strict": (record["ended"] and words <= baseline.LIMITS[family] and not final_read["issues"]
                           and source_ids <= cited <= source_ids | {"VOTE"} and fixed | met.keys() == rules),
                "reply_input_tokens": len(reply["input_ids"]), "reply_output_tokens": len(reply["output_ids"]),
                "writer_output_tokens": len(record["output_ids"]),
            }
        silence = choices["no_question"]
        changes = {}
        for arm in experiment.ARMS[1:]:
            observed = choices[arm]
            survived = set(observed["reply_ideas_retained"])
            control = set(silence["reply_ideas_retained"])
            changes[arm] = {
                "same_targets_answered_without_question": sorted(TARGETS[family][arm] & silence["reply_ideas"].keys()),
                "new_retained_ideas": sorted(survived - control),
                "lost_retained_ideas": sorted(control - survived),
                "requested_added_in_final": sorted((survived - control) & TARGETS[family][arm]),
                "points_delta": observed["points"] - silence["points"],
            }
        points = {arm: record["points"] for arm, record in choices.items()}
        output[family] = {"actions": choices, "versus_no_question": changes,
                          "best_by_final_points": sorted(arm for arm, value in points.items() if value == max(points.values())),
                          "best_question_points_delta": max(points[arm] for arm in experiment.ARMS[1:]) - points["no_question"]}
    return {"review": label["scope"], "dockets": output}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
