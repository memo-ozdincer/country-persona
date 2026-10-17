"""Prepare blank source-backed reviews or validate completed human/assistant reviews.

No semantic grade is inferred from n-grams or a loss decrease. A blank review
cannot authorize a dependent fit. Preserve earlier reviews if adjudicating.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import read_jsonl, sha256, write_json


def validate_review(review, responses, rubric, response_hash):
    if review["responses_sha256"] != response_hash or not review["reviewer"].strip() or not review["rationale"].strip():
        raise ValueError("Missing or stale review provenance")
    expected = {r["id"]: r for r in responses}
    if len(review["cases"]) != len(expected) or {r["id"] for r in review["cases"]} != set(expected):
        raise ValueError("Every complete response requires a review")
    scores = []
    for case in review["cases"]:
        answer, criteria = expected[case["id"]], rubric["cases"][case["id"]]
        if not case["complete_raw_answer_read"] or not case["notes"].strip():
            raise ValueError("Complete raw answer inspection required")
        if len(case["units"]) != len(criteria) or {u["id"] for u in case["units"]} != {u["id"] for u in criteria}:
            raise ValueError("Changed or omitted material criteria")
        for unit in case["units"]:
            if unit["status"] not in {"met", "unmet", "uncertain"} or not unit["reason"].strip():
                raise ValueError("Unfinished material review")
            if unit["status"] == "met" and (not unit["answer_quote"] or unit["answer_quote"] not in answer["output_raw"]):
                raise ValueError("A met criterion needs an actual answer quote")
        if set(case["guards"]) != set(rubric["guards"]):
            raise ValueError("Missing attribution, grounding, chronology or formatting guard")
        for guard in case["guards"].values():
            if guard["status"] not in {"pass", "fail", "uncertain"} or not guard["reason"].strip():
                raise ValueError("Unfinished guard review")
        scores.append(dict(id=case["id"], strict_pass=not answer["at_cap"]
                           and all(u["status"] == "met" for u in case["units"])
                           and all(g["status"] == "pass" for g in case["guards"].values())))
    if review["decision"] not in {"run_four_example_fit", "inspect_adapter_next", "replan", "stop"}:
        raise ValueError("Explicit evidence-based next decision required")
    return scores


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--review", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Preserve existing inspection")
    rubric_path = ROOT / "research/scenario-role-sft-20261017-v1/rubric.json"
    rubric = json.loads(rubric_path.read_text())
    responses = list(read_jsonl(a.run / "responses.jsonl"))
    response_hash = sha256(a.run / "responses.jsonl")
    if a.review:
        review = json.loads(a.review.read_text())
        if review["rubric_sha256"] != sha256(rubric_path):
            raise ValueError("Review rubric changed")
        scores = validate_review(review, responses, rubric, response_hash)
        write_json(a.output, {**review, "scores": scores, "review_file_sha256": sha256(a.review)})
    else:
        write_json(a.output, dict(responses_sha256=response_hash, rubric_sha256=sha256(rubric_path),
            reviewer="", rationale="", decision="", independent_review=False,
            cases=[dict(id=r["id"], complete_raw_answer_read=False, notes="",
                units=[dict(id=u["id"], status="", answer_quote="", reason="") for u in rubric["cases"][r["id"]]],
                guards={g: dict(status="", reason="") for g in rubric["guards"]}) for r in responses]))


if __name__ == "__main__":
    main()
