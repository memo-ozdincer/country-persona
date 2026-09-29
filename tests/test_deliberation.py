from copy import deepcopy

import pytest

from country_persona.deliberation import COUNTRIES, CONDITIONS, PROTOCOL, make_case, run_condition, transition_metrics, validate_scenario
from country_persona.io import digest
from country_persona.deliberation_audit import validate_transcript


@pytest.fixture
def scenario():
    row = {"id": "fixture", "split_group": "one-fixture-not-a-real-event", "description": "Authored engineering fixture.",
           "questions": {c: f"What does {c}'s source establish?" for c in COUNTRIES},
           "evidence": [{"id": c, "country": c, "symbol": "TEST/1", "statement_date": "2000-01-01",
                         "text": f"Source for {c}", "text_digest": digest(f"Source for {c}"),
                         "source_role": "prior_public_statement"} for c in COUNTRIES], "final_task": "Compare these sources."}
    row["scenario_sha256"] = digest(row)
    return row


def fixture_generator(case, cap, use_adapter):
    return {"id": case["id"], "case_sha256": case["case_sha256"], "response_id": case["id"] + "-response",
            "output": f"Fixture output {case['country']} {case['stage']}", "prompt_tokens": 100, "generated_tokens": 12,
            "generator_kind": "authored_engineering_fixture_not_model_inference", "used_adapter": use_adapter}


def test_controls_have_identical_initial_prompts_and_source_access(scenario):
    a = run_condition(scenario, "independent_revision", fixture_generator)
    b = run_condition(scenario, "peer_revision", fixture_generator)
    assert len(a) == len(b) == 9
    for left, right in zip(a[:4], b[:4]):
        assert left["case"]["prompt"] == right["case"]["prompt"]
        for country in COUNTRIES:
            assert f"Source for {country}" in left["case"]["prompt"][1]["content"]


def test_peer_revisions_see_all_initial_notes_and_no_revised_peer(scenario):
    rows = run_condition(scenario, "peer_revision", fixture_generator)
    first_ids = {r["response_id"] for r in rows[:4]}
    for row in rows[4:8]:
        assert set(row["depends_on_response_ids"]) == first_ids
        for earlier_revision in rows[4:8]:
            assert earlier_revision["response_id"] not in row["case"]["prompt"][1]["content"]
    assert set(rows[-1]["depends_on_response_ids"]) == {r["response_id"] for r in rows[4:8]}


def test_independent_revision_never_receives_other_countries_notes(scenario):
    rows = run_condition(scenario, "independent_revision", fixture_generator)
    for i, row in enumerate(rows[4:8]):
        assert row["depends_on_response_ids"] == [rows[i]["response_id"]]
        assert sum(r["response_id"] in row["case"]["prompt"][1]["content"] for r in rows[:4]) == 1


def test_equal_output_caps_and_fixed_base_aggregator(scenario):
    for condition in CONDITIONS:
        rows = run_condition(scenario, condition, fixture_generator)
        assert sum(r["maximum_output_tokens"] for r in rows) == PROTOCOL["per_condition_output_token_cap"]
        assert rows[-1]["adapter_permitted"] is False and rows[-1]["used_adapter"] is False
        assert all(r["used_adapter"] for r in rows[:-1])
        assert all(q in rows[-1]["case"]["prompt"][1]["content"] for q in scenario["questions"].values())


def test_tampered_source_and_outcome_evidence_are_rejected(scenario):
    bad = deepcopy(scenario); bad["evidence"][0]["text"] = "Altered"
    with pytest.raises(ValueError, match="hash"):
        validate_scenario(bad)
    bad["scenario_sha256"] = digest({k: v for k, v in bad.items() if k != "scenario_sha256"})
    with pytest.raises(ValueError, match="evidence"):
        validate_scenario(bad)


def test_wrong_output_join_and_caps_fail(scenario):
    def incorrect(case, cap, use_adapter):
        return {**fixture_generator(case, cap, use_adapter), "case_sha256": "wrong"}
    with pytest.raises(ValueError, match="mismatched"):
        run_condition(scenario, "peer_revision", incorrect)
    def oversized(case, cap, use_adapter):
        return {**fixture_generator(case, cap, use_adapter), "generated_tokens": cap + 1}
    with pytest.raises(ValueError, match="budget"):
        run_condition(scenario, "peer_revision", oversized)


def test_unchanged_wrong_policy_does_not_count_as_retention():
    result = transition_metrics({"a": "unmet"}, {"a": "unmet"})
    assert result["retention_rate"] is None
    assert result["known_corrections"] == result["known_regressions"] == 0


def test_corrections_regressions_and_missing_ratings_are_distinct():
    result = transition_metrics({"a": "met", "b": "unmet"}, {"a": "unmet", "b": "met"})
    assert result["known_corrections"] == result["known_regressions"] == 1
    assert result["retention_rate"] == 0 and result["content_change"] == 0
    unknown = transition_metrics({"a": "met", "b": "unratable"}, {"a": "met", "b": "met"})
    assert unknown["coverage"] == .5 and unknown["content_change"] is None and unknown["retention_rate"] is None


def test_transcript_replay_detects_history_tampering_and_missing_calls(scenario):
    rows = [r for condition in CONDITIONS for r in run_condition(scenario, condition, fixture_generator)]
    assert validate_transcript([scenario], rows)["responses"] == 21
    tampered = deepcopy(rows); tampered[0]["output"] += " unrecorded change"
    with pytest.raises(ValueError, match="history"):
        validate_transcript([scenario], tampered)
    with pytest.raises(ValueError, match="ends"):
        validate_transcript([scenario], rows[:-1])
    tampered = deepcopy(rows); tampered[-1]["adapter_active"] = True
    with pytest.raises(ValueError, match="aggregator"):
        validate_transcript([scenario], tampered)
