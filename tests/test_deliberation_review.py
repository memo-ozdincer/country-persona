from copy import deepcopy

import pytest

from country_persona.deliberation import CONDITIONS, COUNTRIES, run_condition
from country_persona.deliberation_review import review_completion, review_item, review_template, score_deliberation
from country_persona.deliberation_comparison import compare_checkpoints
from country_persona.io import digest


@pytest.fixture
def interaction():
    scenario = {"id": "fixture", "split_group": "authored-fixture", "description": "Engineering fixture.",
                "questions": {c: "What is documented?" for c in COUNTRIES}, "final_task": "Compare documented positions.",
                "evidence": [{"id": c, "country": c, "symbol": "FIXTURE/1", "statement_date": "2000-01-01",
                              "text": "Fixture text", "text_digest": digest("Fixture text"),
                              "source_role": "prior_public_statement"} for c in COUNTRIES]}
    scenario["scenario_sha256"] = digest(scenario)
    reference = {"scenario_id": scenario["id"], "scenario_sha256": scenario["scenario_sha256"],
                 "national_policy_rubrics": {c: {"criteria": [{"id": "position", "description": "Preserve documented position."}],
                                                 "universal_checks": {"no_unsupported_commitment": "Do not invent commitments."}} for c in COUNTRIES},
                 "synthesis_checks": {"supported_agreement": "Do not invent agreement."}}
    def generate(case, cap, use_adapter):
        return {"id": case["id"], "case_sha256": case["case_sha256"], "response_id": case["id"] + "-fixture",
                "output": "Authored engineering fixture, not model inference.", "prompt_tokens": 1, "generated_tokens": 1}
    rows = [row for condition in CONDITIONS for row in run_condition(scenario, condition, generate)]
    reviews = []
    for row in rows:
        review = review_template(review_item(row, reference))
        review.update(reviewer_id="fixture-expectations", reviewer_kind="authored_fixture")
        review["ratings"] = {k: "met" for k in review["ratings"]}
        reviews.append(review)
    return rows, [reference], reviews


def test_missing_reviews_leave_all_quality_and_paired_gains_null(interaction):
    rows, refs, _ = interaction
    result = score_deliberation(rows, refs)
    assert result["reviewed_responses"] == 0
    assert all(r["content_met_rate"] is None and r["strict_pass"] is None for r in result["scores"])
    assert result["paired_deliberation_contrasts"][0]["country_macro_peer_gain"] is None


def test_partial_or_assistant_review_never_marks_semantic_review_complete(interaction):
    rows, refs, reviews = interaction
    result = score_deliberation(rows, refs, reviews[:1])
    status = review_completion(result, refs)
    assert status["ratings_supplied"] == 1 and status["fully_rated_responses"] == 1
    assert status["rating_completion_pending"] and status["semantic_review_pending"]
    for review in reviews:
        review["reviewer_kind"] = "assistant"
    status = review_completion(score_deliberation(rows, refs, reviews), refs)
    assert not status["rating_completion_pending"]
    assert status["semantic_review_pending"] and status["independent_construct_review_pending"]


def test_ambiguity_does_not_hide_a_known_failed_unit(interaction):
    rows, refs, reviews = interaction
    keys = list(reviews[0]["ratings"])
    reviews[0]["ratings"][keys[0]] = "unmet"
    reviews[0]["ratings"][keys[1]] = "unratable"
    result = score_deliberation(rows, refs, reviews)["scores"][0]
    assert not result["all_ratings_complete"]
    assert result["known_failure"] and result["strict_pass"] is False


def test_review_rejects_output_or_rubric_changes_and_blank_templates(interaction):
    rows, refs, reviews = interaction
    changed = deepcopy(rows); changed[0]["output"] += " modified"
    with pytest.raises(ValueError, match="exact"):
        score_deliberation(changed, refs, reviews)
    changed = deepcopy(refs); changed[0]["national_policy_rubrics"]["FRA"]["criteria"][0]["description"] += " changed"
    with pytest.raises(ValueError, match="exact"):
        score_deliberation(rows, changed, reviews)
    with pytest.raises(ValueError, match="identity"):
        score_deliberation(rows, refs, [review_template(review_item(rows[0], refs[0]))])
    stale = deepcopy(reviews); stale[0]["guidance_sha256"] = "old-instructions"
    with pytest.raises(ValueError, match="guidance"):
        score_deliberation(rows, refs, stale)


