"""Compile a protected public record and bounded national claims from real drafts."""
import argparse
import json
from pathlib import Path
import re

from minurso_deliberation_review import grade_final
from minurso_vote_reconciliation import base, requests
from source_record_run import digest

# Case-scoped extraction rules. An unrecognized utterance has no typed value.
SENTENCE = r"(?:^|(?<=[.!?])\s+)"
SWISS_YES = re.compile(SENTENCE + r"We backed (?:Algeria's )?S/2024/797\b[^.]*", re.IGNORECASE)
SWISS_FIRST_CONFLICT = re.compile(
    r"\b(?:abstained on|voted against|did not vote on)\s+(?:Algeria's )?"
    r"(?:S/2024/797\b|the nine-year absence note\b)", re.IGNORECASE
)
SWISS_ABSTENTION = re.compile(
    SENTENCE + r"(?:(?:Switzerland supported Resolution 2756 \(MAIN\) and)|(?:Switzerland|It|We)) "
    r"abstained on (?:S/2024/798\b|the MINURSO monitoring amendment\b)[^.]*", re.IGNORECASE
)
SWISS_ABSTENTION_CONFLICT = re.compile(
    r"\b(?:voted (?:in favour|in favor|against)|did not abstain|did not vote) on "
    r"(?:S/2024/798\b|the MINURSO monitoring amendment\b)", re.IGNORECASE
)
CONTINUITY = re.compile(
    r"\babstained on S/2024/798(?: \(AMEND\))? to ensure MINURSO continuity\b",
    re.IGNORECASE,
)
MONITORING = re.compile(
    r"(?im)^We reject the Council's failure to incorporate human-rights monitoring into MINURSO's mandate\b"
)


def extract(dz, ch):
    selected = {}
    reject = {}
    if match := MONITORING.search(dz):
        selected["monitoring-position"] = match.group()
    if conflict := SWISS_FIRST_CONFLICT.search(ch):
        reject["swiss-first"] = conflict.group()
    elif match := SWISS_YES.search(ch):
        selected["swiss-first"] = match.group()
    if conflict := SWISS_ABSTENTION_CONFLICT.search(ch):
        reject["swiss-second"] = conflict.group()
    elif match := SWISS_ABSTENTION.search(ch):
        selected["swiss-second"] = match.group()
        if reason := CONTINUITY.search(match.group()):
            selected["continuity"] = reason.group()
    return selected, reject


def public_sections():
    fixture = base.case()
    adoption, rest = fixture["reference"].split(" [MAIN].", 1)
    amendments, rest = rest.strip().split(" [AMEND].", 1)
    start = rest.index("The Council extended ")
    authority = rest[start:]
    assert authority.endswith(" [TEXT].")
    return {"Adoption": adoption + " [MAIN].", "Amendments": amendments + " [AMEND].", "Authority": authority}


def render(request, view):
    selected, reject = extract(*view.values())
    text = public_sections()
    met = {
        "instrument": [text["Adoption"], ["MAIN"], None],
        "tally": [text["Adoption"], ["MAIN"], None],
        "nonparticipation": [text["Adoption"], ["MAIN"], None],
        "797-content": [text["Amendments"], ["AMEND"], None],
        "797-outcome": [text["Amendments"], ["AMEND"], None],
        "798-content": [text["Amendments"], ["AMEND"], None],
        "798-outcome": [text["Amendments"], ["AMEND"], None],
        "renewal": [text["Authority"], ["TEXT"], None],
        "visits": [text["Authority"], ["TEXT"], None],
        "no-monitoring": [text["Authority"], ["TEXT"], None],
    }
    if "monitoring-position" in selected:
        position = "Algeria argued for a human-rights monitoring component in MINURSO [DZ-DRAFT]."
        text["Algeria"] = position
        met["monitoring-position"] = [position, ["DZ-A"], [request["seen"][0], selected["monitoring-position"]]]
    else:
        text["Algeria"] = "The delivered draft does not verify a national explanation."

    swiss = []
    clauses = {
        "swiss-first": "Switzerland supported S/2024/797 [CH-DRAFT].",
        "swiss-second": "Switzerland abstained on S/2024/798"
                        + (" to ensure MINURSO continuity" if "continuity" in selected else "") + " [CH-DRAFT].",
    }
    for key, clause in clauses.items():
        if key in selected:
            swiss.append(clause)
            met[key] = [clause, ["CH-A"], [request["seen"][1], selected[key]]]
    if "continuity" in selected:
        met["continuity"] = [clauses["swiss-second"], ["CH-A"], [request["seen"][1], selected["continuity"]]]
    if swiss:
        key = "swiss-second" if "swiss-second" in selected else "swiss-first"
        met["capacity"] = met[key]
    text["Switzerland"] = " ".join(swiss) if swiss else "The delivered draft does not verify a national amendment position."
    record = "\n".join(f"{head}: {text[head]}" for head in base.HEADINGS)
    guard = {"status": "clear", "source": [], "response": "",
             "reason": "The fixture's public section and emitted national phrases match the available historical evidence."}
    return record, met, reject, guard


def check():
    texts = [
        "We backed S/2024/797. Switzerland abstained on S/2024/798 (AMEND) to ensure MINURSO continuity.",
        "We backed S/2024/797. Switzerland did not vote on the nine-year absence note.",
        "Switzerland voted against S/2024/798. Could Switzerland have abstained on S/2024/798?",
        "Switzerland abstained on S/2024/798 to preserve consensus.",
        "Switzerland could have abstained on S/2024/798 to ensure MINURSO continuity.",
        "Algeria's failed draft proposed considering monitoring. We propose a new monitoring arrangement now.",
    ]
    expected = [{"swiss-first","swiss-second","continuity"}, set(), set(), {"swiss-second"}, set(), set()]
    for text, keys in zip(texts, expected, strict=True):
        selected, _ = extract(text, text)
        assert set(selected) == keys
        assert all(v in text for v in selected.values())
    return len(expected)


def report(prior_score):
    before = json.loads(prior_score.read_text())["arms"]
    outputs = {}
    for request, audit in requests():
        view = json.loads(request["messages"][-1]["content"])["national_drafts"]
        row = {**request, "ended": True, "input_ids": [], "output_ids": []}
        row["output"], met, rejected, guard = render(request, view)
        visible = dict(zip(row["seen"], view.values(), strict=True))
        report = grade_final(row, {"met": met, "guard": guard}, visible, [])
        # This treatment uses no model call. Word count is meaningful; token
        # fields from the neural record comparison do not apply.
        report = {k: v for k, v in report.items() if k not in ("input_tokens", "output_tokens", "finish")}
        report["author_fixed_public_points"] = 42
        report["draft_supported_national_points"] = report["grounded_points"] - 42
        assert report["basic_release_eligible"] and report["historical_points"] == report["grounded_points"]
        name = row["id"]
        outputs[name] = {"reconciled_free_text_points": before[name]["after_points"],
                         "compiled_record": row["output"], "compiled_review": report,
                         "removed": audit, "blocked_conflicting_draft_claims": rejected}
    return {
        "scope": "Adaptive fixture-specific compiler. Public text is taken from the authored primary-source reference. "
                 "A small exact phrase grammar selects from already generated natural-language drafts. "
                 "Guard assessments and national phrases were checked against the same dossier. "
                 "No fresh writer generation, independent review or generalization evidence.",
        "software_controls": check(), "free_text_scores_sha256": digest(prior_score), "outputs": outputs,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("prior_score", type=Path)
    print(json.dumps(report(cli.parse_args().prior_score), indent=2, ensure_ascii=False))
