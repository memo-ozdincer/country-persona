"""Apply conservative request selection to archived, reviewed documentary outcomes."""
import argparse
from functools import lru_cache
from hashlib import sha256
from itertools import permutations, product
import json
from pathlib import Path

import numpy as np

import facilitator_channel_fit as fit
import facilitator_preflight_2699 as haiti

D, R = fit.D, fit.ROUTE
HERE = fit.HERE
EVIDENCE = HERE / "facilitator-conservative-archive-evidence"
NOTES = tuple(product(range(4), repeat=2))
PRESENT = R.SEND.copy()
PRESENT[1:, 0] = False
TABLES = np.asarray(list(product(*(np.flatnonzero(row) for row in PRESENT))))
MASKS = np.array([int(R.BITS[a] | R.BITS[b]) for a, b in NOTES])
ASK = D.CHAIR_LEGAL[MASKS]
SEED = 143024
HISTORIES = 32
PREFIXES = (0, 4, 16)


def banks():
    held = fit.OLD.base.cases()[1]
    points = fit.live.rubric()
    held["resolution_2593"] = points, points
    p = haiti.packet()["scoring"]
    points = fit.OLD.base.rubric(p["public"], (p["per_card"],) * 3, p["bridge_mask"], p["bridge"])
    held["resolution_2699"] = points, points
    return held


def styles():
    for ordering in permutations((1, 2, 3)):
        yield np.array([next((a for a in ordering if PRESENT[i, a]), 0) for i in range(8)])


PRIORITIES = tuple(styles())


def opening(left, right, prior):
    loss = D.LOSS
    x = (1 - loss) * left + loss * np.eye(4)[0]
    y = (1 - loss) * right + loss * np.eye(4)[0]
    p = np.einsum("lr,la,rb->ablr", prior, x, y).reshape(16, 8, 8)
    assert abs(p.sum() - 1.) < 1e-12
    return p


def utility(points):
    terminal = fit.OLD.base.terminal(points)
    extra = terminal[MASKS[:, None] | R.BITS] - terminal[MASKS, None]
    value = terminal[MASKS, None, None] + ((1 - D.LOSS) ** 2 * extra[:, None, :] -
                                         (1 - D.LOSS) * D.SEND_COST) * PRESENT[None, :, :]
    return value - D.QUERY_COST


def total_return(mass, values):
    return np.einsum("slr,srq->sq", mass, values)


def choices(mass, values):
    return np.where(ASK, total_return(mass, values), -np.inf).argmax(-1)


class Conservative:

    def __init__(self, prior, values, baseline):
        self.prior, self.values, self.baseline = prior, values, baseline
        self.types = np.array([1 << i for i in range(8)], dtype=np.uint16)
        self.support = {(topic, k): int((table == topic) @ self.types)
                        for topic, k in product(range(1, 4), range(len(TABLES)))
                        for table in (TABLES[k],)}

    def fit(self, history):
        observed = [[NOTES[s][side] for s in history if NOTES[s][side]] for side in range(2)]
        return tuple(tuple(k for k in range(len(TABLES)) if all(self.support[t, k] for t in reports))
                     for reports in observed)

    @lru_cache(maxsize=30000)
    def decide(self, receipt, candidates):
        fallback = int(self.baseline[receipt])
        possibilities = []
        for side, topic in enumerate(NOTES[receipt]):
            masks = {self.support[topic, k] for k in candidates[side]} - {0} if topic else {255}
            if not masks:
                return fallback, 0.
            possibilities.append([(m & self.types) != 0 for m in masks])
        distributions = np.asarray([self.prior * a[:, None] * b for a, b in product(*possibilities)])
        collapsed = distributions.sum(1)
        collapsed /= collapsed.sum(-1, keepdims=True)
        delta = self.values[receipt] - self.values[receipt, :, fallback, None]
        least = np.where(ASK[receipt], (collapsed @ delta).min(0), -np.inf)
        q = int(least.argmax())
        return (q, float(least[q])) if least[q] > 1e-12 else (fallback, 0.)


