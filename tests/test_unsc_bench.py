from country_persona.unsc_bench import country_name, normalize_record


def source():
    return {"date": "2020-01-01", "draft_resolution": "S/2020/1", "meeting_record": "1",
            "votes_by_member": [{"country": "France", "vote": "N"}],
            "total_yes": 0, "total_no": 1, "total_abstentions": 0,
            "draft_url": "draft", "record_url": "record", "draft_pdf": {"text_en": "Draft"}}


def test_aliases_do_not_merge_historical_states():
    assert country_name("United Kingdom of Great Britain and Northern Ireland") == "UNITED KINGDOM"
    assert country_name("USSR") != country_name("Russian Federation")
    assert country_name("German Democratic Republic") != country_name("Germany")


def test_source_vote_and_provenance_preserved():
    r = normalize_record(source(), "vetoed", 4)
    assert r["votes"] == [{"country": "FRANCE", "original_country": "France", "vote": "N"}]
    assert r["row_index"] == 4
    assert r["issues"] == []


def test_missing_draft_not_replaced_by_final_resolution():
    row = source()
    row["draft_pdf"]["text_en"] = ""
    row["resolution_text"] = {"text_en": "Post-decision text"}
    assert "missing_english_draft" in normalize_record(row, "vetoed", 0)["issues"]


def test_vote_and_date_problems_are_flagged():
    row = source()
    row["date"] = "unknown"
    row["total_yes"] = 1
    row["votes_by_member"] *= 2
    issues = normalize_record(row, "vetoed", 0)["issues"]
    assert set(issues) == {"unparsed_vote_date", "duplicate_country_votes", "vote_totals_mismatch"}


def test_final_vote_cannot_be_silently_joined_to_vetoed_amendment():
    row = source()
    row["votes_by_member"][0]["vote"] = "A"
    row.update(total_no=0, total_abstentions=1)
    row["draft_pdf"]["text_en"] = "France: amendment to the draft resolution contained in S/2025/112"
    issues = normalize_record(row, "vetoed", 0)["issues"]
    assert "vetoed_record_without_negative_vote" in issues
    assert "amendment_requires_parent_draft_and_stage_review" in issues
