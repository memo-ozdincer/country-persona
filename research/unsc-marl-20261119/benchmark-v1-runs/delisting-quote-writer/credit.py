"""Measure how each valid comparison affects the routing policy in isolation."""
from itertools import combinations
import json
from unittest.mock import patch

import numpy as np

import quote_writer

scoring = quote_writer.scoring
read = scoring.read


def run():
    case = read(scoring.CASE / "case.json")
    prior = read(scoring.CASE / "results.json")
    policies = [tuple(np.array(prior[history][-1][name]) for name in ("sender", "receiver"))
                for history in ("history", "sampled_history")]
    bank = scoring.earlier["bank"](case, read(scoring.CASE / "verified.json")["outputs"])[1]
    pairs = {key: row for key, row in prior["records"].items() if row["expected"]}
    assert len(pairs) == 2
    results = []
    with patch.object(scoring.team, "PRIVATE", {"2664": ("full", "diversion", "request-only"),
                                                "2744": tuple(case["early"])}):
        for size in range(len(pairs) + 1):
            for credited in combinations(pairs, size):
                for i, (early, delegate) in enumerate(case["early"].items()):
                    for j, (late, document) in enumerate(case["late"].items()):
                        key = f"{early}/{late}"
                        bank[3][1, i, j] = (pairs[key]["ideal"] if key in credited else
                                            sum(item["weight"] for item in case["public"]) +
                                            delegate["weight"] + document["weight"])
                comparison = scoring.evaluate(bank, *policies)["mean_utility"]["2744"]
                results.append({"credited": credited, **comparison,
                                "gain_over_arrival": round(comparison["native_fit"] -
                                                           comparison["best_arrival_only"], 8)})
    return results


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
