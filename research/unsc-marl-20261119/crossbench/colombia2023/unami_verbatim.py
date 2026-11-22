"""Assemble two distinct UNAMI obligations from reviewed, receipt-gated text."""
import json
from pathlib import Path

import unami_handoff as handoff

HERE = handoff.HERE
SOURCE = HERE / "unami-handoff-evidence"
CASE = handoff.baseline.CASES["unami"]
REVIEW = (
    "The Secretary-General was requested to conduct an independent strategic review of UNAMI, "
    "to be delivered to the Council by 31 March 2024."
)
REVIEW_SOURCE = (
    "The Secretary-General was requested to conduct and provide the Council with an independent "
    "strategic review of UNAMI no later than 31 March 2024."
)
REPORT = "The Secretary-General was requested to report to the Council on fulfilment of UNAMI responsibilities every four months."
SLOTS = {
    "no_question": (
        "The Council also mandated an independent strategic review of UNAMI by 31 March 2024 [Working Note 2].",
        "The Secretary-General is required to report biannually on UNAMI's fulfilment of responsibilities [Working Note 1].",
    ),
    "actor": (
        "The Secretary-General is tasked with conducting an independent strategic review of UNAMI, to be delivered by 31 March 2024 [WORKING NOTE 2].",
        "The Council also requested biannual reports on UNAMI's fulfilment of responsibilities [WORKING NOTE 1].",
    ),
}
REGISTRY = {"peer_review": ("actor_reply", "REVIEW", REVIEW),
            "official_report": ("report_card", "REPORT", REPORT)}
FIXED = {"vote", "tally"}
GUARD = "The original record asserts an incorrect cadence. The unsourced reporting sentence is removed before delivery."


def admits(receipt, packet):
    """Admit a reviewed exact span under a host-supplied receipt and field ID."""
    if packet is None:
        return False
    slot, origin, card, text = packet
    return origin in receipt and REGISTRY.get(slot) == (origin, card, text)


def assembled(base, choice, receipt, review_packet=None, report_packet=None):
    # These are reviewed edit locations in two given archived generations.
    # Fail closed on duplicates or unexpected edits.
    review_text, report_text = SLOTS[choice]
    assert base.count(review_text) == base.count(report_text) == 1
    outside_a, outside_b = "__VERIFIED_REVIEW_SLOT__", "__VERIFIED_REPORT_SLOT__"
    assert outside_a not in base and outside_b not in base
    template = base.replace(review_text, outside_a).replace(report_text, outside_b)
    accepts_review = admits(receipt, review_packet) and review_packet[0] == "peer_review"
    accepts_report = admits(receipt, report_packet) and report_packet[0] == "official_report"
    blocks = (REVIEW + " [REVIEW]" if accepts_review else review_text,
              REPORT + " [REPORT]" if accepts_report else "")
    final = template.replace(outside_a, blocks[0]).replace(outside_b, blocks[1])
    remainder = template.replace(outside_a, "").replace(outside_b, "")
    # Compare byte-for-byte outside the two selected fields.
    carry = final.replace(blocks[0], "", 1)
    if blocks[1]:
        carry = carry.replace(blocks[1], "", 1)
    assert carry == remainder
    return final, accepts_review, accepts_report


