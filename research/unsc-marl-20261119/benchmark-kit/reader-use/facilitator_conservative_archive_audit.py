"""Verify documentary receipt probabilities and costs by direct event enumeration."""
from itertools import product
import json

import numpy as np

import facilitator_conservative_frequency as fit

base, D, R = fit.base, fit.D, fit.R


def direct(prior, left, right, quiet, chair, points):
    expected = 0.
    for a, b in product(range(8), repeat=2):
        x, y = left[a], right[b]
        for flags in product((0, 1), repeat=4):
            ox, oy, heard, delivered = flags
            weight = prior[a, b] * (1 - D.LOSS) ** sum(flags) * D.LOSS ** (4 - sum(flags))
            q = chair[4 * x * ox + y * oy]
            c = q if q and heard and R.SEND[b, q] else quiet[b]
            mask = R.BITS[x] * ox | R.BITS[y] * oy | R.BITS[c] * delivered
            reward = points[mask] + (D.COMPLETE_BONUS if points[mask] == 70 else 0.)
            expected += weight * (reward - D.SEND_COST[x] - D.SEND_COST[y] - D.SEND_COST[c] - D.QUERY_COST[q])
    return expected


def audit():
    # Every allowed model must send a held singleton by construction.
    assert len(base.TABLES) == 24
    assert all(np.array_equal(base.TABLES[:, mask], np.full(24, topic)) for topic, mask in enumerate(R.BITS[1:], 1))
    outputs = json.loads((base.EVIDENCE / "frequency.json").read_text())["dockets"]
    flags = 0
    for name, (declared, reviewed) in base.banks().items():
        style = {"same_priority": (base.PRIORITIES[0], base.PRIORITIES[0]),
                 "opposite_priority": (base.PRIORITIES[0], base.PRIORITIES[-1])}
        for label in base.fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            nominal = fit.nominal_model(prior)
            for tag, (x, y) in style.items():
                for name_of_rule, planned in (("declared", declared), ("review_calibrated", reviewed)):
                    quiet = fit.fallback(nominal, planned)
                    ask = fit.best_for(nominal.sum(1), fit.returns(planned, quiet)[-1])
                    expected = direct(prior, x, y, quiet, ask, reviewed)
                    result = outputs[name]["conditions"][f"{label}/{tag}"][name_of_rule]["baseline"]["net"]
                    assert abs(expected - result) < 1e-12
                    flags += 1
    return {"verified_expected_baseline_cells": flags, "inventory_loss_branches_per_cell": 1024,
            "forced_singleton_reports_in_every_local_policy": True}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
