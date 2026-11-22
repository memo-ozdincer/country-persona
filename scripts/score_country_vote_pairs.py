"""Score one matched pair of vote predictions per delegation and decision.

Both input JSON files contain arrays of records keyed by decision. The reference
has a votes mapping. Predictions have base and candidate mappings. Each mapping
uses country codes as keys and yes/no/abstain as values. Use invalid for a failed
prediction, so it stays in the denominator.
"""
import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
from statistics import mean


def index(path):
    rows = json.loads(path.read_text())
    result = {row["decision"]: row for row in rows}
    if not rows or len(result) != len(rows):
        raise ValueError("Require unique decisions and a nonempty input")
    return result


def score(votes, predictions):
    valid = {"yes", "no", "abstain"}
    if not votes or not set(votes.values()) <= valid:
        raise ValueError("Require nonempty observed yes/no/abstain votes")
    split = [(a, b) for a, b in combinations(votes, 2) if votes[a] != votes[b]]
    output = {}
    for arm in ("base", "candidate"):
        p = predictions[arm]
        if p.keys() != votes.keys() or not set(p.values()) <= valid | {"invalid"}:
            raise ValueError("Each arm must predict every observed delegation once")
        output[arm] = dict(correct=sum(p[k] == v for k, v in votes.items()),
                           roles=len(votes), invalid=sum(x == "invalid" for x in p.values()),
                           split_pairs_correct=sum(p[a] == votes[a] and p[b] == votes[b] for a, b in split),
                           split_pairs=len(split))
    transitions = Counter()
    for k, v in votes.items():
        a, b = predictions["base"][k], predictions["candidate"][k]
        if "invalid" in (a, b):
            transitions["includes_invalid"] += 1
        elif a != b:
            transitions["toward" if b == v else "away" if a == v else "wrong_to_wrong"] += 1
        else:
            transitions["unchanged"] += 1
    output["movement_counts"] = dict(transitions)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    truth, preds = index(args.reference), index(args.predictions)
    if truth.keys() != preds.keys():
        raise ValueError("Decision sets differ")
    events = {k: score(r["votes"], preds[k]) for k, r in truth.items()}
    rates = {}
    for arm in ("base", "candidate"):
        rows = [e[arm] for e in events.values() if e[arm]["split_pairs"]]
        rates[arm] = mean(r["split_pairs_correct"] / r["split_pairs"] for r in rows) if rows else None
    print(json.dumps(dict(events=events, equal_event_split_pair_accuracy=rates), indent=2))


if __name__ == "__main__":
    main()
