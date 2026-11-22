"""Learn shared action weights from public values under the third-delivery protocol."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

import facilitator_third_delivery_paired as paired

base = paired.base
delivery = base.delivery
route = base.route
HERE = Path(__file__).resolve().parent
UPDATES = 240
INITIAL = ((1., 0., 0.), (1., 1., 0., 0.))


def features(points, opening):
    # The chair can condition on its receipts and the public opening model.
    # The responder conditions on its intended send and heard request. A
    # hypothetical request narrows its receipt distribution to missing q.
    value = delivery.LAST @ base.terminal(points) - delivery.SEND_COST
    delta = (value - value[:, :1]) / 10.
    fallback = delivery.scripts()[3]
    receive = (1 - delivery.LOSS) * delivery.one_hot(fallback) + delivery.LOSS * delivery.one_hot(fallback[:, :, :1])
    reply_value = np.einsum("rbm,rbqc,mc->mq", opening, receive, delta)
    mass = np.maximum(opening.sum((0, 1)), 1e-12)
    can_answer = np.einsum("rbm,rq->mq", opening, route.SEND) / mass[:, None]
    request_cost = (route.ACTIONS != 0)[None, :]
    chair = np.stack(((reply_value - reply_value[:, :1]) / mass[:, None],
                      can_answer * request_cost, np.broadcast_to(request_cost, (8, 4))), axis=-1)

    admitted = np.ones((8, 4), dtype=bool)
    admitted[:, 1:] = delivery.CHAIR_LEGAL[:, 1:]
    posterior = opening[:, :, :, None] * admitted
    denom = np.maximum(posterior.sum(axis=2), 1e-12)
    expected = np.einsum("rbmq,mc->rbqc", posterior, delta) / denom[..., None]
    r, b, q, c = np.ix_(np.arange(8), route.ACTIONS, route.ACTIONS, route.ACTIONS)
    obey = np.broadcast_to((q == c) & (q != 0), expected.shape)
    repeat = np.broadcast_to((b == c) & (c != 0), expected.shape)
    send = np.broadcast_to(c != 0, expected.shape)
    reply = np.stack((expected, obey, repeat, send), axis=-1)
    return chair, reply


def infer(parameters, points, opener, opening):
    chair, reply = features(points, opening)
    q, r = (np.asarray(p) for p in parameters)
    requested = np.where(delivery.CHAIR_LEGAL, chair @ q, -np.inf).argmax(-1)
    sent = np.where(delivery.FINAL_LEGAL, reply @ r, -np.inf).argmax(-1)
    return *opener, requested, sent


def train(training, contexts):
    torch.set_num_threads(1)
    items = [(*features(public, contexts[tuple(public)][2]), contexts[tuple(public)][2], base.terminal(actual))
             for public, actual in training.values()]
    chair, reply, opening, terminal = (torch.as_tensor(np.stack(x), dtype=torch.float64) for x in zip(*items, strict=True))
    payoff = torch.einsum("mcn,pn->pmc", torch.as_tensor(delivery.LAST), terminal)
    payoff -= torch.as_tensor(delivery.SEND_COST)
    q, r = (torch.nn.Parameter(torch.as_tensor(x, dtype=torch.float64)) for x in INITIAL)
    optimizer = torch.optim.Adam((q, r), lr=.04)
    legal = torch.as_tensor(delivery.CHAIR_LEGAL)
    reply_legal = torch.as_tensor(delivery.FINAL_LEGAL)
    fees = torch.as_tensor(delivery.QUERY_COST)
    silence = torch.eye(4, dtype=torch.float64)[0]
    trace = []
    for _ in range(UPDATES):
        ask = (chair @ q).masked_fill(~legal, -torch.inf).softmax(-1)
        answer = (reply @ r).masked_fill(~reply_legal, -torch.inf).softmax(-1)
        heard = (1 - delivery.LOSS) * ask + delivery.LOSS * silence
        ends = torch.einsum("prbm,pmq,prbqc->pmc", opening, heard, answer)
        total = torch.einsum("pmc,pmc->p", ends, payoff) - (opening.sum((1, 2)) * (ask @ fees)).sum(-1)
        optimizer.zero_grad()
        objective = total.mean()
        (-objective).backward()
        assert torch.isfinite(objective) and torch.isfinite(q.grad).all() and torch.isfinite(r.grad).all()
        trace.append(float(objective.detach()))
        optimizer.step()
    return (q.detach().numpy(), r.detach().numpy()), trace


def score(parameters, public, actual, prior, anchored=None):
    left, right, opening, _ = base.context(public if anchored is None else anchored, prior)
    trained = infer(parameters, public, (left, right), opening)
    original = infer(INITIAL, public, (left, right), opening)
    # Keep each agent's local observations and the exact opening. Erase only
    # its public receipt weights from the features used to pick actions.
    fixed = infer(parameters, base.rubric(34, (12, 12, 12)), (left, right), opening)
    optimum, _ = base.diagnose.exact_tail(left, right, prior, base.terminal(public))
    _, _, chair, reply = delivery.scripts()
    plans = {"trained": trained, "initial_action_rule": original, "constant_values": fixed,
             "script": (left, right, chair, reply), "exact_public": optimum}
    if anchored is None:
        plans["public_independent"] = delivery.exact_independent(prior, base.terminal(public))
    for p in plans.values():
        base.diagnose.audit(p, prior)
    scores = {name: delivery.measure(p, prior, actual) for name, p in plans.items()}
    scores["trained_erased"] = delivery.measure(trained, prior, actual, erase=True)
    return scores, trained[2:]


def run():
    training, held = base.cases()
    contexts = paired.training_contexts(training)
    learned, trace = train(training, contexts)
    contrasts = []
    prior = route.TEST_PRIORS["uniform"]
    anchor = base.rubric(34, (7, 7, 7))
    for pair in (3, 6):
        rubric = base.rubric(34, (7, 7, 7), pair, 15)
        values, actions = score(learned, rubric, rubric, prior, anchored=anchor)
        contrasts.append({"pair": pair, "arms": values, "tail": [a.tolist() for a in actions]})
    transfer = {name: {condition: score(learned, public, observed, route.TEST_PRIORS[condition])[0]
                       for condition in ("uniform", "correlated_duplicates")}
                for name, (public, observed) in held.items()}
    return {
        "scope": "Per-action public value estimates use only an assumed reply rule and permitted local information. "
                 "A new exact team-reward fit learns a shared weight vector for each agent. Evaluate unchanged openings "
                 "and compare with the input-value rule before training.",
        "initial": INITIAL, "learned": [x.tolist() for x in learned], "trace": trace,
        "contrast": contrasts, "contrast_changes_actions": contrasts[0]["tail"] != contrasts[1]["tail"],
        "transfer": transfer,
        "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (
            Path(__file__), Path(paired.__file__), Path(base.__file__))},
    }


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2, ensure_ascii=False))
