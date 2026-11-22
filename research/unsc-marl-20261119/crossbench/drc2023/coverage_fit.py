"""Fit one weighted evidence-coverage policy on the original written-vote task."""
import json
from pathlib import Path
from unittest.mock import patch

import results
from policy_replay import policy
from specialist_fit import batches, optimizer

HERE = results.HERE
relay = policy.relay
shift = policy.shift
read_scores = optimizer.scores
BONUS = 7


def covered_scores():
    return {(target, anchor, pending): score + BONUS * (len(target) - len(pending) - 1)
            for (target, anchor, pending), score in read_scores().items()}


def run():
    with patch.object(optimizer, "scores", covered_scores):
        states, actions, outcomes, mass = batches()
    history, learned = optimizer.fit(states, actions, outcomes, mass)
    replay = optimizer.evaluate(learned["joint_learned"], actions, outcomes, mass)["design_mixture"]
    assert abs(replay["record_reward"] - history[-1]["record_reward"]) < 1e-9
    new = {state: learned["joint_learned"][offset:offset + width].tolist()
           for state, (offset, width) in states.items()}
    docket = results.load(results.writer.CASE)
    products = results.load(results.EVIDENCE / "results.json")["field_packets"]
    origin = results.load(results.EVIDENCE / "policy-replay.json")
    existing = origin["table_alignment"]["rows"]
    bank = results.verified_bank(docket)
    ids = tuple(docket["sources"])
    table = {(row["anchor"], *row["other_cards"]): row for row in existing}
    groups = {}
    important = "EXPERTS"
    for name, prev in origin["conditions"].items():
        strength, desk, kind = shift.CONDITIONS[name]
        predicted = 1 - desk if kind == "wrong_hint" else desk
        rows = []
        for (target, anchor), former in zip(relay.SCENARIOS, prev["rows"], strict=True):
            left = [i for i in target if i != anchor]
            anchor_name = ids[anchor]
            key = (anchor_name, *(ids[i] for i in left))
            assert former["anchor"] == anchor_name and former["target"] == [ids[i] for i in target]
            prior = shift.distribution(left, strength, desk, kind)
            distribution = shift.remap(new, prior, target, anchor, table[key], (predicted, 1 - predicted))
            score = policy.benefits(target, anchor, ids, distribution, products, bank)
            requested = ids.index(important)
            if requested in left:
                score["expert_receipt_when_missing"] = sum(p for pending, (p, _, _) in distribution.items()
                                                           if requested not in pending)
            rows.append({"anchor": anchor_name, "target": former["target"], "coverage_bonus_fit": score})
        expert = [r["coverage_bonus_fit"]["expert_receipt_when_missing"] for r in rows
                  if "expert_receipt_when_missing" in r["coverage_bonus_fit"]]
        totals = policy.transfer.mean([{"fit": {k: v for k, v in r["coverage_bonus_fit"].items()
                                                   if k != "expert_receipt_when_missing"}} for r in rows])["fit"]
        groups[name] = {"coverage_bonus": totals, "original_specialist": prev["mean"]["specialist"],
                        "expert_receipt_when_missing": sum(expert) / len(expert), "rows": rows}
    return {"scope": "One exact joint fit on the original written-vote docket. Its reward adds seven for each "
                     "additional requested source delivered. DRC labels and prose never enter the fit. Evaluation "
                     "uses the same pre-existing alignment and first-pass outputs.",
            "bonus_for_added_requested_source": BONUS, "steps": optimizer.STEPS,
            "trajectory_count": len(actions), "training": history, "stresses": groups,
            "policy": [{"local_state": state, "probabilities": row} for state, row in new.items()],
            "pins": {name: results.writer.runner.digest(path) for name, path in (
                ("optimizer", Path(optimizer.__file__)), ("observed_drc", results.EVIDENCE / "results.json"),
                ("comparison_policy", HERE.parent / "colombia2023/specialist-fit-results.json"))}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
