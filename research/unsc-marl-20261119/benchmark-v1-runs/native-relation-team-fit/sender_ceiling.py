"""Diagnose remaining routing regret with the native-fit reply policy held fixed."""
from collections import Counter
import json

import numpy as np

from fit import HERE, read, tables, team


def run():
    fit = read(HERE / "results.json")
    table = tables(fit["grades"])[0]["audited_native"]
    public, first, last, both, observed = table
    families = list(team.PRIVATE)
    evaluation = fit["evaluation"]["audited_native"]
    summaries = {}
    for docket, name in enumerate(families):
        whole, wrong = [], Counter()
        for record in evaluation["held"]:
            if record["family"] != name:
                continue
            chosen = record["native_fit"]
            mapping = np.array(chosen["reply"])
            q0, q1, price = (record[k] for k in ("q_first", "q_reply", "cost"))
            prior = np.array(record["private_prior"])
            absent = (1-q1)*public[docket] + q1*last[docket, mapping[0]]
            present = (1-q1)*first[docket] + q1*both[docket, np.arange(3), mapping[observed[docket]]]
            send_gain = q0*(present-absent)-price
            best = float(prior @ (absent + np.maximum(send_gain, 0)))
            whole.append(best)
            for view, gain, sent in zip(team.PRIVATE[name], send_gain, chosen["send"], strict=True):
                if abs(gain) > 1e-9 and bool(sent) != (gain > 0):
                    wrong[view] += 1
        best = round(float(np.mean(whole)), 8)
        summary = evaluation["mean_utility"][name]
        assert best <= summary["oracle"] + 1e-8
        summaries[name] = {"rows": len(whole), "sender_actions_below_ceiling_by_view": dict(wrong),
                           "optimized_sender_with_learned_reply": best,
                           "regret_from_sender": round(best - summary["native_fit"], 8),
                           "remaining_regret_from_reply": round(summary["oracle"] - best, 8)}
    return summaries


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
