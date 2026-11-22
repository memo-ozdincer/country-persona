"""Choose documentary requests from likelihood-based partner confidence sets."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_conservative_archive as base

D, R = base.D, base.R
SEED = 143025
PREFIXES = (0, 16, 64)
ALPHA = .05
HYPOTHESES = tuple(product(range(len(base.TABLES)), repeat=2))


def nominal_model(prior):
    local = base.PRESENT / base.PRESENT.sum(-1, keepdims=True)
    return base.opening(local, local, prior)


def distribution(prior):
    """Joint opening-state and right-inventory law for every local table pair."""
    observations = ((1 - D.LOSS) * D.one_hot(base.TABLES) +
                    D.LOSS * np.eye(4)[0])
    data = np.einsum("lr,ila,jrb->ijabr", prior, observations, observations)
    data = data.reshape(len(HYPOTHESES), 16, 8)
    assert np.allclose(data.sum((1, 2)), 1., rtol=0, atol=1e-12)
    return data


def fallback(mass, points):
    pay = D.LAST[base.MASKS] @ base.fit.OLD.base.terminal(points) - D.SEND_COST
    val = mass.sum(1).T @ pay
    return np.where(R.SEND, val, -np.inf).argmax(-1)


def returns(points, quiet):
    """Expected material, strict flag and tail value on each receipt and right card."""
    # If a query is lost or asks for an unavailable card, the independent
    # send still takes place. This gives all requesters the same third slot.
    respond = np.where(R.SEND & (R.ACTIONS != 0), R.ACTIONS, quiet[:, None])
    channel = (1 - D.LOSS) * D.one_hot(respond) + D.LOSS * D.one_hot(quiet)[:, None, :]
    points_by_send = D.LAST[base.MASKS] @ points
    strict_by_send = D.LAST[base.MASKS] @ (points == 70)
    tail = points_by_send + D.COMPLETE_BONUS * strict_by_send - D.SEND_COST
    return (np.einsum("rqc,sc->srq", channel, points_by_send),
            np.einsum("rqc,sc->srq", channel, strict_by_send),
            np.einsum("rqc,sc->srq", channel, tail) - D.QUERY_COST)


def best_for(mass, payoff):
    return np.where(base.ASK, np.einsum("sr,srq->sq", mass, payoff), -np.inf).argmax(-1)


def score(mass, values, q, opening_fee):
    q = np.atleast_2d(q)
    states = np.arange(16)
    assert base.ASK[states, q].all()
    points, strict, value = [np.einsum("sr,srq->sq", mass, x)[states, q].sum(1) for x in values]
    asks = np.sum(mass.sum(1) * (q != 0), axis=-1)
    return {"net": float(value.mean() - opening_fee), "guarded_points": float(points.mean()),
            "complete_probability": float(strict.mean()), "expected_requests": float(asks.mean())}, value - opening_fee


def infer(likelihood, histories):
    log = np.log(likelihood[:, histories]).sum(-1).T
    peak = log.max(1, keepdims=True)
    centered = np.exp(log - peak)
    mixture = peak + np.log(centered.mean(1, keepdims=True))
    retained = log >= mixture + np.log(ALPHA)
    posterior = centered / centered.sum(1, keepdims=True)
    assert retained.any(1).all() and np.allclose(posterior.sum(1), 1.)
    return retained, posterior


def evaluate(actual, model, nominal, planned, assessed, histories, draws, true_index, fee):
    independent = fallback(actual[:, None, :], assessed)
    strong_independent = score(actual, returns(assessed, independent), np.zeros(16, dtype=int), fee)[0]
    quiet = fallback(nominal, planned)
    u = returns(assessed, quiet)
    goal = returns(planned, quiet)[-1]
    arm = best_for(nominal.sum(1), goal)
    benchmark = score(actual, u, arm, fee)[0]
    exact = score(actual, u, best_for(actual, u[-1]), fee)[0]
    no_request = score(actual, u, np.zeros(16, dtype=int), fee)[0]
    occurrence = model.sum(2)
    weighted_payoff = np.einsum("hsr,srq->hsq", model, goal)
    cond = np.divide(weighted_payoff, occurrence[..., None], out=np.zeros_like(weighted_payoff),
                     where=occurrence[..., None] > 0.)
    backup = cond[:, np.arange(16), arm]
    diff = np.where(occurrence[..., None] > 0., cond - backup[..., None], np.inf)
    collect = np.searchsorted(np.cumsum(histories), draws, side="right")
    assert (histories[collect] > 0.).all()
    outputs = {}
    for n in PREFIXES:
        support, posterior = infer(occurrence, collect[:, :n])
        safety = np.min(np.where(support[:, :, None, None], diff[None], np.inf), axis=1)
        safety = np.where(base.ASK, safety, -np.inf)
        candidate = safety.argmax(-1)
        min_gain = np.take_along_axis(safety, candidate[..., None], axis=-1).squeeze(-1)
        admissible = np.isfinite(min_gain) & (min_gain > 1e-12)
        robust = np.where(admissible, candidate, arm)
        bayes_values = np.einsum("rh,hsq->rsq", posterior, weighted_payoff)
        bayesian = np.where(base.ASK, bayes_values, -np.inf).argmax(-1)
        report, history = score(actual, u, robust, fee)
        predicted_low = np.where(admissible, min_gain, 0.) @ histories
        if np.array_equal(planned, assessed):
            assert np.all(history[support[:, true_index]] >= benchmark["net"] + predicted_low[support[:, true_index]] - 1e-12)
        outputs[str(n)] = {"conservative": report, "posterior_mean": score(actual, u, bayesian, fee)[0],
                           "mean_retained_tables": float(support.sum(1).mean()),
                           "true_table_exclusions": int((~support[:, true_index]).sum()),
                           "negative_histories": int((history < benchmark["net"] - 1e-12).sum())}
        assert report["net"] <= exact["net"] + 1e-12
    return {"baseline": benchmark, "no_request": no_request, "true_partner_same_fallback": exact,
            "true_partner_optimized_independent": strong_independent, "prefixes": outputs}


def run():
    rng = np.random.default_rng(SEED)
    result = {}
    styles = {"same_priority": (base.PRIORITIES[0], base.PRIORITIES[0]),
              "opposite_priority": (base.PRIORITIES[0], base.PRIORITIES[-1])}
    for docket, (public, assessed) in base.banks().items():
        result[docket] = {"declared": public.tolist(), "reviewed": assessed.tolist(), "conditions": {}}
        for key in base.fit.live.PRIORS:
            prior = R.TEST_PRIORS[key]
            model = distribution(prior)
            nominal = nominal_model(prior)
            for name, (left, right) in styles.items():
                l, r = [int(np.flatnonzero((base.TABLES == x).all(1))[0]) for x in (left, right)]
                true = HYPOTHESES.index((l, r))
                actual = model[true]
                f = actual.sum(1)
                fee = float(prior.sum(1) @ D.SEND_COST[left] + prior.sum(0) @ D.SEND_COST[right])
                draws = rng.random((base.HISTORIES, PREFIXES[-1]))
                result[docket]["conditions"][f"{key}/{name}"] = {
                    title: evaluate(actual, model, nominal, points, assessed, f, draws, true, fee)
                    for title, points in (("declared", public), ("review_calibrated", assessed))}
    paths = (Path(__file__), Path(base.__file__), base.EVIDENCE / "frequency-protocol.md")
    return {"alpha": ALPHA, "prefixes": PREFIXES, "histories": base.HISTORIES, "dockets": result,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
