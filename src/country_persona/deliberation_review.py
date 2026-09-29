"""Bind explicit reviews to interaction outputs; missing ratings never imply quality."""
from .action_eval import validate_case
from .deliberation import COUNTRIES, transition_metrics
from .io import digest

REVIEW_GUIDANCE = (
    "Met means the answer preserves the supported position and material qualifications without contradicting it elsewhere. A matching phrase is insufficient: appending a correct statement while retaining an incompatible earlier claim is not a successful correction.",
    "Use unmet for an incorrect or omitted required point; use unratable when evidence or the criterion itself is ambiguous and explain why. Equivalent supported wording is acceptable.",
    "Source silence is not proof of rejection or non-approval. A cited record must support the attributed event and date, not merely share a matching document symbol. Review capped answers as delivered; do not infer a missing ending.",
)


def review_item(row, reference):
    case = row["case"]
    validate_case(case)
    if any(row[k] != case[k] for k in ("id", "case_sha256", "scenario_id", "scenario_sha256", "stage", "condition", "country")):
        raise ValueError("Transcript metadata disagrees with its exact case")
    if reference["scenario_id"] != row["scenario_id"] or reference["scenario_sha256"] != row["scenario_sha256"]:
        raise ValueError("Review reference belongs to a different scenario")
    if not isinstance(row.get("output"), str) or not row.get("response_id"):
        raise ValueError("Missing response text or identity")
    units = {}
    if row["stage"] == "synthesis":
        units = {"synthesis." + k: v for k, v in reference["synthesis_checks"].items()}
    else:
        countries = COUNTRIES if row["country"] == "ALL" else (row["country"],)
        for country in countries:
            rubric = reference["national_policy_rubrics"][country]
            for criterion in rubric["criteria"]:
                units[f"{country}.content.{criterion['id']}"] = criterion["description"]
            units.update({f"{country}.check.{k}": v for k, v in rubric["universal_checks"].items()})
    if not units:
        raise ValueError("Empty review rubric")
    return {"response_id": row["response_id"], "id": row["id"], "case_sha256": row["case_sha256"],
            "output_digest": digest(row["output"]), "units_sha256": digest(units), "units": units,
            "guidance_sha256": digest(REVIEW_GUIDANCE),
            "rubric_status": "proposed_independent_construct_review_pending"}


def review_template(item):
    return {**{k: item[k] for k in ("response_id", "id", "case_sha256", "output_digest", "units_sha256", "guidance_sha256")},
            "reviewer_id": None, "reviewer_kind": None,
            "ratings": {k: None for k in item["units"]}, "notes": None}


def review_completion(result, references):
    """Coverage is not independent validation, even when some reviews exist."""
    fully_rated = sum(r["all_ratings_complete"] for r in result["scores"])
    source_review_pending = any(r.get("independent_review_status") != "complete" for r in references)
    human_only = result["reviewer_kinds"] == ["human"]
    return {"responses": result["responses"], "ratings_supplied": result["reviewed_responses"],
            "fully_rated_responses": fully_rated,
            "rating_completion_pending": fully_rated != result["responses"],
            "reviewer_kinds": result["reviewer_kinds"],
            "independent_construct_review_pending": source_review_pending,
            "semantic_review_pending": fully_rated != result["responses"] or not human_only or source_review_pending,
            "independence_note": "Reviewer labels alone do not prove independent collection or validate the construct."}