def measure(mass, request, assessed, opening_fee):
    if request.ndim == 1:
        request = request[None]
    state = np.arange(16)
    p = mass.sum((1, 2))
    actual = total_return(mass, utility(assessed))
    net = actual[state, request].sum(-1) - opening_fee
    target = R.BITS[request]
    available = (target[..., None] & np.arange(8)) != 0
    reply_ok = (1 - D.LOSS) ** 2 * available
    end = MASKS | target
    marginal = mass.sum(1)
    gain = (marginal * reply_ok).sum(-1)
    points = (p * assessed[MASKS] + gain * (assessed[end] - assessed[MASKS])).sum(-1)
    complete = (p * (assessed[MASKS] == 70) +
                gain * ((assessed[end] == 70).astype(float) - (assessed[MASKS] == 70))).sum(-1)
    return {"net": float(net.mean()), "history_net": net, "guarded_points": float(points.mean()),
            "complete_probability": float(complete.mean()), "requests": float(((request != 0) * p).sum(-1).mean())}


def independent(mass, assessed, opening_fee):
    benefit = D.LAST[MASKS] @ fit.OLD.base.terminal(assessed) - D.SEND_COST
    state_local = mass.sum(1)
    expected = state_local.T @ benefit
    # The responder invests its third send without receipt or query information.
    return float(np.where(R.SEND, expected, -np.inf).max(-1).sum() - opening_fee)


def comparison(prior, left, right, public, assessed, draws):
    mass = opening(D.one_hot(left), D.one_hot(right), prior)
    nominal = PRESENT / PRESENT.sum(-1, keepdims=True)
    unsure = opening(nominal, nominal, prior)
    prevalence = mass.sum((1, 2))
    visits = np.searchsorted(np.cumsum(prevalence), draws, side="right")
    assert np.all(prevalence[visits] > 0)
    fee = float(prior.sum(1) @ D.SEND_COST[left] + prior.sum(0) @ D.SEND_COST[right])
    best = measure(mass, choices(mass, utility(assessed)), assessed, fee)
    best.pop("history_net")
    result = {"known_partner": best, "best_independent_net": independent(mass, assessed, fee)}
    for phase, points in (("declared", public), ("review_calibrated", assessed)):
        values = utility(points)
        q = choices(unsure, values)
        baseline = measure(mass, q, assessed, fee)
        baseline.pop("history_net")
        model = Conservative(prior, values, q)
        row = {"baseline": baseline, "prefixes": {}}
        for n in PREFIXES:
            choices_by_history, lower_gains = [], []
            for history in visits[:, :n]:
                compatible = model.fit(history)
                act, bound = zip(*(model.decide(s, compatible) for s in range(16)), strict=True)
                choices_by_history.append(act)
                lower_gains.append(prevalence @ bound)
            score = measure(mass, np.asarray(choices_by_history), assessed, fee)
            gain = score.pop("history_net") - baseline["net"]
            if np.array_equal(points, assessed):
                assert np.all(gain >= lower_gains - np.full(len(gain), 1e-12))
            assert score["net"] <= best["net"] + 1e-12
            row["prefixes"][str(n)] = {**score, "mean_lower_bound": float(np.mean(lower_gains)),
                                       "negative_histories": int((gain < -1e-12).sum())}
        model.decide.cache_clear()
        result[phase] = row
    return result


def run():
    rng = np.random.default_rng(SEED)
    out = {}
    for docket, (public, scored) in banks().items():
        out[docket] = {"declared_points": public.tolist(), "reviewed_points": scored.tolist(), "prior": {}}
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            for name, (left, right) in {"same_priority": (PRIORITIES[0], PRIORITIES[0]),
                                       "opposite_priority": (PRIORITIES[0], PRIORITIES[-1])}.items():
                cell = out[docket]["prior"].setdefault(label, {})
                cell[name] = comparison(prior, left, right, public, scored, rng.random((HISTORIES, PREFIXES[-1])))
    files = (Path(__file__), EVIDENCE / "protocol.md", Path(fit.__file__), Path(D.__file__), haiti.PACKET)
    return {"seed": SEED, "histories": HISTORIES, "candidate_local_tables": len(TABLES), "dockets": out,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.parse_args()
    print(json.dumps(run(), indent=2))
