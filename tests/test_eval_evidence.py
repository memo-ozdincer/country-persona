from copy import deepcopy
import json
from pathlib import Path

import pytest

from country_persona.action_eval import validate_case
from country_persona.eval_evidence import extract_speech, unique_span
from country_persona.io import digest, read_jsonl, sha256


def test_ambiguous_source_anchor_is_rejected():
    with pytest.raises(ValueError, match="one occurrence"):
        unique_span("We support this. We support this.", "We support this.")


def test_outcome_record_cannot_become_prior_evidence():
    text = "Speaker: opening. Next speaker: ending."
    document = {"text": text, "text_digest": digest(text), "sections": []}
    spec = {"start_anchor": "Speaker: opening.", "end_anchor": "Next speaker: ending."}
    with pytest.raises(ValueError, match="cannot become prior speeches"):
        extract_speech(document, spec, {"role": "outcome_reference_only"})


@pytest.fixture(scope="module")
def built_pack():
    root = Path("data/prepared/eval-pilot-20260927/two-event-v1")
    if not root.exists():
        pytest.skip("Run the source collector and two-event builder for the local integration check")
    return (root, list(read_jsonl(root / "cases.jsonl")),
            list(read_jsonl(root / "policy.references.jsonl")),
            {e["id"]: e for e in read_jsonl(root / "evidence.jsonl")})


def test_pair_diff_is_only_dated_evidence_and_never_outcome(built_pack):
    _, cases, _, evidence = built_pack
    pairs = {}
    for c in cases:
        validate_case(c)
        pairs.setdefault(c["pair_id"], {})[c["condition"]] = c
        for eid in c["evidence_ids"]:
            assert evidence[eid]["source_role"] == "prior_public_statement"
        for forbidden in ("expected", "worked_answer", "criteria", "outcome_source_id"):
            assert forbidden not in c
    assert len(pairs) == 15
    for a_b in pairs.values():
        a, b = a_b["A"], a_b["B"]
        assert a["prompt"][0] == b["prompt"][0]
        assert b["prompt"][1]["content"].startswith(a["prompt"][1]["content"] + "\n\nDATED PUBLIC STATEMENT\n")
        assert a["evidence_ids"] == [] and len(b["evidence_ids"]) == 1


def test_each_rubric_span_is_present_in_exact_frozen_evidence(built_pack):
    _, _, refs, evidence = built_pack
    for ref in refs:
        for criterion in ref["criteria"]:
            if criterion["kind"] == "bounded_absence":
                bound = criterion["bounded_source_for_absence"]
                assert evidence[bound["evidence_id"]]["text_digest"] == bound["text_digest"]
            else:
                assert criterion["support_spans"]
            for span in criterion["support_spans"]:
                e = evidence[span["evidence_id"]]
                assert e["text"][span["start"]:span["end"]] == span["quote"]
                assert e["text_digest"] == span["text_digest"]
                assert span["locations"]


def test_country_boundaries_exclude_neighboring_speakers(built_pack):
    _, _, _, e = built_pack
    assert "PREPARE" not in e["climate-fra"]["text"]
    assert "Mr. Zhang Jun" not in e["climate-ind"]["text"]
    assert "Mr. Kimani" not in e["climate-gbr"]["text"]
    assert "Mr. Biang" not in e["climate-bra"]["text"]
    assert "I now resume my functions" not in e["ukraine-fra"]["text"]
    assert "Mr. Agyeman" not in e["ukraine-ind"]["text"]
    assert "Mr. De Almeida Filho" not in e["ukraine-gbr"]["text"]
    assert "Mr. De la Fuente" not in e["ukraine-bra"]["text"]


def test_brazil_climate_has_policy_but_no_fabricated_vote(built_pack):
    root, cases, _, _ = built_pack
    brazil = [c for c in cases if c["country"] == "BRA" and c["family"] == "unsc-climate-security-2021"]
    assert len(brazil) == 2 and all(c["task"] == "policy_fidelity" for c in brazil)
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["action_label_support_per_arm"] == {"Y": 4, "N": 1, "A": 2}
    for name, expected in manifest["files_sha256"].items():
        assert sha256(root / name) == expected
