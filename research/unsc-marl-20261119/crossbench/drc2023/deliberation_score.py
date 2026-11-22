"""Audit exact factual witnesses and paired peer uptake on the DRC revision."""
import json

import deliberation
from experts_judge import GROUPS
from experts_reward import WITNESSES as INITIAL

HERE = deliberation.HERE
EVIDENCE = HERE / "deliberation-evidence"
SOURCE_WITNESSES = {
    "mandate_expiry": "The Council extended the Group of Experts mandate to 1 August 2024",
    "review_deadline": "intended to review it and act on a possible further extension by 1 July 2024",
    "future_action": "act on a possible further extension",
    "midterm_date": "a midterm report to the Council after discussion with the Committee by 30 December 2023",
    "final_date": "a final report by 15 June 2024",
    "report_recipient": "It requested a midterm report to the Council after discussion with the Committee by 30 December 2023 and a final report by 15 June 2024",
    "committee_cadence": "send monthly updates to the Committee except in the two report-due months",
}
ARMS = {
    "solo": ("solo_opening", "solo_second_review"),
    "independent": ("peer_opening", "peer_independent_report"),
    "interactive": ("peer_opening", "peer_interactive_report"),
    "direct": (),
}


def run():
    rows = deliberation.replay(EVIDENCE)
    labels = json.loads((HERE / "deliberation-annotations.json").read_text())
    assert labels["transcript_sha256"] == deliberation.runner.digest(EVIDENCE / "transcript.jsonl")
    annotations = labels["records"]
    assert annotations.keys() == rows.keys()
    official = json.loads(deliberation.writer.CASE.read_text())["sources"]["EXPERTS"]["card"]
    assert all(span in official for span in SOURCE_WITNESSES.values())
    facts = {}
    consultation = labels["extra_committee_discussion"]
    assert consultation.keys() <= ARMS.keys()
    assert all(span in rows[key]["output"] for key, span in consultation.items())
    for name, row in rows.items():
        annotation = annotations[name]
        assert annotation["met"].keys() <= SOURCE_WITNESSES.keys()
        assert all(spans and all(span in row["output"] for span in spans) for spans in annotation["met"].values())
        assert all(span in row["output"] for span in annotation["unsupported"])
        facts[name] = set(annotation["met"])

    arms = {}
    for key, notes in ARMS.items():
        final = rows[key]
        ids = [*notes, key]
        assert final["seen"] == list(notes)
        kept = facts[key]
        introduced = set().union(*(facts[note] for note in notes)) - INITIAL.keys()
        arms[key] = {
            "final_facts": sorted(kept), "atomic_count": len(kept),
            "compound_points_out_of_14": 7 * sum(set(group) <= kept for group in GROUPS),
            "partial_points_out_of_14": sum(7 * len(kept.intersection(group)) / len(group) for group in GROUPS),
            "new_facts_relative_to_initial_draft": sorted(kept - INITIAL.keys()),
            "new_facts_first_seen_in_notes_and_retained": sorted(introduced & kept),
            "unique_new_facts_across_notes": len(introduced),
            "committee_discussion_witness": consultation.get(key),
            "final_words": len(final["output"].split()),
            "unsupported": annotations[key]["unsupported"],
            "all_output_calls_finished": all(rows[r]["ended"] for r in ids),
            "total_input_tokens": sum(len(rows[r]["input_ids"]) for r in ids),
            "total_output_tokens": sum(len(rows[r]["output_ids"]) for r in ids),
            "configured_output_token_cap": sum(rows[r]["cap"] for r in ids),
            "calls": len(ids),
            "working_note_counts": {note: {"source_supported": len(facts[note]),
                                            "new_vs_initial": sorted(facts[note] - INITIAL.keys())}
                                    for note in notes},
            "peer_to_peer_receipts": int(key == "interactive"),
        }

    assert rows["peer_interactive_report"]["seen"] == ["peer_opening"]
    assert not rows["peer_independent_report"]["seen"]
    candidate = facts["peer_opening"] & facts["peer_interactive_report"]
    incoming_only = candidate - facts["peer_independent_report"] - INITIAL.keys()
    retained = incoming_only & facts["interactive"] - facts["independent"] - facts["solo"]
    return {
        "scope": "One exposed source docket and exact-span same-assistant annotations. "
                 "The reviewed facts were available to every participant in the same dossier. "
                 "The independent and interactive reporting instructions differ in whether to respond explicitly.",
        "source_witnesses": SOURCE_WITNESSES,
        "arms": arms,
        "peer_interaction": {
            "opening_facts_repeated_by_interactive_reporter": sorted(candidate),
            "new_draft_facts_shared_by_peers_and_absent_from_independent_reporter": sorted(incoming_only),
            "retained_only_by_interactive_final_vs_solo_and_independent": sorted(retained),
            "retained_only_by_interactive_final_including_direct_control": sorted(retained - facts["direct"]),
        },
        "annotations": annotations,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
