"""Compare acquisition bounds with and without monotone receipt scores."""
from functools import lru_cache
from itertools import product
import json

import numpy as np

import facilitator_review_selection as review
from facilitator_free_record_bank import EVIDENCE

base, freq, R, D = review.base, review.freq, review.R, review.D


class IndependentIntervals(review.Review):

    @lru_cache(maxsize=25000)
    def robust(self, anchors):
        scores = np.zeros((2 ** (8 - len(anchors)), 8), dtype=int)
        for mask, score in anchors:
            scores[:, mask] = score
        missing = sorted(set(range(8)) - dict(anchors).keys())
        if missing:
            scores[:, missing] = list(product((0, 70), repeat=len(missing)))
        utilities = self.decisions(review.encoded(scores))
        regret = utilities.max(-1, keepdims=True) - utilities
        upper = regret.max(0)
        policy = upper.argmin(-1)
        return policy, float(upper[np.arange(len(policy)), policy].sum())

    def review(self, anchors, mode):
        candidates = set(review.UNKNOWN) - dict(anchors).keys()

        def worst_after(mask):
            return max(self.robust(tuple(sorted((*anchors, (mask, score)))))[1]
                       for score in range(71)), mask

        return min(candidates, key=worst_after)


def violations(anchors):
    known = dict(anchors)
    return [[a, b, known[a], known[b]] for a, b in review.SUBSETS
            if a in known and b in known and known[a] > known[b]]


def path(planner, actual, monotone):
    anchors = planner.initial
    target = planner.decisions(review.encoded(actual)[None])[0]
    steps = []
    acquired = []
    bank_matches_assumption = not monotone or not violations(tuple(enumerate(actual)))
    while True:
        conflict = violations(anchors) if monotone else []
        if conflict:
            return steps, conflict
        policy, bound = planner.robust(anchors)
        nominal = float(target.max(-1).sum() - target[np.arange(len(policy)), policy].sum())
        if bank_matches_assumption:
            assert nominal <= bound + 1e-10
        if steps:
            assert steps[-1]["bound"] >= bound - 1e-10
        steps.append({"reviewed": acquired.copy(), "anchors": dict(anchors), "bound": bound, "nominal_regret": nominal,
                      "policy": policy.tolist(), "bound_holds": nominal <= bound + 1e-10})
        if len(anchors) == len(actual):
            assert abs(bound) < 1e-10
            return steps, []
        pick = planner.review(anchors, "regret")
        acquired.append(pick)
        anchors = tuple(sorted((*anchors, (pick, int(actual[pick])))))


def run(scored):
    public = base.banks()["resolution_2699"][0]
    banks = {k: scored[k] for k in ("material_bank", "released_bank")}
    banks["fixed_renderer"] = public.tolist()
    outcomes = {}
    for key, values in banks.items():
        actual = np.array(values)
        conditions = {}
        for name in base.fit.live.PRIORS:
            p = R.TEST_PRIORS[name]
            paths = {}
            for method, cls in (("monotone", review.Review), ("independent", IndependentIntervals)):
                planner = cls(public, actual, p)
                steps, conflict = path(planner, actual, method == "monotone")
                for team, right in (("same_priority", base.PRIORITIES[0]), ("opposite_priority", base.PRIORITIES[-1])):
                    left = base.PRIORITIES[0]
                    mass = base.opening(D.one_hot(left), D.one_hot(right), p).sum(1)
                    fee = float(p.sum(1) @ D.SEND_COST[left] + p.sum(0) @ D.SEND_COST[right])
                    values_by_action = freq.returns(actual, planner.quiet)
                    for step in steps:
                        metrics = freq.score(mass, values_by_action, np.array(step["policy"]), fee)[0]
                        metrics["record_points"] = metrics.pop("guarded_points")
                        step.setdefault("teams", {})[team] = metrics
                paths[method] = {"steps": steps, "contradictory_anchors": conflict}
                planner.robust.cache_clear()
            conditions[name] = paths
        outcomes[key] = {"points": actual.tolist(), "conditions": conditions}
    return outcomes


if __name__ == "__main__":
    print(json.dumps(run(json.loads((EVIDENCE / "results.json").read_text())), indent=2))
