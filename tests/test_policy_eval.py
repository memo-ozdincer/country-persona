from copy import deepcopy

import pytest

from country_persona.io import digest
from country_persona.policy_eval import rubric_digest, score_policy_response, summarize_policy_scores


@pytest.fixture
def example():
    case = {"id": "case", "country": "IND", "split_group": "event", "condition": "B",
            "task": "policy_fidelity", "prompt": [{"role": "user", "content": "Explain the qualification."}]}
    case["case_sha256"] = digest(case)
    ref = {"id": "case", "case_sha256": case["case_sha256"],
           "criteria": [{"id": "position"}, {"id": "qualification"}],
           "universal_checks": {"no_unsupported_commitment": "No invention", "correct_attribution": "Right speaker"}}
    prediction = {"id": "case", "case_sha256": case["case_sha256"], "response_id": "response",
                  "output": "A position and its qualification."}
    review = {"id": "case", "case_sha256": case["case_sha256"], "response_id": "response",
              "output_digest": digest(prediction["output"]), "reviewer_id": "fixture", "reviewer_kind": "authored_fixture",
              "criteria": {"position": "met", "qualification": "met"},
              "checks": {"no_unsupported_commitment": "met", "correct_attribution": "met"}}
    return case, ref, prediction, review


def test_missing_material_qualification_fails_despite_other_success(example):
    case, ref, prediction, review = example
    review["criteria"]["qualification"] = "unmet"
    score = score_policy_response(case, ref, prediction, review)
    assert score["outcome"] == "fail"
    assert score["required_content_met_rate"] == 0.5


def test_full_required_content_cannot_compensate_for_invention(example):
    case, ref, prediction, review = example
    review["checks"]["no_unsupported_commitment"] = "unmet"
    score = score_policy_response(case, ref, prediction, review)
    assert score["required_content_met_rate"] == 1
    assert score["outcome"] == "fail" and score["unsupported_commitment"] is True


def test_empty_output_cannot_pass_even_with_positive_ratings(example):
    case, ref, prediction, review = example
    prediction["output"] = " \n "
    review["output_digest"] = digest(prediction["output"])
    assert score_policy_response(case, ref, prediction, review)["outcome"] == "fail"


def test_no_review_is_unresolved_and_has_no_headline_pass_rate(example):
    case, ref, prediction, _ = example
    score = score_policy_response(case, ref, prediction)
    summary = summarize_policy_scores([score])
    assert score["outcome"] == "unresolved"
    assert summary["strict_pass_rate"] is None
    assert summary["review_coverage"] == 0


def test_partial_review_does_not_silently_drop_unknown_criteria(example):
    case, ref, prediction, review = example
    review["criteria"]["qualification"] = "unratable"
    score = score_policy_response(case, ref, prediction, review)
    assert score["outcome"] == "unresolved"
    assert score["criterion_rating_coverage"] == 0.5
    assert score["required_content_met_rate"] is None
    assert summarize_policy_scores([score])["strict_pass_rate"] is None


@pytest.mark.parametrize("mutation", ["case_hash", "response_id", "text"])
def test_cannot_reuse_rating_for_changed_output(example, mutation):
    case, ref, prediction, review = example
    if mutation == "case_hash":
        prediction["case_sha256"] = "stale"
    elif mutation == "response_id":
        prediction["response_id"] = "different"
    else:
        prediction["output"] += " Invented promise."
    with pytest.raises(ValueError, match="mismatch|linked"):
        score_policy_response(case, ref, prediction, review)


def test_blank_template_is_not_an_independent_review(example):
    case, ref, prediction, review = example
    review["reviewer_id"] = None
    with pytest.raises(ValueError, match="Reviewer identity"):
        score_policy_response(case, ref, prediction, review)


def test_missing_criterion_key_does_not_count_as_not_applicable(example):
    case, ref, prediction, review = example
    del review["criteria"]["qualification"]
    with pytest.raises(ValueError, match="criterion/check IDs"):
        score_policy_response(case, ref, prediction, review)


def test_multiple_raters_cannot_inflate_response_count(example):
    score = score_policy_response(*example)
    second = deepcopy(score)
    second["reviewer_id"] = "another"
    with pytest.raises(ValueError, match="one reviewer per response"):
        summarize_policy_scores([score, second])


def test_review_cannot_silently_follow_a_changed_rubric(example):
    case, ref, prediction, review = example
    ref["rubric_version"] = "atomic-v2"
    ref["rubric_sha256"] = rubric_digest(ref)
    with pytest.raises(ValueError, match="exact rubric version"):
        score_policy_response(case, ref, prediction, review)
    review["rubric_sha256"] = ref["rubric_sha256"]
    assert score_policy_response(case, ref, prediction, review)["outcome"] == "pass"
    ref["criteria"][0]["description"] = "A changed requirement under the same ID"
    with pytest.raises(ValueError, match="Rubric hash mismatch"):
        score_policy_response(case, ref, prediction, review)
    ref["rubric_sha256"] = rubric_digest(ref)
    with pytest.raises(ValueError, match="exact rubric version"):
        score_policy_response(case, ref, prediction, review)


def test_unsupported_noncommitment_claim_also_fails_v2(example):
    case, ref, prediction, review = example
    ref["universal_checks"]["all_material_claims_supported"] = "Every substantive source claim has support"
    review["checks"]["all_material_claims_supported"] = "unmet"
    score = score_policy_response(case, ref, prediction, review)
    assert score["outcome"] == "fail"
    assert score["unsupported_material_claim"] is True
    assert score["unsupported_commitment"] is False
