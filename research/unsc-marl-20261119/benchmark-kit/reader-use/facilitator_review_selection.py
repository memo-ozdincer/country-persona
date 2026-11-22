"""Select pair and full-record audits by their impact on request regret."""
import argparse
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_conservative_archive_calibration as calibration

freq, base = calibration.study, calibration.base
R, D = base.R, base.D
HERE = base.HERE
EVIDENCE = HERE / "facilitator-review-selection-evidence"
START = (0, 1, 2, 4)
UNKNOWN = (3, 5, 6, 7)
SUBSETS = tuple((a, b) for a, b in product(range(8), repeat=2) if a != b and a & b == a)


def encoded(value):
    return value + D.COMPLETE_BONUS * (value == 70)


@lru_cache(maxsize=10000)
def reward_vertices(observed):
    """Vertices sufficient to maximize any linear difference in policy return."""
    pinned = np.asarray([value for _, value in observed])
    coordinate = tuple(mask for mask, _ in observed)
    missing = tuple(i for i in range(8) if i not in coordinate)
    supports = sorted(set(pinned.tolist()) | {0, 69, 70})
    scores = np.zeros((len(supports) ** len(missing), 8), dtype=int)
    scores[:, coordinate] = pinned
    if missing:
        scores[:, missing] = np.array(list(product(supports, repeat=len(missing))))
    lo, hi = zip(*SUBSETS, strict=True)
    scores = scores[(scores[:, lo] <= scores[:, hi]).all(1)]
    assert len(scores)
    return encoded(scores)


def critical_visitation(trace):
    # The maximum over queries is calculated separately for each opening.
    return np.where(base.ASK[..., None], trace, 0.).max(axis=1).sum(0)


class Review:

    def __init__(self, public, actual, p):
        self.nominal = freq.nominal_model(p).sum(1)
        self.declared = public
        self.corrected = calibration.correct_singletons(public, actual)
        self.quiet = freq.fallback(freq.nominal_model(p), self.corrected)
        # This tensor is the probability of ending in final mask k after q
        # at sender-attributed state s, with the nominal opening model.
        respond = np.where(R.SEND & (R.ACTIONS != 0), R.ACTIONS, self.quiet[:, None])
        tried = (1 - D.LOSS) * D.one_hot(respond) + D.LOSS * D.one_hot(self.quiet)[:, None, :]
        self.trace = np.einsum("sr,rqc,sck->sqk", self.nominal, tried, D.LAST[base.MASKS])
        cost = np.einsum("sr,rqc,c->sq", self.nominal, tried, D.SEND_COST)
        self.fee = cost + self.nominal.sum(1)[:, None] * D.QUERY_COST
        self.visitation = critical_visitation(self.trace)
        self.initial = tuple((mask, int(actual[mask])) for mask in START)

    def decisions(self, values):
        raw = np.einsum("sqk,pk->psq", self.trace, values) - self.fee
        return np.where(base.ASK, raw, -np.inf)

    @lru_cache(maxsize=25000)
    def robust(self, anchors):
        utilities = self.decisions(reward_vertices(anchors))
        regret = utilities.max(-1, keepdims=True) - utilities
        upper = regret.max(0)
        policy = upper.argmin(-1)
        return policy, float(upper[np.arange(16), policy].sum())

    def review(self, anchors, mode):
        revealed = dict(anchors)
        available = [i for i in UNKNOWN if i not in revealed]
        if mode == "fixed":
            return available[0]
        if mode == "visitation":
            return max(available, key=lambda mask: (self.visitation[mask], -mask))
        assert mode == "regret"
        after = {}
        for mask in available:
            lo = max(v for m, v in anchors if m & mask == m)
            hi = min((v for m, v in anchors if m & mask == mask), default=70)
            after[mask] = max(self.robust(tuple(sorted((*anchors, (mask, value)))))[1]
                              for value in range(lo, hi + 1))
        return min(available, key=lambda mask: (after[mask], mask))

    def evaluate(self, actual, mass, fee):
        target = self.decisions(encoded(actual)[None])[0]
        best = target.max(-1).sum()
        values = freq.returns(actual, self.quiet)

        def measure(policy):
            # Report regret for the same nominal inputs used in planning, and
            # separately replay the fixed policy on the observed opening team.
            output = freq.score(mass, values, policy, fee)[0]
            output["nominal_regret"] = float(best - target[np.arange(16), policy].sum())
            return output

        declared = self.decisions(encoded(self.declared)[None])[0].argmax(-1)
        corrected = self.decisions(encoded(self.corrected)[None])[0].argmax(-1)
        rows = {"declared_point_plan": measure(declared), "singleton_point_plan": measure(corrected),
                "full_review_plan": measure(target.argmax(-1)), "paths": {}}
        for mode in ("fixed", "visitation", "regret"):
            anchors = self.initial
            progress = []
            acquired = []
            for n in range(5):
                policy, bound = self.robust(anchors)
                score = measure(policy)
                assert score["nominal_regret"] <= bound + 1e-10
                progress.append({"reviewed": acquired.copy(), "guaranteed_regret_upper": bound, **score})
                if n < 4:
                    pick = self.review(anchors, mode)
                    acquired.append(pick)
                    anchors = tuple(sorted((*anchors, (pick, int(actual[pick])))))
            assert all(u["guaranteed_regret_upper"] >= v["guaranteed_regret_upper"] - 1e-10
                       for u, v in zip(progress, progress[1:]))
            rows["paths"][mode] = progress
        return rows


def outcomes(public, actual):
    yield "archived", actual
    singleton = public[[0, 1, 2, 4]]
    additive = singleton[0] + ((np.arange(8)[:, None] & R.BITS[1:]) != 0) @ (singleton[1:] - singleton[0])
    extras = public[[3, 5, 6]] - additive[[3, 5, 6]]
    if (extras > 0).any():
        for rotation in (1, 2):
            alternate = additive.copy()
            alternate[[3, 5, 6]] += np.roll(extras, rotation)
            alternate[7] = public[7]
            yield f"shift_pair_bonus_{rotation}", alternate
    if actual[7] == 70 and max(actual[:7]) < 70:
        lowered = actual.copy()
        lowered[7] = max(actual[:7])
        yield "full_score_shortfall", lowered


def run():
    out = {}
    for docket, (public, assessed) in base.banks().items():
        variants = {}
        for label, actual in outcomes(public, assessed):
            assert all(actual[a] <= actual[b] for a, b in SUBSETS)
            rows = {}
            for name in base.fit.live.PRIORS:
                p = R.TEST_PRIORS[name]
                planner = Review(public, actual, p)
                for opener, (left, right) in {"same_priority": (base.PRIORITIES[0], base.PRIORITIES[0]),
                                             "opposite_priority": (base.PRIORITIES[0], base.PRIORITIES[-1])}.items():
                    mass = base.opening(D.one_hot(left), D.one_hot(right), p).sum(1)
                    fee = float(p.sum(1) @ D.SEND_COST[left] + p.sum(0) @ D.SEND_COST[right])
                    rows[f"{name}/{opener}"] = planner.evaluate(actual, mass, fee)
                planner.robust.cache_clear()
            variants[label] = {"actual_scores": actual.tolist(), "conditions": rows}
        out[docket] = variants
    paths = (Path(__file__), EVIDENCE / "protocol.md", Path(base.__file__), Path(freq.__file__),
             Path(calibration.__file__))
    return {"starting_reviews": START, "extra_review_candidates": UNKNOWN, "dockets": out,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
