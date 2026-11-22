"""Fit documentary request and reply policies against evidence admission uncertainty."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np
import torch

import facilitator_prospective_2593 as live
from facilitator_live_delivery import ACTION_FIT

OLD = live.TRAINED
D = live.D
ROUTE = live.ROUTE
HERE = live.HERE
EVIDENCE = HERE / "facilitator-channel-fit-evidence"
PERFECT = np.ones((4, 4))
ERASURE = np.eye(4)[0]
MAPS = np.asarray(list(product(*(np.flatnonzero(row) for row in D.CHAIR_LEGAL))))


def channel(match, fallback, silence):
    table = np.full((4, 4), fallback)
    np.fill_diagonal(table, match)
    table[0, :] = silence
    table[:, 0] = 1.
    return table


DESIGN = channel(.80, .25, .95)
REGIMES = (PERFECT, channel(.95, .50, .95), channel(.70, .10, .95), channel(.35, .10, .83))
STRESS = {"clean": PERFECT, "fallback_loss": channel(.85, .05, 1.),
          "topic_asymmetry": channel(.60, .16, .90)}
STRESS["topic_asymmetry"][1, 1] = .96
STRESS["topic_asymmetry"][2, 2] = .32


def context(points, prior):
    left, right, opening, _ = OLD.base.context(points, prior)
    return (left, right), opening


def value(points, admission):
    # Physical request t and eventual card c. Channel loss can turn a
    # sent card into the unchanged receipt mask even when its cost is paid.
    terminal = OLD.base.terminal(points)
    material = D.LAST @ terminal
    return terminal[:, None, None] + (material - terminal[:, None])[:, None, :] * admission - D.SEND_COST


def features(points, opening, estimate):
    payoff = value(points, estimate)
    delta = (payoff - payoff[:, :, :1]) / 10.
    script = D.one_hot(D.scripts()[3])
    if_speaks = np.einsum("rbm,rbqc,mqc->mq", opening, script, delta)
    if_silent = np.einsum("rbm,rbc,mc->m", opening, script[:, :, 0], delta[:, 0])
    expected = (1 - D.LOSS) * if_speaks + D.LOSS * if_silent[:, None]
    mass = np.maximum(opening.sum((0, 1)), 1e-12)
    can_answer = np.einsum("rbm,rq->mq", opening, ROUTE.SEND) / mass[:, None]
    asks = (ROUTE.ACTIONS != 0)[None, :]
    chair = np.stack(((expected - expected[:, :1]) / mass[:, None],
                      can_answer * asks, np.broadcast_to(asks, (8, 4))), axis=-1)

    allowed = D.CHAIR_LEGAL.copy()
    assert allowed[:, 0].all()
    posterior = opening[:, :, :, None] * allowed
    denom = np.maximum(posterior.sum(2), 1e-12)
    reply_value = np.einsum("rbmq,mqc->rbqc", posterior, delta) / denom[..., None]
    r, b, q, c = np.ix_(np.arange(8), ROUTE.ACTIONS, ROUTE.ACTIONS, ROUTE.ACTIONS)
    flags = ((q == c) & (q != 0), (b == c) & (c != 0), c != 0)
    answer = np.stack((reply_value, *(np.broadcast_to(f, reply_value.shape) for f in flags)), axis=-1)
    return chair, answer


def heard(requests):
    return (1 - D.LOSS) * requests + D.LOSS * ERASURE


def train(banks, robust):
    torch.set_num_threads(1)
    cases = []
    contexts = OLD.paired.training_contexts(banks)
    for public, target in banks.values():
        opening = contexts[tuple(public)][2]
        for actual in REGIMES if robust else (PERFECT,):
            estimate = PERFECT if actual is PERFECT else DESIGN
            cases.append((*features(public, opening, estimate), opening, value(target, actual), target[0]))
    chair, answer, opening, payoff, base = (
        torch.as_tensor(np.stack(col), dtype=torch.float64) for col in zip(*cases, strict=True))
    q, r = (torch.nn.Parameter(torch.tensor(x, dtype=torch.float64)) for x in OLD.INITIAL)
    opt = torch.optim.Adam((q, r), lr=.04)
    ask_legal, answer_legal = map(torch.as_tensor, (D.CHAIR_LEGAL, D.FINAL_LEGAL))
    fees = torch.as_tensor(D.QUERY_COST)
    silence = torch.as_tensor(ERASURE)
    trace = []
    for _ in range(OLD.UPDATES):
        ask = (chair @ q).masked_fill(~ask_legal, -torch.inf).softmax(-1)
        response = (answer @ r).masked_fill(~answer_legal, -torch.inf).softmax(-1)
        actual = (1 - D.LOSS) * ask + D.LOSS * silence
        end = torch.einsum("nrbm,nmt,nrbtc->nmtc", opening, actual, response)
        scores = torch.einsum("nmtc,nmtc->n", end, payoff) - ((ask @ fees) * opening.sum((1, 2))).sum(-1)
        objective = (scores - base).mean()
        opt.zero_grad()
        (-objective).backward()
        assert all(torch.isfinite(p.grad).all() for p in (q, r))
        opt.step()
        trace.append(float(objective.detach()))
    return (q.detach().numpy(), r.detach().numpy()), trace


def action_policy(parameters, public, opening, estimate):
    chair, answer = features(public, opening, estimate)
    q, a = parameters
    return (np.where(D.CHAIR_LEGAL, chair @ q, -np.inf).argmax(-1),
            np.where(D.FINAL_LEGAL, answer @ a, -np.inf).argmax(-1))


def exact(public, opening, admission, independent=False):
    maps = MAPS[:1] if independent else MAPS
    p = heard(D.one_hot(maps))
    conditional = np.einsum("rbm,pmt,mtc->prbtc", opening, p, value(public, admission))
    legal = np.where(D.FINAL_LEGAL[None], conditional, -np.inf)
    total = legal.max(-1).sum((1, 2, 3)) - D.QUERY_COST[maps] @ opening.sum((0, 1))
    best = int(total.argmax())
    return (maps[best], legal[best].argmax(-1))


def measure(tail, opener, opening, prior, points, admission, erase=False):
    q, reply = tail
    assert D.CHAIR_LEGAL[np.arange(8), q].all()
    assert np.take_along_axis(np.broadcast_to(D.FINAL_LEGAL, (8, 4, 4, 4)), reply[..., None], axis=-1).all()
    physical = heard(D.one_hot(q))
    if erase:
        end = np.einsum("rbm,mt,rbc->mtc", opening, physical, D.one_hot(reply[:, :, 0]))
    else:
        end = np.einsum("rbm,mt,rbtc->mtc", opening, physical, D.one_hot(reply))
    success = np.sum(end * admission, axis=1)
    rejected = np.sum(end * (1 - admission), axis=(1, 2))
    mass = np.einsum("mc,mcn->n", success, D.LAST) + rejected
    assert abs(mass.sum() - 1.) < 1e-12
    left, right = opener
    cost = (prior.sum(1) @ D.SEND_COST[left] + prior.sum(0) @ D.SEND_COST[right]
            + opening.sum((0, 1)) @ D.QUERY_COST[q] + end.sum((0, 1)) @ D.SEND_COST)
    return {"guarded_points": float(mass @ points), "strict_complete": float(mass[7] if points[7] == 70 else 0.),
            "cost": float(cost), "net": float(mass @ OLD.base.terminal(points) - cost),
            "reply_rejection_probability": float(rejected.sum()), "receipt_mass": mass.tolist()}


def measured_afghanistan():
    rows = json.loads((live.EVIDENCE / "results.json").read_text())
    table = np.zeros((4, 4))
    table[:, 0] = 1.
    assert rows["decoded"] == list(range(4))
    for key in rows["approved_reply_ids"]:
        _, q, c = key.split("/")
        table[int(q), int(c)] = 1.
    assert table[0].all()
    return table, rows


def trial(public, points, prior, actual, clean, robust, stress, check=None):
    opener, opening = context(public, prior)
    estimate = DESIGN if stress else PERFECT
    _, _, asks, replies = D.scripts()
    tails = {
        "channel_blind_initial": action_policy(OLD.INITIAL, public, opening, PERFECT),
        "clean_fit": action_policy(clean, public, opening, PERFECT),
        "channel_aware_initial": action_policy(OLD.INITIAL, public, opening, estimate),
        "robust_fit": action_policy(robust, public, opening, estimate),
        "public_independent": exact(public, opening, estimate, independent=True),
        "public_exact": exact(public, opening, estimate),
        "exact_actual_upper": exact(points, opening, actual),
        "script": (asks, replies),
    }
    scores = {name: measure(tail, opener, opening, prior, points, actual) for name, tail in tails.items()}
    scores["robust_erased_request"] = measure(tails["robust_fit"], opener, opening, prior, points, actual, erase=True)
    assert all(row["net"] <= scores["exact_actual_upper"]["net"] + 1e-9 for row in scores.values())
    if check is not None:
        archived = json.loads(ACTION_FIT.read_text())["learned"]
        tail = OLD.infer(archived, public, opener, opening)[2:]
        scores["archived_fit"] = measure(tail, opener, opening, prior, points, actual)
        assert np.allclose(scores["archived_fit"]["receipt_mass"], check["mass"], atol=1e-12, rtol=0)
        assert abs(scores["archived_fit"]["net"] - check["net"]) < 1e-12
    if not stress:
        for name, tail in tails.items():
            expected = D.measure((*opener, *tail), prior, points)
            assert abs(expected["net"] - scores[name]["net"]) < 1e-10
    return scores


def run():
    training, held = OLD.base.cases()
    afghanistan, recorded = measured_afghanistan()
    clean, clean_trace = train(training, robust=False)
    robust, robust_trace = train(training, robust=True)
    # Perfect-channel features and clean training must reproduce the archived fit.
    saved = json.loads(ACTION_FIT.read_text())["learned"]
    assert all(np.allclose(a, b, atol=1e-9, rtol=0.) for a, b in zip(clean, saved, strict=True))
    held["resolution_2593"] = (live.rubric(), live.rubric())
    trials = {}
    for family, (public, points) in held.items():
        trials[family] = {}
        real = family == "resolution_2593"
        for prior_id in live.PRIORS:
            prior = ROUTE.TEST_PRIORS[prior_id]
            cases = {"source_only": PERFECT, "question_visible": afghanistan} if real else STRESS
            trials[family][prior_id] = {}
            for name, actual in cases.items():
                stressed = actual is not PERFECT
                check = recorded["priors"][prior_id]["fitted"]["english" if stressed else "typed"] if real else None
                trials[family][prior_id][name] = trial(public, points, prior, actual, clean, robust, stressed, check)
    artifacts = (Path(__file__), EVIDENCE / "protocol.md", Path(OLD.__file__), Path(OLD.base.__file__),
                 Path(D.__file__), ACTION_FIT, live.EVIDENCE / "results.json", live.PACKET)
    return {"training_families": list(training), "updates_per_fit": OLD.UPDATES,
            "clean": [v.tolist() for v in clean], "robust": [v.tolist() for v in robust],
            "clean_trace": clean_trace, "robust_trace": robust_trace,
            "training_admission": [v.tolist() for v in REGIMES], "declared_noisy_admission": DESIGN.tolist(),
            "stress_admission": {k: v.tolist() for k, v in STRESS.items()}, "measured_admission": afghanistan.tolist(),
            "results": trials, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in artifacts}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
