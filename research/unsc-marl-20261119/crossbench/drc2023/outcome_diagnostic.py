"""Test whether optimizing observed prose gives up on requested source coverage."""
import json

import results
from policy_replay import policy

relay = policy.relay
shift = policy.shift
HERE = results.HERE


def run():
    primary = results.load(results.EVIDENCE / "results.json")
    case = results.load(results.writer.CASE)
    bank = results.verified_bank(case)
    observed = primary["field_packets"]
    ids = tuple(case["sources"])
    expert = ids.index("EXPERTS")
    endpoints = {"authored_coverage": bank}
    # Seven is one rubric criterion. This additional term deliberately gives
    # credit for delivery of requested evidence even when wording is incomplete.
    for label, per_card in (("observed_only", 0), ("observed_plus_delivered_sources", 7)):
        endpoints[label] = {held: {"record_points": observed[",".join(sorted(held))]["points"] + per_card * len(held)}
                            for held in bank if 1 <= len(held) <= 3}
    rows = []
    for target, anchor in relay.SCENARIOS:
        missing = set(target) - {anchor}
        prior = shift.distribution(missing, 6., 1)
        by_route = {}
        for label, reward in endpoints.items():
            dist = policy.script(target, anchor, ids, reward, prior, True)
            score = policy.benefits(target, anchor, ids, dist, observed, bank)
            score["requested_source_receipt_count"] = sum(m * (len(target) - len(left))
                                                           for left, (m, _, _) in dist.items())
            if expert in missing:
                score["expert_receipt"] = sum(m for left, (m, _, _) in dist.items() if expert not in left)
            by_route[label] = score
        rows.append({"target": [ids[i] for i in target], "anchor": ids[anchor], "routes": by_route})
    expert_rows = [r["routes"] for r in rows if "expert_receipt" in r["routes"]["observed_only"]]
    main = [{route: {k: v for k, v in row.items() if k != "expert_receipt"}
             for route, row in case["routes"].items()} for case in rows]
    exact = policy.transfer.mean(main)
    scoped = policy.transfer.mean(expert_rows)
    assert exact["observed_only"]["actual_net_gain"] >= exact["authored_coverage"]["actual_net_gain"] - 1e-9
    return {"scope": "Retrospective exact planners that see reviewed DRC wording. This is an outcome-objective "
                     "diagnostic, not a new learned system. The strongest adaptive scripts have the same true "
                     "prior, contact cap, fees, and two choices for reply priority.",
            "all_cases": exact, "where_expert_source_is_requested_and_missing": scoped, "case_details": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
