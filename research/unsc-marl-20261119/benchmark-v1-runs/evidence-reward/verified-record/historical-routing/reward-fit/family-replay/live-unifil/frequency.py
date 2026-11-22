"""Place the selected receipt witness inside the all-delivered prior."""
import json

import review_witness_run as review

m = review.m
e = m.e


def run():
    context, selected, plan = m.select()
    scores, label, law, *_ = context
    by_arm = {}
    comparison = {a: {"higher_score_mass": 0., "equal_score_mass": 0., "lower_score_mass": 0.}
                  for a in m.ARMS[1:]}
    for row, columns in enumerate(law):
        for col, probability in enumerate(columns):
            if probability == 0.:
                continue
            streams = {r["arm"]: r for r in m.simulate(context, (row, col), m.ideal)}
            outcome = {}
            for arm, record in streams.items():
                released = float(scores[record["final_mask"]])
                outcome[arm] = released
                summary = by_arm.setdefault(arm, {"released": 0., "cost": 0.})
                summary["released"] += probability * released
                summary["cost"] += probability * record["cost"]
            for arm, summary in comparison.items():
                comparison_kind = "higher" if outcome["learned"] > outcome[arm] else (
                    "lower" if outcome["learned"] < outcome[arm] else "equal")
                summary[comparison_kind + "_score_mass"] += probability
    assert all(abs(sum(values.values()) - 1.) < 1e-10 for values in comparison.values())
    return {"prior": label, "requested_witness": list(selected), "modeled_witness_mass": plan["modeled_joint_mass"],
            "archived_score_means_under_ideal_delivery": by_arm, "quality_comparison_learned_vs_control": comparison}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
