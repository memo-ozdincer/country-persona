"""Measure how verified partial credit changes the DRC retrieval incentive."""
import json

import experts_judge as criteria
import results
from outcome_diagnostic import run as original
from policy_replay import policy

WITNESSES = {
    "mandate_expiry": "extended Group of Experts mandate to 1 Aug 2024",
    "review_deadline": "reviewing by 1 July 2024",
    "midterm_date": "Midterm report due 30 Dec 2023",
    "final_date": "final report 15 June 2024",
    "committee_cadence": "Monthly Committee updates except report months",
}


def run():
    evaluation = results.load(results.EVIDENCE / "results.json")
    observed = evaluation["field_packets"]
    case = results.load(results.writer.CASE)
    authored = results.verified_bank(case)
    ids = tuple(case["sources"])
    expert = ids.index("EXPERTS")
    reviewed = {field for field, state in zip(criteria.FIELDS, criteria.ACTUAL["EXPERTS"], strict=True)
                if state == "stated"}
    assert reviewed == set(WITNESSES)
    partial = sum(7 * len(reviewed.intersection(group)) / len(group) for group in criteria.GROUPS)
    adjusted = {}
    for held in authored:
        if not 1 <= len(held) <= 3:
            continue
        packet = observed[",".join(sorted(held))]
        if "EXPERTS" in held:
            assert {"experts_term", "experts_reports"}.issubset(packet["missing"])
            assert all(span in packet["record"] for span in WITNESSES.values())
        adjusted[held] = {"record_points": packet["points"] + partial * ("EXPERTS" in held)}

    rows = []
    for target, anchor in policy.relay.SCENARIOS:
        pending = set(target) - {anchor}
        prior = policy.shift.distribution(pending, 6., 1)
        distribution = policy.script(target, anchor, ids, adjusted, prior, True)
        row = policy.benefits(target, anchor, ids, distribution, observed, authored)
        row["requested_source_receipt_count"] = sum(mass * (len(target) - len(missing))
                                                    for missing, (mass, _, _) in distribution.items())
        if expert in pending:
            row["expert_receipt"] = sum(mass for missing, (mass, _, _) in distribution.items()
                                        if expert not in missing)
        rows.append({"target": [ids[i] for i in target], "anchor": ids[anchor], "metrics": row})

    main = policy.transfer.mean([{"atomic": {k: v for k, v in row["metrics"].items() if k != "expert_receipt"}}
                                 for row in rows])["atomic"]
    expert_only = policy.transfer.mean([{"atomic": row["metrics"]} for row in rows
                                       if "expert_receipt" in row["metrics"]])["atomic"]
    old = original()
    assert main["actual_net_gain"] <= old["all_cases"]["observed_only"]["actual_net_gain"] + 1e-9
    return {
        "scope": "Exact scripted objective intervention. Routing receives partial credit from manually verified "
                 "atomic witnesses. Evaluation uses the original score and all original gates. "
                 "The LLM judge is evaluated separately.",
        "partial_points_out_of_14": partial,
        "exact_witnesses": WITNESSES,
        "all_cases": main,
        "where_expert_source_is_requested_and_missing": expert_only,
        "per_scenario": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
