"""Refit the sender critic to measured release after generated-purpose admission."""
import json

import numpy as np

from purpose_study import HERE, previous, read

source = previous.RUNS / "humanitarian-2664-admission/sender-credit-fit"
sender = previous.load("purpose_sender_fit", source / "train.py")


def evaluate(release_method):
    assert sender.plan() == read(source / "plan.json")
    before = read(source / "results.json")
    release = read(HERE / "scores.json")["cases"]
    orders = ("sponsors-first", "algeria-first")
    target = np.array([[42, 49, 49, release[order][release_method]]
                       for order in orders])
    standalone = target[0, [2, 1]] - target[0, 0]
    log = sender.exploration(target)
    assert [r | {"reward": 0} for r in log] == [
        r | {"reward": 0} for r in before["exploration"]
    ]
    critics = {name: sender.fit_team(log, name)[0] for name in ("order_pooled", "order_aware")}
    truth_rows = []
    for row in before["held"]:
        q, mix = row["delivery"], row["india_first"]
        truth = sender.evaluate_actions(target, standalone, q, mix)
        all_policies = {
            "fixed_withhold": 0, "fixed_send_both": 3,
            "frozen_2664": sender.ACTION_NAMES.index(row["fitted"]["order_aware"]["action"]),
            "target_oracle": sender.choose(truth),
        }
        for name, parameters in critics.items():
            predicted = sender.predict(parameters, name)
            all_policies[name] = sender.choose(sender.evaluate_actions(predicted, standalone, q, mix))
        truth_rows.append({"delivery": q, "algeria_first": mix, "policies": {
            name: truth[action] | {"action": sender.ACTION_NAMES[action]}
            for name, action in all_policies.items()
        }})
    return {
        "terminal_rows": target.tolist(), "observed_rollouts": log, "critics": critics,
        "held": truth_rows,
        "mean": {name: {
            **{metric: round(float(np.mean([r["policies"][name][metric] for r in truth_rows])), 8)
               for metric in ("release", "utility")},
            "oracle_matches": sum(r["policies"][name]["action"] == r["policies"]["target_oracle"]["action"]
                                  for r in truth_rows),
        } for name in truth_rows[0]["policies"]},
    }


if __name__ == "__main__":
    methods = ("mechanical_only_release", "mechanical_plus_verifier_release")
    print(json.dumps({method: evaluate(method) for method in methods}, ensure_ascii=False, indent=2))
