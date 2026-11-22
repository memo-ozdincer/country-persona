"""Verify recorded randomized policies as mixtures of deterministic tables."""
import json
from pathlib import Path

import numpy as np

from robust_followup import HERE, READ, TARGET, WRITERS, s


def run():
    results = {}
    init = READ(s.INITIAL)["training"]["budget_fit"]
    paths = [Path(__file__)]
    for name in WRITERS:
        bank = TARGET / "scoped-writer" / f"{name}-bank.json"
        scores = np.array(READ(bank)["score_bank"], dtype=float)
        file = HERE / f"robust-{name}.json"
        paths.extend((bank, file))
        rows = []
        for row in READ(file)["rows"]:
            law, proxy = s.a.laws()[row["law"]]
            announced = law if row["prior_information"] == "exact" else proxy
            opening, _, _ = s.context(scores, scores[3], announced, init)
            actual_mass = s.o.opening(*opening, law)
            for correction, arms in row["arms"].items():
                for arm, value in arms.items():
                    if not value["policy"]["stochastic"]:
                        continue
                    query, reply = (np.asarray(part) for part in value["policy"]["deployed_actions"])
                    cumulative = np.cumsum(reply, axis=-1)
                    assert np.all(reply >= -1e-12)
                    assert np.allclose(cumulative[..., -1], 1.0, atol=1e-9, rtol=0)
                    breaks = np.unique(np.r_[0., np.clip(cumulative[..., :3].ravel(), 0, 1), 1.])
                    total = {key: 0. for key in ("released", "cost", "net", "queries")}
                    receipts = np.zeros(8)
                    for left, right in zip(breaks[:-1], breaks[1:], strict=True):
                        midpoint = (left + right) / 2
                        actions = (cumulative[..., :3] <= midpoint).sum(axis=-1)
                        score = s.o.measure(scores, actual_mass, law, opening, (query, actions))
                        for key in total:
                            total[key] += float((right - left) * score[key])
                        receipts += (right - left) * np.asarray(score["receipt_mass"])
                    assert np.allclose(receipts, value["receipt_mass"], atol=1e-9, rtol=0)
                    error = max(abs(result - value["result"][key]) for key, result in total.items())
                    assert error <= 1e-9
                    rows.append({"law": row["law"], "prior_information": row["prior_information"],
                                 "review_offset": row["review_offset"], "correction": correction,
                                 "arm": arm, "deterministic_mixture_terms": len(breaks) - 1,
                                 "maximum_absolute_error": error})
        results[name] = rows
    assert sum(map(len, results.values())) == 14
    return {"verified": sum(map(len, results.values())), "rows": results,
            "sha256": {file.name: s.digest(file) for file in paths}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
