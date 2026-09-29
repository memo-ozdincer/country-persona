"""Adversarial mechanical checks; authored fixtures are not quality calibration."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from country_persona.action_eval import validate_case
from country_persona.evidence_ledger import check_ledger
from country_persona.io import digest, read_jsonl, sha256


@pytest.fixture
def example():
    sources = [{"id": c.lower(), "country": c, "text": "We support access. Conditions still apply.",
                "text_digest": digest("We support access. Conditions still apply.")}
               for c in ("FRA", "GBR", "IND", "BRA")]
    rows = [{"country": e["country"], "answer": "Support access with conditions.",
             "evidence": [{"claim": "Support access", "evidence_id": e["id"], "quote": "We support access."}],
             "not_established": []} for e in sources]
    value = {"countries": rows, "common_ground": [{"claim": "All four support access.",
              "countries": [e["country"] for e in sources],
              "evidence": [{"country": e["country"], "evidence_id": e["id"], "quote": "We support access."} for e in sources]}],
             "differences": [], "proposals": [{"text": "Discuss the remaining conditions.", "status": "proposal_not_commitment"}]}
    return sources, value


def test_correct_quote_does_not_certify_opposite_claim_or_complete_answer(example):
    sources, value = example
    value["countries"][0]["answer"] = "France rejects access without any conditions."
    value["countries"][0]["evidence"][0]["claim"] = "France rejects access."
    report = check_ledger(json.dumps(value), sources)
    assert report["mechanical_checks_passed"]
    assert report["valid_source_quotations"] == 8
    assert report["semantic_validity"] is None and report["answer_completeness"] is None


def test_identical_text_in_another_country_does_not_allow_wrong_attribution(example):
    sources, value = example
    value["countries"][0]["evidence"][0]["evidence_id"] = "gbr"
    report = check_ledger(json.dumps(value), sources)
    assert not report["mechanical_checks_passed"]
    assert report["quote_checks"][0]["quote_found"]
    assert not report["quote_checks"][0]["source_country_matches"]


@pytest.mark.parametrize("bad_quote", ["We reject access.", "we support access.", "We support access!", ""])
def test_changed_quote_is_not_silently_repaired(example, bad_quote):
    sources, value = example
    value["countries"][0]["evidence"][0]["quote"] = bad_quote
    assert not check_ledger(json.dumps(value), sources)["mechanical_checks_passed"]


def test_quote_whitespace_only_normalization(example):
    sources, value = example
    value["countries"][0]["evidence"][0]["quote"] = "We\n support   access."
    assert check_ledger(json.dumps(value), sources)["mechanical_checks_passed"]


def test_all_country_claim_requires_each_source_even_if_schema_is_valid(example):
    sources, value = example
    value["common_ground"][0]["evidence"].pop()
    report = check_ledger(json.dumps(value), sources)
    assert report["schema_valid"]
    assert not report["mechanical_checks_passed"]
    assert any(e["kind"] == "coverage" for e in report["errors"])


@pytest.mark.parametrize("mutation", ["missing_country", "duplicate_country", "missing_answer", "wrong_proposal", "extra_key", "bad_country_type"])
def test_incomplete_or_malformed_deliverable_stays_failure(example, mutation):
    sources, value = example
    if mutation == "missing_country":
        value["countries"].pop()
    elif mutation == "duplicate_country":
        value["countries"][-1] = deepcopy(value["countries"][0])
    elif mutation == "missing_answer":
        value["countries"][0]["answer"] = ""
    elif mutation == "wrong_proposal":
        value["proposals"][0]["status"] = "agreed_commitment"
    elif mutation == "extra_key":
        value["countries"][0]["unvalidated_claims"] = "Anything goes"
    else:
        value["common_ground"][0]["countries"][0] = ["FRA"]
    report = check_ledger(json.dumps(value), sources)
    assert not report["schema_valid"] and not report["mechanical_checks_passed"]


@pytest.mark.parametrize("text", ['{"countries": [], "countries": []}', '```json\n{}\n```', '{"countries": NaN}', '{"countries":'])
def test_duplicate_keys_fences_constants_and_incomplete_json_rejected(example, text):
    sources, _ = example
    assert not check_ledger(text, sources)["json_valid"]


def test_capped_valid_json_stays_delivery_failure(example):
    sources, value = example
    report = check_ledger(json.dumps(value), sources, capped=True)
    assert report["json_valid"] and report["schema_valid"]
    assert not report["mechanical_checks_passed"]


def test_changed_source_is_not_scored(example):
    sources, value = example
    sources[0]["text"] = "We reject access."
    with pytest.raises(ValueError, match="evidence inventory"):
        check_ledger(json.dumps(value), sources)


@pytest.fixture(scope="module")
def pack():
    path = Path("data/prepared/evidence-format-20260928-v1")
    if not path.exists():
        pytest.skip("Build the frozen format diagnostic for its integration checks")
    manifest = json.loads((path / "manifest.json").read_text())
    for name, expected in manifest["files_sha256"].items():
        assert sha256(path / name) == expected
    return path, list(read_jsonl(path / "cases.jsonl")), list(read_jsonl(path / "scenarios.jsonl"))


def test_format_comparison_preserves_questions_sources_and_notes(pack):
    _, cases, scenarios = pack
    assert len(cases) == 9
    for scenario in scenarios:
        selected = [c for c in cases if c["scenario_id"] == scenario["id"]]
        assert len(selected) == 3
        assert len({c["parent_case_sha256"] for c in selected}) == 1
        common = selected[0]["prompt"][-1]["content"]
        for c in selected:
            validate_case(c)
            assert c["prompt"][0] == selected[0]["prompt"][0]
            assert c["prompt"][-1]["content"].startswith(common)
            assert "Use at most 700 words" in c["prompt"][-1]["content"]
            assert all(q in c["prompt"][-1]["content"] for q in scenario["questions"].values())
            assert all(e["text"] in c["prompt"][-1]["content"] for e in scenario["evidence"])
            assert not any(k in c for k in ("criteria", "worked_answer", "expected", "reference"))
        for condition in selected[1:]:
            assert "EVIDENCE REQUIREMENTS" in condition["prompt"][-1]["content"]


def test_fresh_references_and_whole_speech_boundaries(pack):
    path, cases, scenarios = pack
    fresh, = [s for s in scenarios if s["id"].startswith("south-sudan")]
    sources = {e["id"]: e for e in fresh["evidence"]}
    refs = list(read_jsonl(path / "review.references.jsonl"))[-1]
    assert len(refs["criteria"]) == 13
    spec = json.loads((path / "source-curation.json").read_text())
    for boundary in spec["speeches"]:
        e = sources[boundary["id"]]
        assert e["text"].startswith(boundary["start_anchor"])
        assert boundary["end_anchor"] not in e["text"]
        assert sorted({l["page"] for l in e["locations"]}) == boundary["pages"]
    for criterion in refs["criteria"]:
        for span in criterion["support_spans"]:
            e = sources[span["evidence_id"]]
            assert e["text"][span["start"]:span["end"]] == span["quote"]
            assert e["text_digest"] == span["text_digest"]
            assert span["locations"]
        if criterion.get("kind") == "bounded_absence":
            bound = criterion["bounded_source_for_absence"]
            assert sources[bound["evidence_id"]]["text_digest"] == bound["text_digest"]
    for c in cases:
        if c["scenario_id"] == fresh["id"]:
            assert c["depends_on_response_ids"] == []
            assert "INITIAL OR REVISED NOTES" not in c["prompt"][-1]["content"]


@pytest.fixture
def audit_fixture(pack, tmp_path):
    """Fake receipt in a temporary directory, solely to test audit rejection paths."""
    from country_persona.io import write_json, write_jsonl
    path, cases, _ = pack
    spec = importlib.util.spec_from_file_location("format_audit", "scripts/audit_evidence_format_probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    run = tmp_path / "fixture-run"
    rows = [{"id": c["id"], "case_sha256": c["case_sha256"], "input_ids": [1, 2], "input_ids_digest": digest([1, 2]),
             "response_id": "authored-fixture-" + c["id"], "output": "not JSON; authored engineering fixture",
             "generated_ids": [3], "prompt_tokens": 2, "generated_tokens": 1,
             "generation_seconds": 0, "stop_reason": "eos"} for c in cases]
    write_jsonl(run / "predictions.jsonl", rows)
    manifest = json.loads((path / "manifest.json").read_text())
    record = {"test_fixture_only": True, "status": "completed", "run_kind": "pinned_model_development_inference",
              "predictions_sha256": sha256(run / "predictions.jsonl"), "adapter": None,
              "generation_config": {"max_new_tokens": 2048}, "completed_cases": len(cases),
              "preflight": {"pack_manifest_sha256": sha256(path / "manifest.json"),
                            "model_lock_sha256": manifest["planned_model_lock_sha256"],
                            "input_token_digests": {c["id"]: digest([1, 2]) for c in cases}}}
    write_json(run / "run.json", record)
    return module.audit, path, run, rows, record


def test_audit_retains_bad_json_and_null_semantics(audit_fixture, tmp_path):
    audit, path, run, _, _ = audit_fixture
    result = audit(path, run, tmp_path / "audit")
    assert result["semantic_quality_scores"] is None
    assert result["by_condition"]["evidence_json"]["mechanical_ledger_passes"] == 0
    assert result["by_condition"]["prose_control"]["mechanical_ledger_passes"] is None
    assert all(r["ratings"] is None for r in read_jsonl(tmp_path / "audit" / "blank-review-checklist.jsonl"))


@pytest.mark.parametrize("mutation", ["changed_prediction", "wrong_case", "altered_inputs", "wrong_pack", "missing_case", "wrong_cap"])
def test_audit_rejects_changed_or_unmatched_results(audit_fixture, tmp_path, mutation):
    from country_persona.io import write_json, write_jsonl
    audit, path, run, rows, record = audit_fixture
    if mutation == "changed_prediction":
        rows[0]["output"] = "silently replaced"
    elif mutation == "wrong_case":
        rows[0]["case_sha256"] = "wrong"
    elif mutation == "altered_inputs":
        rows[0]["input_ids"] = [9, 9]
    elif mutation == "wrong_pack":
        record["preflight"]["pack_manifest_sha256"] = "wrong"
    elif mutation == "missing_case":
        rows.pop()
    else:
        record["generation_config"]["max_new_tokens"] = 512
    write_jsonl(run / "predictions.jsonl", rows)
    if mutation != "changed_prediction":
        record["predictions_sha256"] = sha256(run / "predictions.jsonl")
    write_json(run / "run.json", record)
    with pytest.raises(ValueError):
        audit(path, run, tmp_path / "audit")
    assert not (tmp_path / "audit").exists()
