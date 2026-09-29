"""Read-only inspection of the two UNSC-Bench schemas; no label inference."""
from collections import Counter
from datetime import date
import re

TARGETS = {"FRANCE": "FRA", "UNITED KINGDOM": "GBR", "INDIA": "IND", "BRAZIL": "BRA"}
ALIASES = {"UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND": "UNITED KINGDOM",
           "UNITED STATES OF AMERICA": "UNITED STATES"}


def country_name(value):
    name = " ".join(value.upper().split())
    return ALIASES.get(name, name)


def normalize_record(row, config, index):
    detail = None
    if config == "adopted":
        day = row["dates"]["vote_date"]
        symbol = row["draft_from_file1"]["draft_symbol"]
        meeting = row["meeting"]["meeting_record"]
        votes = [{"country": country_name(v["name"]), "original_country": v["name"], "vote": v["vote"]}
                 for v in row["member_state_votes"]]
        totals = {"Y": row["voting_totals"]["vote_yes"], "N": row["voting_totals"]["vote_no"],
                  "A": row["voting_totals"]["vote_abstention"]}
        draft_url = row["urls_draft"]["en"]
        record_url = row["urls_meeting"]["en"]
        detail = row["voting_totals"].get("vote_detail")
    elif config == "vetoed":
        day, symbol = row["date"], row["draft_resolution"]
        meeting = row["meeting_record"]
        votes = [{"country": country_name(v["country"]), "original_country": v["country"], "vote": v["vote"]}
                 for v in row["votes_by_member"]]
        totals = {"Y": row["total_yes"], "N": row["total_no"], "A": row["total_abstentions"]}
        draft_url, record_url = row["draft_url"], row["record_url"]
    else:
        raise ValueError("Unknown source config")
    issues = []
    try:
        date.fromisoformat(day)
    except (ValueError, TypeError):
        issues.append("unparsed_vote_date")
    draft = (row.get("draft_pdf") or {}).get("text_en")
    if not isinstance(draft, str) or not draft.strip():
        issues.append("missing_english_draft")
    if not symbol:
        issues.append("missing_draft_symbol")
    if config == "vetoed" and not any(v["vote"] == "N" for v in votes):
        issues.append("vetoed_record_without_negative_vote")
    if draft and re.search(r"amendments?\s+to\s+the\s+draft\s+resolution", draft[:1800], re.I):
        issues.append("amendment_requires_parent_draft_and_stage_review")
    if len({v["country"] for v in votes}) != len(votes):
        issues.append("duplicate_country_votes")
    if any(v["vote"] not in ("Y", "N", "A") for v in votes):
        issues.append("nonstandard_vote_label")
    if dict(Counter(v["vote"] for v in votes)) != {k: v for k, v in totals.items() if v}:
        issues.append("vote_totals_mismatch")
    if detail:
        detail_votes = {}
        for line in detail.splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2 and parts[0] in ("Y", "N", "A"):
                detail_votes[country_name(parts[1])] = parts[0]
        if detail_votes != {v["country"]: v["vote"] for v in votes}:
            issues.append("vote_detail_mismatch")
    return {"config": config, "row_index": index, "date": day, "draft_symbol": symbol,
            "meeting": meeting, "draft_text": draft, "draft_url": draft_url, "record_url": record_url,
            "votes": votes, "issues": issues}
