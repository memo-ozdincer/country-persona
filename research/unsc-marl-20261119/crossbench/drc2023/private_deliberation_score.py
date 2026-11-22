"""Review final facts, visible support and idea flow in the private-source pilot."""
import json

import private_deliberation as experiment

HERE = experiment.HERE
EVIDENCE = HERE / "private-deliberation-evidence"
RUBRIC = {
    "drc": {
        "mandate_expiry": ("A", "Group of Experts mandate to 1 August 2024"),
        "review_deadline": ("A", "review it and act on a possible further extension by 1 July 2024"),
        "future_action": ("A", "act on a possible further extension"),
        "midterm_date": ("B", "Committee by 30 December 2023"),
        "final_date": ("B", "final report by 15 June 2024"),
        "report_recipient": ("B", "a midterm report to the Council"),
        "committee_consultation": ("B", "after discussion with the Committee"),
        "committee_cadence": ("B", "monthly updates to the Committee except in the two report-due months"),
    },
    "unami": {
        "mandate_expiry": ("A", "extended the existing UN Assistance Mission for Iraq (UNAMI) mandate until 31 May 2024"),
        "periodic_report": ("A", "Secretary-General was requested to report to the Council on fulfilment of UNAMI responsibilities every four months"),
        "review_kind": ("B", "an independent strategic review of UNAMI"),
        "review_actor": ("B", "Secretary-General was requested to conduct"),
        "review_recipient": ("B", "provide the Council with an independent strategic review"),
        "review_deadline": ("B", "no later than 31 March 2024"),
        "consultation": ("B", "consult Iraq, UN agencies, Member States, regional organizations, independent experts, civil society and Kuwait"),
        "iraqi_support": ("B", "Iraq's Government had expressed support for the independent review in a letter dated 18 May 2023"),
    },
}
ARMS = {
    "pooled_solo": ("solo_a", "solo_b"),
    "independent": ("desk_a", "desk_b_independent"),
    "interactive": ("desk_a", "desk_b_interactive"),
    "local_solo": ("local_a", "local_b"),
}


def run():
    rows = experiment.replay(EVIDENCE)
    review = experiment.read(HERE / "private-deliberation-review.json")
    assert review["transcript_sha256"] == experiment.runner.digest(EVIDENCE / "transcript.jsonl")
    annotations = review["records"]
    assert annotations.keys() == rows.keys()
    report = {}
    for family, _, decks in experiment.fixtures():
        rubric = RUBRIC[family]
        assert all(any(witness in clause for clause in decks[desk].values()) for desk, witness in rubric.values())
        facts = {}
        for key, row in rows.items():
            if not key.startswith(family + "/"):
                continue
            label = annotations[key]
            tokens = label["facts"]
            assert tokens.keys() <= rubric.keys()
            assert all(spans and all(span in row["output"] for span in spans) for spans in tokens.values())
            assert all(span in row["output"] for span in label["conflicts"])
            facts[key.split("/")[1]] = set(tokens)

        results = {}
        for arm, notes in ARMS.items():
            keys = [f"{family}/{name}" for name in (*notes, arm)]
            views = [rows[key] for key in keys]
            final = views[-1]
            assert final["seen"] == keys[:-1]
            assert bool(final["evidence_ids"]) == (arm == "pooled_solo")
            supported_by_messages = facts[notes[0]] | facts[notes[1]]
            local = set(rubric) if arm == "pooled_solo" else set()
            supported = facts[arm] & (supported_by_messages | local)
            conflicts = annotations[keys[-1]]["conflicts"]
            eligible = [{fact for fact, (owner, _) in rubric.items() if decks[owner].keys() <= set(row["evidence_ids"])}
                        for row in views[:-1]]
            first = facts[notes[0]] & eligible[0]
            receipt = first if views[0]["id"] in views[1]["seen"] else set()
            second = facts[notes[1]] & (eligible[1] | receipt)
            verified_delivery = first | second
            admissible = supported & (verified_delivery | local)
            words = len(final["output"].split())
            results[arm] = {
                "final_historical_facts": sorted(facts[arm]),
                "historical_facts_with_visible_support": sorted(admissible),
                "historically_correct_but_unwitnessed": sorted(facts[arm] - admissible),
                "eligible_facts_out_of_8": len(admissible),
                "conflicts": conflicts, "final_words": words,
                "complete": final["ended"],
                "contract_pass": len(admissible) == len(rubric) and not conflicts and final["ended"] and words <= 73,
                "distinct_facts_in_verified_working_notes": len(verified_delivery),
                "fact_overlap_across_notes": sorted(first & second),
                "unique_facts_per_note": {notes[0]: sorted(first - second), notes[1]: sorted(second - first)},
                "call_counts": {"working": 2, "final": 1, "desk_to_desk": int(arm == "interactive")},
                "input_tokens": sum(len(row["input_ids"]) for row in views),
                "output_tokens": sum(len(row["output_ids"]) for row in views),
                "output_cap": sum(row["cap"] for row in views),
            }

        independent = set(results["independent"]["historical_facts_with_visible_support"])
        interactive = set(results["interactive"]["historical_facts_with_visible_support"])
        report[family] = {
            "arms": results,
            "peer_specific_final_delta": {
                "gained_vs_independent": sorted(interactive - independent),
                "lost_vs_independent": sorted(independent - interactive),
            },
        }
    return {"scope": "Same-assistant exact-span review from two exposed dockets. Desk holdings are simulated. "
                     "Historical correctness and support in the chair's actual view are scored separately.",
            "full_rubric": RUBRIC, "cases": report, "annotations": annotations}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
