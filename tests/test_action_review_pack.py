import importlib.util
from pathlib import Path
import pytest
from country_persona.action_eval import validate_case

pytest.importorskip("pyarrow")
spec = importlib.util.spec_from_file_location("action_pack", Path(__file__).resolve().parents[1] / "scripts/build_action_review_pack.py")
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


def record():
    return {"config": "vetoed", "row_index": 1, "date": "2021-12-13", "draft_symbol": "S/2021/990",
            "meeting": "S/PV.8926", "draft_text": "Synthetic draft fixture. " * 8, "draft_url": "draft", "record_url": "record",
            "votes": [{"country": "FRANCE", "original_country": "France", "vote": "N"}], "issues": [],
            "meeting_text": "AFTER_VOTE_SENTINEL", "reason": "AFTER_REASON_SENTINEL"}


def test_prompt_fields_do_not_copy_labels_or_post_vote_metadata():
    r = record()
    case, ref, review = pack.make_case(r, r["votes"][0])
    text = str(case)
    for forbidden in ["AFTER_VOTE_SENTINEL", "AFTER_REASON_SENTINEL", "vetoed", "expected"]:
        assert forbidden not in text
    assert ref["expected"] == "N"
    assert review["primary_vote_verified"] is None
    validate_case(case)


def test_same_meeting_keeps_countries_and_amendments_together():
    r = record()
    first = pack.event_key(r)
    r["draft_symbol"] = "S/2021/990/Rev.1"
    r["meeting"] = "8926"
    assert pack.event_key(r) == first


def test_selection_excludes_conflicts_and_reports_missing_classes():
    good, bad = record(), record()
    bad.update(row_index=2, date="2025-01-01", issues=["vote_totals_mismatch"])
    selected, missing = pack.select_events([bad, good])
    assert selected == [good]
    assert {"country": "FRA", "label": "Y"} in missing
    assert {"country": "FRA", "label": "N"} not in missing


def test_existing_snapshot_cannot_be_overwritten(tmp_path):
    with pytest.raises(FileExistsError):
        pack.build(tmp_path / "nonexistent-source", tmp_path)