def test_peer_correction_is_compared_with_self_revision(interaction):
    rows, refs, reviews = interaction
    target = next(i for i, r in enumerate(rows) if r["condition"] == "peer_revision" and r["stage"] == "initial" and r["country"] == "FRA")
    content_keys = [k for k in reviews[target]["ratings"] if ".content." in k]
    reviews[target]["ratings"][content_keys[0]] = "unmet"
    result = score_deliberation(rows, refs, reviews)
    transition = next(t for t in result["initial_to_revision"] if t["condition"] == "peer_revision" and t["country"] == "FRA")
    assert transition["content"]["known_corrections"] == 1
    assert result["paired_deliberation_contrasts"][0]["country_macro_peer_gain"] == pytest.approx(1 / len(content_keys) / 4)
    assert result["reviewer_kinds"] == ["authored_fixture"]


def test_unsupported_commitment_regression_is_visible_separately(interaction):
    rows, refs, reviews = interaction
    target = next(i for i, r in enumerate(rows) if r["condition"] == "peer_revision" and r["stage"] == "revision" and r["country"] == "FRA")
    key = next(k for k in reviews[target]["ratings"] if k.endswith("no_unsupported_commitment"))
    reviews[target]["ratings"][key] = "unmet"
    result = score_deliberation(rows, refs, reviews)
    transition = next(t for t in result["initial_to_revision"] if t["condition"] == "peer_revision" and t["country"] == "FRA")
    assert transition["checks"]["known_regressions"] == 1
    assert result["scores"][target]["strict_pass"] is False


@pytest.fixture
def checkpoint_pair(interaction):
    rows, refs, reviews = interaction
    before, after = deepcopy(rows), deepcopy(rows)
    for group, adapted in ((before, False), (after, True)):
        for row in group:
            row.update(adapter_active=adapted and row["stage"] != "synthesis", generation_config={"greedy": True},
                       generation_seconds=1.0, hit_output_cap=False)
    common = {"status": "completed", "snapshot_verification": {"status": "verified_current_bytes", "files": ["fixture-not-actual-weights"]},
              "model": "fixture", "revision": "fixture-revision", "model_lock_sha256": "fixture-lock", "pack_manifest_sha256": "fixture-pack",
              "protocol_sha256": "fixture-protocol", "chat_template_kwargs": {}, "seed": 0, "generation_call_kwargs": {},
              "torch_version": "fixture", "transformers_version": "fixture", "device": "fixture-device",
              "source_code_sha256": {"fixture.py": "fixture-code"}}
    return {**common, "adapter": None}, {**common, "adapter": {"fixture": "not-real-weights"}}, before, after, refs, reviews


def test_checkpoint_comparison_cannot_turn_missing_reviews_into_improvement(checkpoint_pair):
    before_run, after_run, before, after, refs, _ = checkpoint_pair
    result = compare_checkpoints(before_run, after_run, before, after, refs)
    assert result["fully_rated_pairs"] == 0
    assert all(p["content_met_rate_delta"] is None for p in result["response_pairs"])
    assert all(p["training_change_in_peer_gain"] is None for p in result["deliberation_gain_change"])


def test_fidelity_improvement_and_change_in_discussion_gain_are_separate(checkpoint_pair):
    before_run, after_run, before, after, refs, reviews = checkpoint_pair
    earlier = deepcopy(reviews)
    i = next(i for i, r in enumerate(before) if r["country"] == "FRA" and r["condition"] == "peer_revision" and r["stage"] == "initial")
    key = next(k for k in earlier[i]["ratings"] if ".content." in k)
    earlier[i]["ratings"][key] = "unmet"
    result = compare_checkpoints(before_run, after_run, before, after, refs, earlier, reviews)
    pair = next(p for p in result["response_pairs"] if p["before_response_id"] == before[i]["response_id"])
    assert pair["content_met_rate_delta"] == 1
    assert result["deliberation_gain_change"][0]["training_change_in_peer_gain"] == -.25


@pytest.mark.parametrize("change", ["model_lock_sha256", "device", "protocol_sha256"])
def test_incomparable_checkpoint_conditions_are_rejected(checkpoint_pair, change):
    before_run, after_run, before, after, refs, _ = checkpoint_pair
    after_run[change] = "different"
    with pytest.raises(ValueError, match="differs"):
        compare_checkpoints(before_run, after_run, before, after, refs)


def test_changed_aggregator_and_decoding_are_rejected(checkpoint_pair):
    before_run, after_run, before, after, refs, _ = checkpoint_pair
    bad = deepcopy(after); bad[-1]["adapter_active"] = True
    with pytest.raises(ValueError, match="adapter state"):
        compare_checkpoints(before_run, after_run, before, bad, refs)
    bad = deepcopy(after); bad[0]["generation_config"] = {"greedy": False}
    with pytest.raises(ValueError, match="decoding"):
        compare_checkpoints(before_run, after_run, before, bad, refs)
