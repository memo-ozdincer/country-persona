"""Check compressed score vertices against enumerated integer rewards."""
import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_review_selection as fit


def enumerate_scores(anchor, limit):
    unknown = [i for i in range(8) if i not in anchor]
    rows = []
    for values in product(range(limit, 71), repeat=len(unknown)):
        filled = {**anchor, **dict(zip(unknown, values, strict=True))}
        if all(filled[a] <= filled[b] for a, b in fit.SUBSETS):
            rows.append([filled[m] for m in range(8)])
    return np.asarray(rows)


def validate():
    controls = (
        {0: 63, 1: 64, 2: 64, 4: 65},
        {0: 64, 1: 64, 2: 65, 4: 65, 5: 67},
        {0: 63, 1: 66, 2: 65, 4: 64, 7: 69},
    )
    checked = []
    for anchor in controls:
        endpoints = fit.reward_vertices(tuple(sorted(anchor.items())))
        every = fit.encoded(enumerate_scores(anchor, anchor[0]))
        cases = ((prior_name, fit.R.TEST_PRIORS[prior_name]) for prior_name in fit.base.fit.live.PRIORS)
        for name, p in cases:
            # Arbitrary fixed fallback shows that the endpoint reduction
            # covers comparisons on each receipt, not just one chair plan.
            full_scores, vertices = [], []
            for quiet in fit.base.PRIORITIES:
                nominal = fit.freq.nominal_model(p).sum(1)

                def regrets(points):
                    expected = np.stack([np.einsum("sr,srq->sq", nominal, fit.freq.returns(raw, quiet)[-1])
                                         for raw in points])
                    legal = np.where(fit.base.ASK, expected, -np.inf)
                    return (legal.max(-1, keepdims=True) - legal).max(0)

                # Convert terminal values back to material before the
                # separate return helper reapplies its completion bonus.
                to_points = lambda values: values - fit.D.COMPLETE_BONUS * (values > 70)
                full_scores.append(regrets(to_points(every)))
                vertices.append(regrets(to_points(endpoints)))
            assert np.allclose(full_scores, vertices, rtol=0., atol=1e-12)
            checked.append({"prior": name, "anchors": anchor, "full_integer_banks": len(every),
                            "endpoint_banks": len(endpoints), "fallback_tables": len(vertices)})
    return checked


def summarize(path):
    dated = json.loads(path.read_text())["dockets"]
    rows = [v for banks in dated.values() for bank in banks.values() for v in bank["conditions"].values()]
    families = {}
    for key in ("fixed", "visitation", "regret"):
        families[key] = {}
        for maximum in (.25, .5, 1.):
            n = [next(i for i, val in enumerate(pan["paths"][key]) if val["guaranteed_regret_upper"] <= maximum)
                 for pan in rows]
            families[key][str(maximum)] = {"mean_additional_reviews": float(np.mean(n)),
                                           "at_most_two_reviews": int((np.asarray(n) <= 2).sum())}
    return {"verified_vertex_reduction": validate(), "thresholds": families, "benchmark_cells": len(rows)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("report", type=Path)
    print(json.dumps(summarize(cli.parse_args().report), indent=2))
