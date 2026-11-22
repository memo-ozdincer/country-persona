"""Check whether adjudication uncertainty or selected worlds explain the policy result."""
import argparse
from itertools import product
import json
from pathlib import Path

from mali_request_writer_review import policies
from source_record_run import digest
from source_request_policy import BITS, STATES


def report(scored, policy, joint, scoped):
    outcome = json.loads(scored.read_text())
    receipts = outcome["records"]
    permissive = []
    for row in receipts:
        allowed = (row["guard"] != "failed" and row["ended"]
                   and row["words"] <= 165 and not row["off_packet_citations"])
        permissive.append({**row, "eligible": allowed, "release_points": row["raw_points"] if allowed else 0})
    scenarios = policies(policy, permissive, {"joint_reader": joint, "scoped_reader": scoped})
    selected = [r for r in scenarios if r["reward"] == "release_points" and r["reader"] == "scoped_reader"]
    acquired = json.loads(policy.read_text())["training"]
    paired = []
    for requester, responder in product(STATES, repeat=2):
        request = acquired["request"][requester]
        direct = BITS[acquired["left_delivery"][requester]]
        actual = int(direct | BITS[acquired["reply"][responder][request]])
        erased = int(direct | BITS[acquired["reply"][responder][0]])
        if actual == erased:
            continue
        score_change = receipts[actual]["raw_points"] - receipts[erased]["raw_points"]
        paired.append({"inventory": [int(requester), int(responder)], "with_request": actual,
                       "request_erased": erased, "raw_points_difference": score_change})
    return {
        "scope": "Sensitivity analysis only. Provisionally admit ambiguous guard judgments, retaining definite error and "
                 "off-packet citation exclusions. Intact-link causal checks hold the table and requester submission fixed.",
        "mali_scores_sha256": digest(scored),
        "permissive_release_points": [x["release_points"] for x in permissive],
        "scoped_reader_sensitivity": selected,
        "intact_link_changed_receipt_worlds": {
            "improved": sum(r["raw_points_difference"] > 0 for r in paired),
            "declined": sum(r["raw_points_difference"] < 0 for r in paired),
            "tied": sum(r["raw_points_difference"] == 0 for r in paired),
            "details": paired,
        },
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for key in ("scores", "policy", "joint", "scoped"):
        cli.add_argument(key, type=Path)
    args = cli.parse_args()
    print(json.dumps(report(args.scores, args.policy, args.joint, args.scoped), ensure_ascii=False, indent=2))
