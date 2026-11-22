"""Train and evaluate a requester against the exact matching no-request policy."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

import facilitator_conservative_archive as archive
import facilitator_validated_accounts as accounts
import facilitator_validated_accounts_swaps as swap

fit = swap.fit
D, R = fit.D, fit.ROUTE
HERE = fit.HERE
EVIDENCE = HERE / "facilitator-baseline-request-fit-evidence"
WEIGHTS = fit.EVIDENCE / "results.json"
UPDATES = 96
INITIAL = np.array([.5, .5, 0., 0.])


def returns(reply, opening, pay):
    heard = np.einsum("rbm,rbtc,mtc->mt", opening, D.one_hot(reply), pay)
    return heard @ fit.heard(np.eye(4)).T - opening.sum((0, 1))[:, None] * D.QUERY_COST


def problem(public, prior, robust):
    opener, opening = fit.context(public, prior)
    _, reply = fit.action_policy(robust, public, opening, fit.PERFECT)
    mass = opening.sum((0, 1))
    normalizer = np.maximum(mass, 1e-12)[:, None]
    predictions = [returns(reply, opening, fit.value(public, h)) for h in (fit.PERFECT, fit.DESIGN)]
    gain = [(a - a[:, :1]) / normalizer for a in predictions]
    has_card = np.einsum("rbm,rq->mq", opening, R.SEND) / normalizer
    has_card[:, 0] = 0
    request = np.broadcast_to(np.arange(4) != 0, has_card.shape)
    return opener, opening, reply, np.stack((*gain, has_card, request), axis=-1)


def train(banks, robust):
    torch.set_num_threads(1)
    features, gains = [], []
    for public, target in banks.values():
        for label in fit.live.PRIORS:
            _, opening, reply, x = problem(public, R.TEST_PRIORS[label], robust)
            for h in fit.REGIMES:
                actual = returns(reply, opening, fit.value(target, h))
                features.append(x)
                gains.append(actual - actual[:, :1])
    x, advantage = map(lambda v: torch.as_tensor(np.stack(v), dtype=torch.float64), (features, gains))
    allowed = torch.as_tensor(D.CHAIR_LEGAL)
    w = torch.nn.Parameter(torch.from_numpy(INITIAL.copy()))
    opt = torch.optim.Adam([w], lr=.04)
    trace = []
    for update in range(UPDATES + 1):
        policy = (x @ w).masked_fill(~allowed, -torch.inf).softmax(-1)
        delta = (policy * advantage).sum((1, 2))
        downside = (-delta).clamp_min(0).mean()
        objective = delta.mean() - downside
        trace.append({"update": update, "objective": float(objective.detach()),
                      "mean_gain": float(delta.mean().detach()), "mean_downside": float(downside.detach()),
                      "minimum_gain": float(delta.min().detach()), "weights": w.detach().tolist()})
        if update == UPDATES:
            break
        opt.zero_grad()
        (-objective).backward()
        assert torch.isfinite(w.grad).all()
        opt.step()
    return w.detach().numpy(), trace, len(features)


def select(logits):
    return np.where(D.CHAIR_LEGAL, logits, -np.inf).argmax(-1)


def evaluate(public, target, prior, robust, weights, channel):
    opener, opening, reply, x = problem(public, prior, robust)
    old, _ = fit.action_policy(robust, public, opening, fit.PERFECT)
    pay = fit.value(target, channel)
    quiet = np.zeros(8, dtype=int)
    requesters = {"no_request": quiet, "archived_robust": old, "learned": select(x @ weights),
                  "initial_average": select(x @ INITIAL), "analytic_clean": select(x[..., 0]),
                  "analytic_degraded": select(x[..., 1]), "analytic_conservative": select(x[..., :2].min(-1)),
                  "exact_same_responder": select(returns(reply, opening, pay))}
    assert np.array_equal(requesters["exact_same_responder"], swap.best_request(reply, opening, pay))
    policies = {k: (q, reply) for k, q in requesters.items()}
    policies["exact_joint"] = fit.exact(target, opening, channel)
    policies["exact_independent"] = fit.exact(target, opening, channel, independent=True)
    out = {}
    for name, tail in policies.items():
        row = fit.measure(tail, opener, opening, prior, target, channel)
        row["release_probability"] = float(np.array(row["receipt_mass"]) @ (target > 0))
        row["expected_requests"] = float(opening.sum((0, 1)) @ (tail[0] != 0))
        row["requests"] = tail[0].tolist()
        out[name] = row
        if name in requesters:
            assert abs(row["net"] - out["no_request"]["net"] -
                       (returns(reply, opening, pay)[np.arange(8), tail[0]] - returns(reply, opening, pay)[:, 0]).sum()) < 1e-10
    for name, row in out.items():
        row["gain_over_no_request"] = row["net"] - out["no_request"]["net"]
        assert row["net"] <= out["exact_joint"]["net"] + 1e-10
        if name in requesters:
            assert row["net"] <= out["exact_same_responder"]["net"] + 1e-10
    return out


def run():
    saved = json.loads(WEIGHTS.read_text())
    robust = saved["robust"]
    training = fit.OLD.base.cases()[0]
    assert list(training) == saved["training_families"]
    held = archive.banks()
    validated = accounts.EVIDENCE / "apostrophe.json"
    rewrite = accounts.fixed.EVIDENCE / "results.json"
    public = held["resolution_2699"][0]
    held["resolution_2699"] = public, np.array(json.loads(validated.read_text())["released_bank"])
    held["resolution_2699_rewrite"] = public, np.array(json.loads(rewrite.read_text())["released_bank"])
    assert set(training).isdisjoint(held)
    weights, trace, size = train(training, robust)
    result = {}
    for event, (public, target) in held.items():
        result[event] = {}
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            result[event][label] = {name: evaluate(public, target, prior, robust, weights, channel)
                                    for name, channel in fit.STRESS.items()}
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", WEIGHTS, validated, rewrite,
             Path(fit.__file__).resolve(), Path(archive.__file__).resolve(), Path(swap.__file__).resolve(),
             Path(fit.OLD.base.__file__).resolve())
    return {"training_banks": list(training), "training_conditions": size, "updates": UPDATES, "trace": trace,
            "initial": INITIAL.tolist(), "fitted": weights.tolist(), "evaluation": result,
            "sha256": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
