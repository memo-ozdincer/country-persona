"""Replay reward-aware receivers on the archived Jerusalem partner and writer runs."""
import json
from pathlib import Path

import numpy as np

import transfer

HERE = transfer.HERE


def local(name):
    return json.loads((HERE / name).read_text())


def replay(table):
    current = transfer.Calibration()
    current.points[:] = np.tile([42, 70], (4, 1))
    prior_fit = np.asarray(transfer.read("factored-calibration-results.json")["greedy_receiver_table"])
    actions = local("factored-evidence/actions.json")["desks"]
    generated = local("record-evidence/scores.json")["replays"]
    panels = {"compiled": None, **{name: np.asarray(bank["points"]) for name, bank in generated.items()}}
    out = {}
    for name, points in panels.items():
        peers = {}
        for desk, data in actions.items():
            old = transfer.score(data, prior_fit, current, points)["by_topic_order"]
            new = transfer.score(data, table, current, points)["by_topic_order"]
            full = []
            for order, earlier in old.items():
                for prior, original in earlier["priors"].items():
                    revised = new[order]["priors"][prior]
                    full.append({"order": order, "prior": prior,
                                 "old": original["transferred"], "new": revised["transferred"],
                                 "exact": revised["exact_decoder"], "without_probes": revised["frozen_no_probes"]})
            movement = [row["new"] - row["old"] for row in full]
            peers[desk] = {"canonical": next(row for row in full if row["order"] == "0123"
                                             and row["prior"] == "correlated_development"),
                           "fixed_receiver_difference_range": [min(movement), max(movement)],
                           "wins_vs_old": sum(val > 1e-9 for val in movement),
                           "losses_vs_old": sum(val < -1e-9 for val in movement),
                           "maximum_exact_score_gap": max(abs(row["new"] - row["exact"]) for row in full),
                           "conditions": len(full), "all": full}
        out[name] = peers
    return out


if __name__ == "__main__":
    from reward_receiver import decision_table
    fit = local("reward-receiver.json")
    policy = decision_table(fit["cover"], fit["likelihood"], [28] * 4)
    paths = ("reward-receiver.json", "factored-evidence/actions.json", "record-evidence/scores.json")
    result = {"scope": "Unchanged model outputs, observed probes, loss, fees, and focal cases. "
                       "Both receivers use archived rubric-based policies. Actual generated record scores are evaluation only.",
              "code_sha256": transfer.routing.digest(Path(__file__)),
              "source_sha256": {name: transfer.routing.digest(HERE / name) for name in paths},
              "panels": replay(policy)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