def score_deliberation(rows, references, reviews=()):
    """One review per response (one reviewer or an explicitly adjudicated set)."""
    if not rows or len({r["response_id"] for r in rows}) != len(rows):
        raise ValueError("Empty or duplicate response set")
    reference_index = {r["scenario_id"]: r for r in references}
    review_index = {r["response_id"]: r for r in reviews}
    if len(review_index) != len(reviews) or set(review_index) - {r["response_id"] for r in rows}:
        raise ValueError("Duplicate or unknown reviews; score reviewers separately")
    indexed, scored = {}, []
    for row in rows:
        item = review_item(row, reference_index[row["scenario_id"]])
        review = review_index.get(row["response_id"])
        ratings = {k: "unratable" for k in item["units"]}
        if review is not None:
            if any(review.get(k) != item[k] for k in ("id", "case_sha256", "output_digest", "units_sha256", "guidance_sha256")):
                raise ValueError("Review is not bound to this exact case, output, rubric and guidance")
            if not isinstance(review.get("reviewer_id"), str) or not review["reviewer_id"].strip() or review.get("reviewer_kind") not in {"human", "assistant", "authored_fixture"}:
                raise ValueError("Explicit reviewer identity/kind required")
            if set(review["ratings"]) != set(ratings) or any(v not in {"met", "unmet", "unratable"} for v in review["ratings"].values()):
                raise ValueError("Expected explicit ratings for every unit; blank templates are not reviews")
            ratings = review["ratings"]
        content = {k: v for k, v in ratings.items() if ".content." in k or k.startswith("synthesis.")}
        checks = {k: v for k, v in ratings.items() if ".check." in k}
        complete = all(v != "unratable" for v in ratings.values())
        # Strict pass is a conjunction. One known failure is decisive even if
        # another unit remains ambiguous; uncertainty must not hide known errors.
        known_failure = not row["output"].strip() or "unmet" in ratings.values()
        strict_pass = False if known_failure else (True if complete else None)
        result = {"response_id": row["response_id"], "scenario_id": row["scenario_id"], "country": row["country"],
                  "stage": row["stage"], "condition": row["condition"], "ratings": ratings,
                  "reviewer_kind": review["reviewer_kind"] if review else None,
                  "reviewer_id": review["reviewer_id"] if review else None,
                  "rating_coverage": sum(v != "unratable" for v in ratings.values()) / len(ratings),
                  "all_ratings_complete": complete,
                  "content_met_rate": list(content.values()).count("met") / len(content) if "unratable" not in content.values() else None,
                  "known_failed_checks": [k for k, v in checks.items() if v == "unmet"],
                  "known_failure": bool(known_failure), "strict_pass": strict_pass}
        key = (row["scenario_id"], row["condition"], row["country"], row["stage"])
        if key in indexed:
            raise ValueError("Duplicate scenario/condition/country/stage")
        indexed[key] = result
        scored.append(result)
    transitions = []
    for (scenario, condition, country, stage), after in indexed.items():
        if stage not in ("revision", "central_revision"):
            continue
        initial_stage = "initial" if stage == "revision" else "central_initial"
        before = indexed.get((scenario, condition, country, initial_stage))
        if before is None:
            raise ValueError("Revision lacks its initial response")
        content_before = {k: v for k, v in before["ratings"].items() if ".content." in k}
        content_after = {k: v for k, v in after["ratings"].items() if ".content." in k}
        checks_before = {k: v for k, v in before["ratings"].items() if ".check." in k}
        checks_after = {k: v for k, v in after["ratings"].items() if ".check." in k}
        transitions.append({"scenario_id": scenario, "condition": condition, "country": country,
                            "content": transition_metrics(content_before, content_after),
                            "checks": transition_metrics(checks_before, checks_after)})
    contrasts = []
    for scenario in sorted({r["scenario_id"] for r in rows}):
        pairs = []
        for country in COUNTRIES:
            values = {t["condition"]: t["content"]["content_change"] for t in transitions
                      if t["scenario_id"] == scenario and t["country"] == country}
            a, b = values.get("independent_revision"), values.get("peer_revision")
            pairs.append({"country": country, "peer_minus_self_revision_change": b - a if a is not None and b is not None else None})
        complete = all(p["peer_minus_self_revision_change"] is not None for p in pairs)
        contrasts.append({"scenario_id": scenario, "country_pairs": pairs,
                          "country_macro_peer_gain": sum(p["peer_minus_self_revision_change"] for p in pairs) / len(pairs) if complete else None})
    return {"responses": len(rows), "reviewed_responses": len(reviews), "event_groups": len(reference_index),
            "guidance_sha256": digest(REVIEW_GUIDANCE),
            "reviewer_kinds": sorted({r["reviewer_kind"] for r in reviews}),
            "scores": scored, "initial_to_revision": transitions, "paired_deliberation_contrasts": contrasts,
            "limits": ["Arithmetic over explicit ratings, not a semantic judge or evidence of independent human review.",
                       "Proposed rubric requires independent construct review; synthesis units are not interchangeable with national content units.",
                       "Country responses within an event are dependent; two exposed events do not support generalization or significance claims.",
                       "Agreement alone earns no quality credit; source-supported common ground and preserved differences require review."]}
