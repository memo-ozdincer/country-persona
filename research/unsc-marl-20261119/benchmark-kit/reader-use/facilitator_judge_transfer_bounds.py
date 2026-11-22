"""Measure the ceiling of positive-only rechecking on the archived draft bank."""
import argparse
import json

import facilitator_judge_transfer_replay as study


def run(primary, challenge, weights):
    bank = study.test.gather()
    reference = {k: row["passed"] for k, (_, row) in bank.items()}
    positive_only = {k: {**row, "clear": reference[k]} for k, row in challenge.items()}
    full = {k: {**row, "strict_pass": reference[k]} for k, row in primary.items()}
    out = {}
    for name, points, first, second in study.pairs.contexts():
        if not name.startswith("2719_"):
            continue
        # Full review uses the manually reviewed admissions and reports net only;
        # the costs in this diagnostic are not prices for manual review.
        yes = study.run_scenario(points, first, second, weights, primary, positive_only)
        complete = study.run_scenario(
            points, first, second, weights, full,
            {k: {"clear": True, "input_tokens": 0, "output_tokens": 0} for k, v in reference.items() if v})
        result = {}
        for prior in study.fit.live.PRIORS:
            a = yes["primary"]["scores"][prior]["ideal_fit"]
            b = yes["all_positive"]["scores"][prior]["ideal_fit"]
            c = complete["primary"]["scores"][prior]["ideal_fit"]
            assert a["audited_net"] <= b["audited_net"] + 1e-10 <= c["audited_net"] + 2e-10
            result[prior] = {"actual_first_gate": a["audited_net"], "perfect_review_of_initial_positives": b["audited_net"],
                             "review_of_all_candidates": c["audited_net"],
                             "gain_possible_with_perfect_positive_check": b["audited_net"] - a["audited_net"],
                             "loss_due_to_first_stage_missed_valid_candidates": c["audited_net"] - b["audited_net"]}
        out[name] = result
    return out


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = study.test.EVIDENCE
    files = (root / "first.json", root / "challenge.json", study.test.HERE / "facilitator-measured-channel-evidence/fits.json")
    print(json.dumps(run(*(study.trained.read(p) for p in files)), indent=2))
