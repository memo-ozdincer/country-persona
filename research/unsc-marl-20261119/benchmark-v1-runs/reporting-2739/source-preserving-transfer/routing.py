"""Evaluate the frozen 2664 send rule on the new writer scores."""
import json

import numpy as np

from study import HERE, RUNS, base, load

SENDER = RUNS / "humanitarian-2664-admission/sender-credit-fit"
sender = load("sender_2664", SENDER / "train.py")


def run():
    assert sender.plan() == base.read(SENDER / "plan.json")
    fit = base.read(SENDER / "results.json")
    outcome = base.read(HERE / "scores.json")["outcomes"]
    left, right, neither = (outcome[key]["standalone"] for key in ("sponsors", "algeria", "none"))
    facts = np.array([neither, right, left, left + right - neither])
    standalone = np.array([left - neither, right - neither])
    target = np.stack([facts, facts])
    source = target.astype(float)
    target[:, -1] = [outcome[key]["known_pair"] for key in ("sponsors-first", "algeria-first")]
    source[:, -1] += fit["fit"]["order_aware"]["coefficients"][-2:]
    adopted_orders = ("sponsors-first", "algeria-first")
    rows = []
    for r in fit["held"]:
        p, mix = r["delivery"], r["india_first"]
        measured = sender.evaluate_actions(target, standalone, p, mix)
        predicted = sender.evaluate_actions(source, standalone, p, mix)
        chosen = sender.choose(predicted)
        oracle = sender.choose(measured)
        assert sender.ACTION_NAMES[chosen] == r["fitted"]["order_aware"]["action"]
        rows.append({"delivery": p, "algeria_first": mix,
                     "transfer_send": sender.ACTION_NAMES[chosen],
                     "oracle_send": sender.ACTION_NAMES[oracle],
                     "transfer_utility": measured[chosen]["utility"],
                     "oracle_utility": measured[oracle]["utility"],
                     "transfer_release": measured[chosen]["release"],
                     "withhold_utility": measured[0]["utility"]})
    return {
        "full_receipt_orders": adopted_orders,
        "predicted_native_append_gain": (source[:, -1] - facts[-1]).tolist(),
        "observed_native_append_gain": (target[:, -1] - facts[-1]).tolist(),
        "oracle_matches": sum(row["transfer_send"] == row["oracle_send"] for row in rows),
        "mean": {key: round(float(np.mean([row[key] for row in rows])), 8)
                 for key in ("transfer_utility", "oracle_utility", "transfer_release", "withhold_utility")},
        "held": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
