"""Verify checklist fields and replay the unchanged policies with composition."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

from duplicate_card_hybrid import cited_ids
from duplicate_card_qualification import QUALIFICATION, suite
from duplicate_card_transfer import CASE
from duplicate_card_transfer_routes import run as route_rollout
import source_record_review as reviewer

FIELDS = {
    "vote": "China abstained.",
    "objection": "Russia's views were not taken on board.",
    "consultations": "China said there was still time for consultations.",
    "panel": "China supported the Panel's independent work.",
    "time_limit": "China supported a time limit on the sanctions.",
    "reviews": "China supported periodic reviews of the sanctions.",
}


def bundle(directory):
    old_path = directory.with_name("dprk") / "transcript.jsonl"
    old_rows = [json.loads(line) for line in old_path.read_text().splitlines()]
    base, = (row for row in old_rows if row["evidence_ids"] == ["CHINA"])
    raw = [json.loads(line) for line in (directory / "transcript.jsonl").read_text().splitlines()]
    for expected, row in zip(suite(), raw, strict=True):
        assert all(row[key] == value for key, value in expected.items())
    candidates = {row["id"].split("/")[-2]: row for row in [base, *raw]}
    deck = {}
    for name, row in candidates.items():
        packet = json.loads(row["messages"][-1]["content"])["evidence"]
        deck[name] = {"criteria": FIELDS, "evidence": packet, "candidate": row["output"]}
    assert deck["same_card"]["evidence"] == deck["CHINA"]["evidence"]
    original = deck["same_card"]["evidence"]["CHINA"]
    assert deck["withheld_qualification"]["evidence"]["CHINA"] == original.replace(QUALIFICATION, "", 1)
    return deck, candidates, old_rows


def evaluate(directory):
    deck, candidates, old_rows = bundle(directory)
    annotation_path = directory / "annotations.json"
    annotations = json.loads(annotation_path.read_text())
    with patch.object(reviewer, "bundle", return_value=(deck, {name: name for name in deck})):
        grades = reviewer.score(directory, annotations)

    cases = {}
    for name, row in candidates.items():
        units = annotations["reviews"][name]["units"]
        covered = [field for field, mark in units.items() if mark[0] == "met"]
        cites = cited_ids(row["output"])
        cases[name] = {
            "fields": covered,
            "missing": [field for field in FIELDS if field not in covered],
            "guard": grades[name]["critical_guard"], "words": grades[name]["words"],
            "tokens": len(row["output_ids"]), "ended": row["ended"], "cited_ids": sorted(cites),
            "eligible_for_hybrid": len(covered) == len(FIELDS) and grades[name]["critical_guard"] == "clear"
                                   and row["ended"] and cites <= {"CHINA"},
        }
    old_review = json.loads((directory.with_name("dprk") / "scores.json").read_text())
    old_raw = directory.with_name("dprk") / "transcript.jsonl"
    assert old_review["transcript_sha256"] == sha256(old_raw.read_bytes()).hexdigest()
    assert old_review["component_scores"]["JAPAN"]["floor"] == 7
    assert old_review["component_scores"]["JAPAN"]["critical_guard"] == "clear"
    japan, = (row for row in old_rows if row["evidence_ids"] == ["JAPAN"])
    assert japan["ended"]
    case = json.loads(CASE.read_text())
    routes = route_rollout()
    compositions = {}
    for name in ("same_card", "reordered_card"):
        accepted = {"JAPAN": japan["output"]}
        if cases[name]["eligible_for_hybrid"]:
            accepted["CHINA"] = candidates[name]["output"]
        compositions[name] = compose(case, routes, old_review, accepted)
    withheld = cases["withheld_qualification"]
    return {"scope": annotations["scope"],
            "annotation_sha256": sha256(annotation_path.read_bytes()).hexdigest(),
            "source_transcript_sha256": sha256((directory / "transcript.jsonl").read_bytes()).hexdigest(),
            "field_checks": cases,
            "withheld_control_passed": withheld["missing"] == ["consultations"] and withheld["guard"] == "clear",
            "primary_original_order": compositions["same_card"],
            "source_order_diagnostic": compositions["reordered_card"]}


def compose(case, routes, old_review, accepted):
    slots = (None, *routes["slots"])
    bodies = {}
    for receipt in old_review["four_records"]:
        received = receipt["received"]
        roles = {name: accepted[name] for name in received if name in accepted}
        clauses = [text if name in cited_ids(text) else f"{text} [{name}]" for name, text in roles.items()]
        result = "\n\n".join([case["public_reference"], *clauses, case["analysis"]])
        assert cited_ids(result) == set(case["public"]) | set(roles)
        assert len(result.split()) <= 160
        bodies[frozenset(received)] = {
            "received": received, "covered_accounts": list(roles), "unedited_model_clauses": roles,
            "record": result, "words": len(result.split()), "authored_plus_reviewed_points": 56 + 7 * len(roles),
        }
    metrics = {}
    for prior, arms in routes["arms"].items():
        metrics[prior] = {}
        for arm, entry in arms.items():
            paired = [(w["probability"], bodies[frozenset(slots[action] for action in w["actions"] if action)])
                      for w in entry["worlds"]]
            metrics[prior][arm] = {
                "prior_writer_points": old_review["arms"][prior][arm]["mean_hybrid_points"],
                "new_writer_points": sum(p * r["authored_plus_reviewed_points"] for p, r in paired),
                "both_accounts_probability": sum(p for p, r in paired if len(r["covered_accounts"]) == 2),
                "china_account_probability": sum(p for p, r in paired if "CHINA" in r["covered_accounts"]),
                "routing_reward_unchanged": entry["net"],
            }
    return {"four_records": list(bodies.values()), "arms": metrics}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--score", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.directory) if args.score else bundle(args.directory)[0]
    print(json.dumps(result, indent=2, ensure_ascii=False))
