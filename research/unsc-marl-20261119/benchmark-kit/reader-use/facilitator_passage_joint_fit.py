"""Fit decentralized opening and follow-up maps on the same documentary objective."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np
import torch

import facilitator_measured_channel_fit as historic
import facilitator_passage_routing_replay as passage

fit = historic.fit
D, R = fit.D, fit.ROUTE
HERE = fit.HERE
EVIDENCE = HERE / "facilitator-passage-joint-fit-evidence"
UPDATES, BLOCKS = 96, 12
MAPS = np.asarray(list(product(*(np.flatnonzero(row) for row in R.SEND))))
OPEN_INITIAL = (6., 0., 0., 0.)


def opening(left, right, prior):
    return np.einsum("lr,la,rb,abm->rbm", prior, D.one_hot(left), D.one_hot(right), D.FIRST)


def open_features(points, prior, reference):
    left, right = reference
    terminal = fit.OLD.base.terminal(points)
    simple = D.FIRST @ terminal
    tail = D.LAST @ terminal - D.SEND_COST
    upper = np.where(R.SEND[:, None, :], tail[None, :, :], -np.inf).max(-1)
    coordinated = np.einsum("abm,rm->rab", D.FIRST, upper)
    available = np.broadcast_to(np.arange(4) != 0, (8, 4))

    first_single = prior @ simple[:, right].T
    right_single = prior.T @ simple[left]
    first_joint = np.einsum("lr,ra->la", prior, coordinated[np.arange(8), :, right])
    right_joint = np.einsum("lr,rlb->rb", prior, coordinated[:, left, :])
    features = []
    for old, single, joint, marg in ((left, first_single, first_joint, prior.sum(1)),
                                    (right, right_single, right_joint, prior.sum(0))):
        scale = np.maximum(marg, 1e-12)[:, None] * 10
        features.append(np.stack((D.one_hot(old), (single - single[:, :1]) / scale,
                                  (joint - joint[:, :1]) / scale, available), axis=-1))
    return features


def inputs(public, prior):
    reference, mass = fit.context(public, prior)
    asks, replies = fit.features(public, mass, fit.PERFECT)
    return (*open_features(public, prior, reference), asks, replies), reference


def train(banks, learn_opening):
    torch.set_num_threads(1)
    batches = []
    for public, target in banks.values():
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            feats, ref = inputs(public, prior)
            batches.append((*feats, prior, fit.value(target, fit.PERFECT), *(D.one_hot(a) for a in ref)))
    a, b, q, r, prior, reward, pre_a, pre_b = (
        torch.as_tensor(np.stack(items), dtype=torch.float64) for items in zip(*batches, strict=True))
    parameters = [torch.nn.Parameter(torch.tensor(p, dtype=torch.float64), requires_grad=learn_opening or i >= 2)
                  for i, p in enumerate((OPEN_INITIAL, OPEN_INITIAL, *fit.OLD.INITIAL))]
    opt = torch.optim.Adam([p for p in parameters if p.requires_grad], lr=.04)
    masks = [torch.as_tensor(x) for x in (R.SEND, R.SEND, D.CHAIR_LEGAL, D.FINAL_LEGAL)]
    fee, q_fee, transition, silence = map(torch.as_tensor, (D.SEND_COST, D.QUERY_COST, D.FIRST, fit.ERASURE))
    trace = []

    for step in range(UPDATES + 1):
        l, rr, ask, response = [(x @ w).masked_fill(~mask, -torch.inf).softmax(-1)
                                for x, w, mask in zip((a, b, q, r), parameters, masks, strict=True)]
        if not learn_opening:
            l, rr = pre_a, pre_b
        first = torch.einsum("nlr,nla,nrb,abm->nrbm", prior, l, rr, transition)
        heard = (1 - D.LOSS) * ask + D.LOSS * silence
        mass = torch.einsum("nrbm,nmt,nrbtc->nmtc", first, heard, response)
        payment = ((prior.sum(2) * (l @ fee)).sum(1) + (prior.sum(1) * (rr @ fee)).sum(1)
                   + ((ask @ q_fee) * first.sum((1, 2))).sum(1))
        objective = ((mass * reward).sum((1, 2, 3)) - payment).mean()
        trace.append({"step": step, "net": float(objective.detach()),
                      "request_rate": float(((1 - ask[..., 0]) * first.sum((1, 2))).sum(1).mean().detach())})
        if step == UPDATES:
            break
        opt.zero_grad()
        (-objective).backward()
        trace[-1]["gradient_norms"] = [float(p.grad.norm()) if p.requires_grad else 0. for p in parameters]
        assert all(torch.isfinite(p.grad).all() for p in parameters if p.requires_grad)
        opt.step()
    return {"weights": [w.detach().tolist() for w in parameters], "trace": trace, "opening_learned": learn_opening}


def policies(public, prior, fit_product):
    features, reference = inputs(public, prior)
    matrices = [np.where(mask, x @ np.asarray(w), -np.inf) for x, w, mask in
                zip(features, fit_product["weights"], (R.SEND, R.SEND, D.CHAIR_LEGAL, D.FINAL_LEGAL), strict=True)]
    distributions = [np.exp(x - x.max(-1, keepdims=True)) for x in matrices]
    stochastic = [p / p.sum(-1, keepdims=True) for p in distributions]
    hard = [x.argmax(-1) for x in matrices]
    if not fit_product["opening_learned"]:
        hard[:2] = reference
        stochastic[:2] = [D.one_hot(x) for x in reference]
    return hard, stochastic


def soft_net(roles, prior, points, channel):
    a, b, q, r = roles
    mass = np.einsum("lr,la,rb,abm->rbm", prior, a, b, D.FIRST)
    sent = np.einsum("rbm,mt,rbtc->mtc", mass, fit.heard(q), r)
    paid = prior.sum(1) @ (a @ D.SEND_COST) + prior.sum(0) @ (b @ D.SEND_COST)
    paid += mass.sum((0, 1)) @ (q @ D.QUERY_COST)
    return float((sent * fit.value(points, channel)).sum() - paid)


def exact_no_request(prior, points, channel):
    value = np.einsum("abm,mc->abc", D.FIRST, fit.value(points, channel)[:, 0, :])
    value -= D.SEND_COST[:, None, None] + D.SEND_COST[None, :, None]
    received = np.einsum("plbc,lr->prbc", value[MAPS], prior)
    feasible = R.SEND[:, :, None] & R.SEND[:, None, :]
    combinations = np.where(feasible, received, -np.inf).reshape(len(MAPS), 8, 16)
    best = int(combinations.max(-1).sum(-1).argmax())
    b, c = np.divmod(combinations[best].argmax(-1), 4)
    return MAPS[best], b, np.zeros(8, dtype=int), np.broadcast_to(c[:, None, None], (8, 4, 4))


def optimize_openers(q, r, prior, points, channel):
    values = fit.value(points, channel)
    following = np.einsum("mt,rbtc,mtc->rbm", fit.heard(D.one_hot(q)), D.one_hot(r), values)
    following -= D.QUERY_COST[q]
    outcomes = np.einsum("abm,rbm->rab", D.FIRST, following)
    outcomes -= D.SEND_COST[:, None] + D.SEND_COST[None, :]
    lefts = np.einsum("rplb,lr->prb", outcomes[:, MAPS], prior)
    feasible = np.where(R.SEND, lefts, -np.inf)
    best = int(feasible.max(-1).sum(-1).argmax())
    return MAPS[best], feasible[best].argmax(-1)


def metric(team, prior, points, channel):
    a, b, q, r = team
    mass = opening(a, b, prior)
    value = fit.measure((q, r), (a, b), mass, prior, points, channel)
    value["expected_requests"] = float(mass.sum((0, 1)) @ (q != 0))
    return value


def block(start, prior, points, channel):
    team, trace = start, []
    for _ in range(BLOCKS):
        before = metric(team, prior, points, channel)["net"]
        a, b = team[:2]
        q, r = fit.exact(points, opening(a, b, prior), channel)
        tail = (a, b, q, r)
        partial = metric(tail, prior, points, channel)["net"]
        new = (*optimize_openers(q, r, prior, points, channel), q, r)
        final = metric(new, prior, points, channel)["net"]
        assert before <= partial + 1e-10 and partial <= final + 1e-10
        trace.append([before, partial, final])
        team = new
        if final <= partial + 1e-10:
            return tail, trace
    return team, trace


def held():
    source = passage.study.EVIDENCE / "identity.json"
    repair = HERE / "facilitator-procedure-passage-evidence/results.json"
    a = historic.read(source)["admission"]["matrices"]["2719"]
    b = historic.read(repair)["whole_routing"]["measures"]["observed"]["held_admission"]
    return {key: (np.asarray(historic.rubric.ceilings(packet["criteria"])), np.asarray(channel))
            for key, (packet, _), channel in zip(("2719", "2504"), passage.study.sources().values(), (a, b), strict=True)}


def evaluate(public, channel, prior, fits):
    generated = {k: policies(public, prior, model) for k, model in fits.items()}
    joint, fixed = (generated[k][0] for k in ("joint", "fixed_opening"))
    declared = exact_no_request(prior, public, fit.PERFECT)
    comparator, steps = block(declared, prior, public, fit.PERFECT)
    reference = exact_no_request(prior, public, channel)
    hindsight, oracle_steps = block(reference, prior, public, channel)
    from_fit, fit_steps = block(joint, prior, public, channel)
    arms = {"joint_fit": joint, "fixed_opening_fit": fixed,
            "joint_opening_fixed_tail": (*joint[:2], *fixed[2:]),
            "fixed_opening_joint_tail": (*fixed[:2], *joint[2:]),
            "declared_no_request": declared, "declared_block_planner": comparator,
            "hindsight_no_request": reference, "hindsight_block_planner": hindsight,
            "hindsight_block_from_fit": from_fit}
    scored = {k: {**metric(team, prior, public, channel), "team": [a.tolist() for a in team]} for k, team in arms.items()}
    quiet = scored["hindsight_no_request"]["net"]
    for row in scored.values():
        row["advantage_over_hindsight_no_request"] = row["net"] - quiet
    for k, (pure, soft) in generated.items():
        assert abs(soft_net([D.one_hot(v) for v in pure], prior, public, channel) - scored[k + "_fit"]["net"]) < 1e-10
        scored[k + "_fit"]["stochastic_net"] = soft_net(soft, prior, public, channel)
    return {"policies": scored, "blocks": {"declared": steps, "hindsight": oracle_steps, "from_fit": fit_steps}}


def run():
    development = fit.OLD.base.cases()[0]
    matches = held()
    assert not {tuple(p[0]) for p in matches.values()} & {tuple(p[0]) for p in development.values()}
    fits = {name: train(development, name == "joint") for name in ("joint", "fixed_opening")}
    cases = {name: {label: evaluate(points, channel, R.TEST_PRIORS[label], fits) for label in fit.live.PRIORS}
             for name, (points, channel) in matches.items()}
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", Path(fit.__file__).resolve(),
             passage.study.EVIDENCE / "identity.json", HERE / "facilitator-procedure-passage-evidence/results.json")
    return {"training_cases": list(development), "updates_per_arm": UPDATES, "training": fits, "cases": cases,
            "sha256": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), ensure_ascii=False, indent=2))
