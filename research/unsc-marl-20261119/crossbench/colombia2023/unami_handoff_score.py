"""Measure calendar usability, recipient binding, and the full record separately."""
import argparse
import json
from pathlib import Path
import re

import unami_handoff as trial
from peer_question_score import verified_spans

CALENDAR = {"term_date", "review_date", "report_period"}
ACTORS = {"review_actor", "review_recipient", "review_independent", "report_actor", "report_recipient"}
FIELDS = CALENDAR | ACTORS
PROCEDURE = {"vote", "tally"}


def score(directory):
    rows = trial.replay(directory)
    annotations = trial.baseline.read(directory / "annotations.json")
    raw_path = directory / "transcript.jsonl"
    assert annotations["transcript_sha256"] == trial.runner.digest(raw_path)
    assert annotations["records"].keys() == rows.keys()
    rules = set(trial.baseline.read(trial.baseline.CASES["unami"])["rules"])
    _, vote, public, first, second = next(r for r in trial.baseline.fixtures() if r[0] == "unami")
    certified = public.keys() | first.keys() | second.keys()
    outputs = {}
    old = trial.archived()
    for uid, row in rows.items():
        annotation = annotations["records"][uid]
        text = row["output"]
        fields = verified_spans(annotation["fields"], text, FIELDS)
        met = verified_spans(annotation["met"], text, rules - PROCEDURE)
        issues = annotation["issues"]
        assert all(span and span in text and reason for span, reason in issues)
        assert annotation["cadence"] in ("wrong", "omitted", "correct")
        assert (annotation["cadence"] == "correct") == ("report_period" in fields)
        if "deliverable" in met:
            assert {"review_actor", "review_recipient", "review_independent", "review_date"} <= fields.keys()
        if "report" in met:
            assert {"report_actor", "report_recipient", "report_period"} <= fields.keys()
        cited = {key.strip() for group in re.findall(r"\[([A-Z, ]+)\]", text) for key in group.split(",")}
        words = len(text.split())
        calendar = len(fields.keys() & CALENDAR)
        historical = next((old[f"unami/{incoming}/final"]["output"] for incoming in trial.REPLIES
                           if uid == f"unami/{incoming}_plain_notes/final"), None)
        outputs[uid] = {
            "record": vote + "\n\n" + text, "fields": fields, "points": 7 * len(met.keys() | PROCEDURE),
            "met": met, "calendar_entries": calendar, "calendar_usable": calendar == len(CALENDAR),
            "full_handoff_complete": fields.keys() == FIELDS and not issues and row["ended"],
            "cadence": annotation["cadence"], "issues": issues,
            "strict": (met.keys() | PROCEDURE == rules and not issues and row["ended"]
                       and words <= trial.baseline.LIMITS["unami"] and certified <= cited <= certified | {"VOTE"}),
            "record_complete": row["ended"], "words": words, "cited_ids": sorted(cited),
            "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"]),
            "matches_historical_plain_control": historical == text if historical is not None else None,
        }
    deltas = {}
    for incoming in trial.REPLIES:
        get = lambda mode, source: outputs[f"unami/{incoming}_{mode}_{source}/final"]
        for metric in ("points", "calendar_entries"):
            deltas.setdefault(incoming, {})[metric] = {
                "report_card_with_plain": get("plain", "report_card")[metric] - get("plain", "notes")[metric],
                "binding_with_notes": get("bind", "notes")[metric] - get("plain", "notes")[metric],
                "binding_with_report_card": get("bind", "report_card")[metric] - get("plain", "report_card")[metric],
            }
    return {"review": annotations["scope"], "records": outputs, "paired_effects": deltas}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
