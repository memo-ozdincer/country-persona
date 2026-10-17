import copy
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from review_scenario_sft import validate_review


def fixture():
    rubric = {"cases": {"one": [{"id": "a"}]}, "guards": {"source": "Entire answer faithful"}}
    responses = [{"id": "one", "output_raw": "A real quote.", "at_cap": False}]
    review = dict(responses_sha256="abc", reviewer="assistant", rationale="Read source and complete output.",
        decision="replan", cases=[dict(id="one", complete_raw_answer_read=True, notes="Scope inspected.",
            units=[dict(id="a", status="met", answer_quote="real quote", reason="Preserves source.")],
            guards={"source": dict(status="pass", reason="No added assertion.")})])
    return review, responses, rubric


def test_uncertainty_cannot_be_a_strict_pass():
    review, responses, rubric = fixture()
    assert validate_review(review, responses, rubric, "abc")[0]["strict_pass"]
    review["cases"][0]["units"][0]["status"] = "uncertain"
    assert not validate_review(review, responses, rubric, "abc")[0]["strict_pass"]


@pytest.mark.parametrize("corruption", ["quote", "hash", "omitted_case", "blank", "guard", "unread"])
def test_stale_incomplete_or_fabricated_review_rejected(corruption):
    review, responses, rubric = fixture()
    case = review["cases"][0]
    if corruption == "quote": case["units"][0]["answer_quote"] = "invented quote"
    elif corruption == "hash": review["responses_sha256"] = "wrong"
    elif corruption == "omitted_case": review["cases"] = []
    elif corruption == "blank": review["reviewer"] = ""
    elif corruption == "guard": case["guards"] = {}
    else: case["complete_raw_answer_read"] = False
    with pytest.raises(ValueError):
        validate_review(review, responses, rubric, "abc")
