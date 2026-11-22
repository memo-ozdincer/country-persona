"""Measure how limited writer audits change the 2664 two-desk send policy."""
from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations, product
import json

import numpy as np

from audit import HERE, RUNS

FIT = RUNS / "humanitarian-2664-admission/sender-credit-fit/train.py"
spec = spec_from_file_location("sender_fit", FIT)
sender = module_from_spec(spec)
spec.loader.exec_module(sender)


def run():
    assert sender.plan() == json.loads((FIT.parent / "plan.json").read_text())
    full, standalone = sender.reward_data()
    writer = json.loads((HERE / "results.json").read_text())["2664"]["writers"]["append"]
    orders = ("safeguards-first", "india-first")
    rank = [orders.index(r["context"]) for r in writer["rank"]]
    deltas = {order: int(full[i, 3] - (full[i, 2] + full[i, 1] - full[i, 0]))
              for i, order in enumerate(orders)}
    assert deltas == {r["context"]: r["release_delta"] for r in writer["rank"]}
    fallback = full.copy()
    fallback[:, 3] = fallback[:, 2] + fallback[:, 1] - fallback[:, 0]

    def evaluate(audited, p, order_p):
        table = fallback.copy()
        for order in audited:
            table[order, 3] = max(full[order, 3], table[order, 3])
        actual = sender.evaluate_actions(table, standalone, p, order_p)
        best = sender.choose(actual)
        return actual[best] | {"action": sender.ACTION_NAMES[best]}

    test = []
    for p, order_p in product(sender.TEST_DELIVERY, sender.TEST_MIX):
        oracle = evaluate((0, 1), p, order_p)
        rows = {}
        for budget in (0, 1, 2):
            subsets = list(combinations(range(len(orders)), budget))
            for kind, groups in (("ranked", [rank[:budget]]), ("uniform", subsets)):
                outcomes = [evaluate(group, p, order_p) for group in groups]
                rows[f"{kind}_{budget}"] = {
                    **{key: round(float(np.mean([v[key] for v in outcomes])), 8)
                       for key in ("utility", "release", "cost")},
                    "probability_send_both": sum(v["action"] == "both" for v in outcomes) / len(outcomes),
                    "regret": round(oracle["utility"] - np.mean([v["utility"] for v in outcomes]), 8),
                }
        test.append({"delivery": p, "india_first": order_p, "all_audited": oracle, "policies": rows})
    return {
        "score_source_sha256": sender.digest(sender.SOURCE),
        "ranking": [orders[i] for i in rank],
        "mean": {key: {metric: round(float(np.mean([r["policies"][key][metric] for r in test])), 8)
                       for metric in values}
                 for key, values in test[0]["policies"].items()},
        "held": test,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
