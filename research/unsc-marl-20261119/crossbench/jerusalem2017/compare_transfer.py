"""Summarize the transcript, release and reward-shift contrasts."""
import json

import numpy as np

import transfer

HERE = transfer.HERE
JSONS = {"typed": "typed-transfer.json", "language": "language-transfer.json",
          "factored": "factored-transfer.json"}


def read(name):
    return json.loads((HERE / name).read_text())


def margins(bank):
    results = {}
    for desk, entry in bank.items():
        rows = [value for order in entry["by_topic_order"].values() for value in order["priors"].values()]
        a = np.array([row["transferred"] - row["exact_decoder"] for row in rows])
        b = np.array([row["transferred"] - row["frozen_no_probes"] for row in rows])
        results[desk] = {"canonical_development_prior": entry["by_topic_order"]["0123"]["priors"]["correlated_development"],
                         "expected_action_disagreement": {order: v["expected_action_disagreement"]
                                                          for order, v in entry["by_topic_order"].items()},
                         "transferred_advantage_vs_exact_range": [float(a.min()), float(a.max())],
                         "transferred_advantage_vs_frozen_range": [float(b.min()), float(b.max())],
                         "wins_vs_frozen": int((b > 1e-9).sum()), "conditions": len(b)}
    return results


def main():
    cases = {name: read(path) for name, path in JSONS.items()}
    assert cases["typed"]["scores"] == cases["factored"]["scores"]
    assert cases["typed"]["desks"] == cases["factored"]["desks"]
    old = transfer.Calibration()
    new = transfer.Calibration()
    new.points[:] = np.tile([42, 70], (4, 1))
    table = np.asarray(transfer.read("factored-calibration-results.json")["greedy_receiver_table"])
    old_exact, new_exact = [], []
    for bits in transfer.routing.REQUESTS:
        state = tuple(-1 if bit else 1 for bit in bits)
        old_exact.append(old.receiver(old.probabilities(state), old.design_prior))
        new_exact.append(new.receiver(new.probabilities(state), new.design_prior))
    assert np.array_equal(table, old_exact)
    difference = table != new_exact
    assert np.all(np.asarray(new_exact)[difference] == 2)
    arrays = {name: margins(run["scores"]) for name, run in cases.items()}
    measured = read("record-evidence/scores.json")
    arrays.update({key: margins(value["desks"]) for key, value in measured["replays"].items()})
    hashes = [*JSONS.values(), "record-evidence/scores.json"]
    return {"scope": "Coordinates are synthetic inventory assignments, not independent dialogues or dates. "
                     "The factored partner's measured schedules agree with the typed plan despite paraphrase.",
            "score_hashes": {name: transfer.routing.digest(HERE / name) for name in hashes},
            "old_receipt_values": old.points.tolist(), "new_announced_receipt_values": new.points.tolist(),
            "decisions_changed_by_reward_shift": int(difference.sum()), "total_decisions": difference.size,
            "claim_records": measured["records"], "comparisons": arrays}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
