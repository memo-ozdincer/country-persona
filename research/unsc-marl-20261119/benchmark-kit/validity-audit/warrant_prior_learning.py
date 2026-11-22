"""Learn a public inventory model from partial, authorized grade receipts."""
import argparse
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path

import numpy as np

import trained_warrant as fit
import warrant_generalization as domains

EVIDENCE = fit.HERE / "warrant-prior-evidence"
SAMPLES = (9, 27, 81)
SEED = 9410
UNIFORM = np.full(16, 1. / 16)
COUPLINGS = np.array([np.eye(4)[list(order)].ravel() / 4. for order in permutations(range(4))])
HYPOTHESES = np.vstack((UNIFORM, .4 * UNIFORM + .6 * COUPLINGS))


def episodes(cards, true, rng):
    # Every block contains each public slot pair once. Packet delivery never
    # depends on a private value or on the learner's next decision.
    slots = np.array(list(np.ndindex(3, 3)))
    pairs = np.vstack([slots[rng.permutation(9)] for _ in range(SAMPLES[-1] // 9)])
    actual = rng.choice(16, SAMPLES[-1], p=true)
    survives = rng.random((SAMPLES[-1], 2)) >= fit.LOSS
    compatible = np.ones((SAMPLES[-1], 16), dtype=bool)
    observed = []
    for step, (selected, pair, delivered) in enumerate(zip(actual, pairs, survives, strict=True)):
        row = []
        for side, (slot, seen) in enumerate(zip(pair, delivered, strict=True)):
            if seen:
                values = cards[:, side, slot]
                observed_value = int(values[selected])
                compatible[step] &= values == observed_value
                row.append([side, int(slot), observed_value])
        observed.append(row)
        assert compatible[step, selected]
    return compatible, observed


def estimate(compatible):
    # The constrained learner integrates, instead of selecting, matching
    # hypotheses. Give the independence hypothesis half the initial mass.
    start = np.full(len(HYPOTHESES), .5 / len(COUPLINGS))
    start[0] = .5
    mass = compatible @ HYPOTHESES.T
    assert np.all(mass > 0.)
    log_weight = np.log(start) + np.log(mass).sum(0)
    posterior = np.exp(log_weight - log_weight.max())
    posterior /= posterior.sum()
    prediction = posterior @ HYPOTHESES

    # Two symmetric pseudocounts prevent a partial sample from assigning zero
    # probability to a public possibility.
    joint = UNIFORM.copy()
    for _ in range(80):
        prob = compatible * joint
        expected = prob / prob.sum(1, keepdims=True)
        joint = (expected.sum(0) + 2 * UNIFORM) / (len(compatible) + 2)
    return {"matching_posterior": prediction, "unstructured_em": joint}


def opener(env, grades, weights):
    public = np.asarray(fit.features(grades, env))
    return np.eye(3)[(public * weights[:, None, None]).sum(-1).argmax(-1)]


def choose(estimated_env, opening):
    weighted = fit.combinations(*opening, estimated_env[4])
    return fit.value(estimated_env[0], estimated_env[3], weighted)[0].argmax(1)


def evaluate(actual_env, opening, request):
    pay, rec, imp, legal, actual, _ = actual_env
    assert legal[np.arange(len(request)), request].all()
    weighted = fit.combinations(*opening, actual)
    ix = np.arange(len(request))
    net, recommend, impasse = [float((weighted @ table[:, ix, request])[0].sum()) for table in (pay, rec, imp)]
    fee = recommend + impasse - net
    return {"net": net, "recommend": recommend, "impasse": impasse, "unresolved": 1 - recommend - impasse,
            "expected_requests": fee / fit.REPLY_COST}


def reweight(env, prior):
    # Public domain, receipt labels and warrants are unchanged by an estimate.
    prior = np.asarray(prior)
    assert np.isclose(prior.sum(), 1.) and np.all(prior > 0.)
    return (*env[:4], prior.reshape(4, 4), env[-1])


def trial(grades, weights, p, rng):
    cards = np.array(list(np.ndindex(4, 4)))
    cards = np.stack([np.asarray(grades[side])[cards[:, side]] for side in range(2)], axis=1)
    compatible, receipts = episodes(cards, p, rng)
    raw = fit.environment(grades, UNIFORM.reshape(4, 4))
    actual = reweight(raw, p)
    initial_open = opener(raw, grades, weights)
    initial = evaluate(actual, initial_open, choose(raw, initial_open))
    real_open = opener(actual, grades, weights)
    oracle_req = evaluate(actual, initial_open, choose(actual, initial_open))
    rows = {"uniform": initial, "true_prior": evaluate(actual, real_open, choose(actual, real_open)),
            "true_request_fixed_opening": oracle_req}
    for n in SAMPLES:
        rows[str(n)] = {}
        for name, q in estimate(compatible[:n]).items():
            observed = reweight(raw, q)
            opened = opener(observed, grades, weights)
            model = evaluate(actual, opened, choose(observed, opened))
            closed = evaluate(actual, initial_open, choose(observed, initial_open))
            assert closed["net"] <= oracle_req["net"] + 1e-12
            rows[str(n)][name] = {"end_to_end": model, "fixed_opening": closed,
                                  "tv_to_actual": float(np.abs(p - q).sum() / 2),
                                  "estimated_prior": q.reshape(4, 4).tolist()}
    return {"true_prior": p.reshape(4, 4).tolist(), "calibration_receipts": receipts, "scores": rows}


def run(path):
    weights = np.asarray(json.loads(path.read_text())["fit"])
    rng = np.random.default_rng(SEED)
    results = []
    for i, grades in domains.generate():
        first, second = rng.choice(len(COUPLINGS), size=2, replace=False)
        real = {"independent": UNIFORM, "matching": .35 * UNIFORM + .65 * COUPLINGS[first],
                "mixed_matching": .35 * UNIFORM + .65 * (.7 * COUPLINGS[first] + .3 * COUPLINGS[second])}
        results.append({"domain": i, "grades": grades,
                        "modes": {name: trial(grades, weights, p, rng) for name, p in real.items()}})
    paths = (Path(__file__), EVIDENCE / "protocol.md", path, Path(fit.__file__), Path(domains.__file__))
    return {"seed": SEED, "sample_schedule": SAMPLES, "domains": results,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit", type=Path)
    print(json.dumps(run(cli.parse_args().fit), indent=2))
