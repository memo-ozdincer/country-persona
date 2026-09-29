"""Score explicit criterion ratings; this is not a semantic or model judge."""
from __future__ import annotations

from .action_eval import validate_case
from .io import digest

RATINGS = {"met", "unmet", "unratable"}
REVIEWER_KINDS = {"human", "assistant", "authored_fixture"}


def rubric_digest(reference):
    return digest({k: reference[k] for k in ("rubric_version", "criteria", "universal_checks")})


def score_policy_response(case, reference, prediction, review=None):
    validate_case(case)
    if case.get("task") != "policy_fidelity":
        raise ValueError("Expected a policy case, not an action outcome")
    for row in (reference, prediction):
        if row.get("id") != case["id"] or row.get("case_sha256") != case["case_sha256"]:
            raise ValueError("Policy case/reference/output hash or ID mismatch")
    output = prediction.get("output")
    if not isinstance(output, str) or not prediction.get("response_id"):
        raise ValueError("Expected a text response and distinct response_id")
    if "rubric_version" in reference and reference.get("rubric_sha256") != rubric_digest(reference):
        raise ValueError("Rubric hash mismatch")
    criterion_ids = [c["id"] for c in reference["criteria"]]
    check_ids = list(reference["universal_checks"])
    if not criterion_ids or len(criterion_ids) != len(set(criterion_ids)) or not check_ids:
        raise ValueError("Required criteria/checks cannot be empty or duplicated")
    expected_keys = {"criteria": set(criterion_ids), "checks": set(check_ids)}
    ratings = {"criteria": {k: "unratable" for k in criterion_ids},
               "checks": {k: "unratable" for k in check_ids}}
    if review is not None:
        if "rubric_version" in reference and review.get("rubric_sha256") != reference["rubric_sha256"]:
            raise ValueError("Review is not linked to this exact rubric version")
        if (review.get("id") != case["id"] or review.get("case_sha256") != case["case_sha256"] or
            review.get("response_id") != prediction["response_id"] or review.get("output_digest") != digest(output)):
            raise ValueError("Review is not linked to this exact output")
        if (not isinstance(review.get("reviewer_id"), str) or not review["reviewer_id"].strip() or
            review.get("reviewer_kind") not in REVIEWER_KINDS):
            raise ValueError("Reviewer identity and kind are required; fixtures are not human ratings")
        for category, keys in expected_keys.items():
            values = review.get(category)
            if not isinstance(values, dict) or set(values) != keys:
                raise ValueError("Missing or unexpected criterion/check IDs")
            if any(v not in RATINGS for v in values.values()):
                raise ValueError("Ratings must be met, unmet or unratable; a blank template is not a review")
            ratings[category] = values
    flat = [v for group in ratings.values() for v in group.values()]
    empty = not output.strip()
    if empty or "unmet" in flat:
        outcome = "fail"
    elif "unratable" in flat:
        outcome = "unresolved"
    else:
        outcome = "pass"
    criterion_values = list(ratings["criteria"].values())
    complete_content = "unratable" not in criterion_values
    return {"response_id": prediction["response_id"], "id": case["id"], "country": case["country"],
            "split_group": case["split_group"], "condition": case["condition"],
            "outcome": outcome, "empty_answer": empty, "review_supplied": review is not None,
            "reviewer_id": review["reviewer_id"] if review else None,
            "reviewer_kind": review["reviewer_kind"] if review else None,
            "rubric_sha256": reference.get("rubric_sha256"),
            "criterion_ratings": ratings["criteria"], "check_ratings": ratings["checks"],
            "criterion_rating_coverage": sum(v != "unratable" for v in criterion_values) / len(criterion_values),
            "required_content_met_rate": criterion_values.count("met") / len(criterion_values) if complete_content else None,
            "all_ratings_complete": "unratable" not in flat,
            "unsupported_material_claim": {"met": False, "unmet": True, "unratable": None}[
                ratings["checks"].get("all_material_claims_supported", "unratable")],
            "unsupported_commitment": {"met": False, "unmet": True, "unratable": None}[
                ratings["checks"]["no_unsupported_commitment"]]}


def summarize_policy_scores(rows):
    if not rows:
        raise ValueError("Cannot summarize an empty evaluation")
    if len({r["response_id"] for r in rows}) != len(rows):
        raise ValueError("Summarize one reviewer per response at a time")
    unresolved = sum(r["outcome"] == "unresolved" for r in rows)
    complete = all(r["all_ratings_complete"] for r in rows)
    return {"responses": len(rows), "event_groups": len({r["split_group"] for r in rows}),
            "passes": sum(r["outcome"] == "pass" for r in rows),
            "failures": sum(r["outcome"] == "fail" for r in rows), "unresolved": unresolved,
            "review_coverage": sum(r["review_supplied"] for r in rows) / len(rows),
            "fully_rated_fraction": sum(r["all_ratings_complete"] for r in rows) / len(rows),
            "strict_pass_rate": sum(r["outcome"] == "pass" for r in rows) / len(rows) if complete else None,
            "reviewer_kinds": sorted({r["reviewer_kind"] for r in rows if r["reviewer_kind"]}),
            "note": "Arithmetic over supplied ratings. It does not establish semantic correctness, reviewer agreement or model performance."}
