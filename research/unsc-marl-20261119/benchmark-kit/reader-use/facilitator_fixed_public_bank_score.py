"""Audit national evidence and replay request choices with a locked public record."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import facilitator_fixed_public_bank as study
import facilitator_free_record_bank_plan as plan
import facilitator_free_record_bank_score as previous


def alias(mask):
    return sha256(f"2699-national-review:{mask}".encode()).hexdigest()[:8]


def combine(rows):
    public = study.public_anchor()
    facts = study.free.source.packet()["public"]
    assert public == " ".join(facts) and len(facts) == 6
    combined = {}
    for request in study.free.local():
        mask = request["id"]
        if mask in rows:
            row = rows[mask]
            text = row["output"]
            combined[mask] = {**row, "messages": request["messages"], "output": f"{public}\n\n{text}"}
        else:
            assert mask == "0"
            combined[mask] = {**request, "output": public, "ended": True, "input_ids": [], "output_ids": []}
    return combined


def score(combined, marks):
    reviewed = {}
    facts = study.free.source.packet()["public"]
    inherited = {f"P{i}": ["met", fact] for i, fact in enumerate(facts, 1)}
    assert marks.keys() == {alias(i) for i in map(int, combined) if i}
    for key, row in previous.blind(combined).items():
        review = marks.get(alias(row["mask"]), {"criteria": {}, "material_errors": []})
        assert inherited.keys().isdisjoint(review["criteria"])
        reviewed[key] = {**review, "criteria": {**inherited, **review["criteria"]}}
    return previous.score(combined, reviewed)


def controls(report, opening):
    base, freq, R, D = plan.base, plan.freq, plan.R, plan.D
    observed = np.array(report["released_bank"])
    declared = base.banks()["resolution_2699"][0]
    bit_count = np.array([mask.bit_count() for mask in range(8)])
    output = {}
    for label in base.fit.live.PRIORS:
        p = R.TEST_PRIORS[label]
        planner = plan.IndependentIntervals(declared, observed, p)
        values = freq.returns(observed, planner.quiet)
        publishes = freq.returns((observed > 0).astype(int), planner.quiet)[0]
        card_count = freq.returns(bit_count, planner.quiet)[0]
        output[label] = {}
        for name, right in (("same_priority", base.PRIORITIES[0]), ("opposite_priority", base.PRIORITIES[-1])):
            left = base.PRIORITIES[0]
            mass = base.opening(D.one_hot(left), D.one_hot(right), p).sum(1)
            fee = float(p.sum(1) @ D.SEND_COST[left] + p.sum(0) @ D.SEND_COST[right])
            step = opening["released_bank"]["conditions"][label]["independent"]["steps"][-1]
            policies = {"no_request": np.zeros(16, dtype=int), "score_known_request": np.array(step["policy"])}
            rows = {}
            for policy_name, policy in policies.items():
                expected = freq.score(mass, values, policy, fee)[0]
                states = np.arange(len(policy))
                expected["release_probability"] = float(np.einsum("sr,srq->sq", mass, publishes)[states, policy].sum())
                expected["expected_distinct_cards"] = float(np.einsum("sr,srq->sq", mass, card_count)[states, policy].sum())
                rows[policy_name] = expected
            rows["net_gain"] = rows["score_known_request"]["net"] - rows["no_request"]["net"]
            output[label][name] = rows
    return output


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("blind", "score", "plan"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "plan":
        report = json.loads((args.directory / "results.json").read_text())
        opening = plan.run(report)
        output = {"banks": opening, "controls": controls(report, opening)}
    else:
        combined = combine(study.verify(args.directory))
        if args.mode == "blind":
            output = {}
            for row in previous.blind(combined).values():
                if row["mask"]:
                    output[alias(row["mask"])] = {
                        "authorized_cards": row["evidence"]["authorized_national_cards"],
                        "candidate_section": row["candidate"].split("\n\n", 1)[1], "finished": row["finished"],
                        "eligible": [field for field in row["eligible"] if not field.startswith("P")],
                    }
            output = dict(sorted(output.items()))
        else:
            marks = json.loads((args.directory / "review.json").read_text())
            output = score(combined, marks)
    print(json.dumps(output, ensure_ascii=False, indent=2))