def run():
    read = handoff.baseline.read
    raw = SOURCE / "transcript.jsonl"
    assert handoff.runner.digest(raw) == read(SOURCE / "complete.json")["transcript_sha256"]
    chronicle = {r["id"]: r for r in map(json.loads, raw.read_text().splitlines())}
    baseline = read(SOURCE / "results.json")["records"]
    case = read(CASE)
    vote = case["public"]["VOTE"]
    assert REVIEW_SOURCE in case["roles"]["review desk"]["REVIEW"]
    assert REPORT in case["roles"]["mandate desk"]["REPORT"]
    transfer = handoff.archived()
    assert REVIEW in transfer["unami/actor/reply"]["output"]
    assert REVIEW not in transfer["unami/no_question/reply"]["output"]
    review_packet = ("peer_review", *REGISTRY["peer_review"])
    report_packet = ("official_report", *REGISTRY["official_report"])
    results = {}
    for choice in SLOTS:
        id_ = f"unami/{choice}_plain_notes/final"
        base = chronicle[id_]["output"]
        points = baseline[id_]["points"]
        assert base == baseline[id_]["record"].removeprefix(vote + "\n\n")
        assert baseline[id_]["cadence"] == "wrong" and len(baseline[id_]["issues"]) == 1
        assert not {"deliverable", "report"} & baseline[id_]["met"].keys()
        runs = {}
        for ask in (False, True):
            for fetch in (False, True):
                receipt = set()
                if ask:
                    receipt.add("actor_reply")
                if fetch:
                    receipt.add("report_card")
                record, review_kept, report_kept = assembled(base, choice, receipt, review_packet, report_packet)
                assert (review_kept, report_kept) == (ask, fetch)
                existing = baseline[id_]["met"]
                assert all(span in record for spans in existing.values() for span in spans)
                assert "biannual" not in record and "biannually" not in record
                assert (REVIEW in record, REPORT in record) == (ask, fetch)
                covered = sorted(FIXED | set(existing) | ({"deliverable"} if ask else set()) | ({"report"} if fetch else set()))
                runs[f"{'ask' if ask else 'pass'}/{'fetch' if fetch else 'no_fetch'}"] = {
                    "receipt": sorted(receipt), "record": vote + "\n\n" + record, "pinned_review": review_kept,
                    "pinned_reporting": report_kept, "calendar_entries": 2 + int(fetch),
                    "both_obligations_source_complete": review_kept and report_kept,
                    "points": len(covered) * 7, "content_criteria": covered,
                    "delta_over_generated_base": len(covered) * 7 - points, "within_original_supplement_cap": len(record.split()) <= 175,
                    "strict": False, "untouched_remainder": "exact",
                }
        results[choice] = {
            "receipts": runs,
            "joint_interaction_in_points": (
                runs["ask/fetch"]["points"] - runs["ask/no_fetch"]["points"]
                - runs["pass/fetch"]["points"] + runs["pass/no_fetch"]["points"]
            ),
        }
    controls = audit(review_packet, report_packet)
    return {"scope": "Posthoc deterministic assembly of two reviewed fields on one exposed docket. "
                     "Historical reviews for unchanged sentences are inherited. The edit registry does not verify arbitrary prose. "
                     "The same question and reporting receipts are counterfactually crossed with two frozen remainders.",
            "inputs": {p.name: handoff.runner.digest(p) for p in
                       (Path(__file__), raw, CASE, handoff.SOURCE / "transcript.jsonl", SOURCE / "results.json")},
            "review_documentary_witness": REVIEW_SOURCE, "report_documentary_witness": REPORT,
            "archived_peer_sentence": REVIEW, "receipt_controls": controls, "records": results}


def audit(review, report):
    controls = {
        "authentic_peer": ({"actor_reply"}, review, True),
        "authentic_report": ({"report_card"}, report, True),
        "withheld_peer": ({"report_card"}, review, False),
        "withheld_report": ({"actor_reply"}, report, False),
        "wrong_slot": ({"actor_reply"}, ("official_report", *review[1:]), False),
        "wrong_origin": ({"actor_reply", "report_card"}, (review[0], "report_card", *review[2:]), False),
        "wrong_card": ({"actor_reply"}, (*review[:2], "REPORT", review[3]), False),
        "recipient_reversal": ({"actor_reply"}, (*review[:3], REVIEW.replace("to the Council", "to the Secretary-General")), False),
        "deadline_swap": ({"actor_reply"}, (*review[:3], REVIEW.replace("31 March", "31 May")), False),
        "wrong_cadence": ({"report_card"}, (*report[:3], REPORT.replace("every four months", "biannually")), False),
        "paraphrased_but_faithful": ({"actor_reply"}, (*review[:3], REVIEW.replace("to be delivered", "for submission")), False),
    }
    out = {}
    for name, (receipt, row, expected) in controls.items():
        value = admits(receipt, row)
        assert value == expected, name
        out[name] = value
    return out


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
