"""Exhaustive honest-clarification ceiling and communication-cost baseline."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from environment import HOLD, outcome
from evaluate import exhaustive_worlds


def decide(case, leader, limit):
    local, counterpart = case["mandates"][leader], case["mandates"][1 - leader]
    offers = [menu.index(1) for menu in case["mandates"]]
    other_offer = offers[1 - leader]
    if local[other_offer]:
        return "agreement", other_offer, []
    candidates = [i for i, allowed in enumerate(local) if allowed]
    replies = []
    for option in candidates[:limit]:
        accept = bool(counterpart[option])
        replies.append((option, accept))
        if accept:
            return "agreement", option, replies
    if len(replies) == len(candidates):
        return "deadlock", HOLD, replies
    return "unresolved", None, replies


def assess(cases, limit):
    counts = Counter()
    overhead = []
    for case in cases:
        # Evaluate both leader choices. Each question and reply is one message.
        feasible = any(a and b for a, b in zip(*case["mandates"]))
        for leader in (0, 1):
            state, action, replies = decide(case, leader, limit)
            counts["feasible" if feasible else "infeasible"] += 1
            counts[state] += 1
            overhead.append(len(replies))
            if state == "unresolved":
                continue
            strict = outcome(case, [m.index(1) for m in case["mandates"]], [action] * 2)
            assert strict["strict"] and (state == "agreement") == feasible
    available = len(overhead)
    return {
        "presentations": available, "feasible": counts["feasible"], "infeasible": counts["infeasible"],
        "verified_agreement": counts["agreement"], "verified_deadlock": counts["deadlock"],
        "unresolved": counts["unresolved"],
        "agreement_recall": counts["agreement"] / counts["feasible"],
        "deadlock_recall": counts["deadlock"] / counts["infeasible"],
        "mean_query_reply_pairs": mean(overhead), "mean_messages_including_openings_and_disposition": 3 + 2 * mean(overhead),
    }


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("output", type=Path)
    models = {
        family: {budget: assess(cases, budget) for budget in range(len(cases[0]["options"]) + 1)}
        for family in ("climate", "sanctions", "women_peace_security") if (cases := exhaustive_worlds(family))
    }
    with args.parse_args().output.open("x") as stream:
        json.dump(models, stream, indent=2)
        stream.write("\n")
