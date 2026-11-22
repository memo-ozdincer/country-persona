"""Fit decentralized follow-up policies using a refreshed public opening model."""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
import torch

import facilitator_passage_joint_fit as joint
from facilitator_passage_joint_initialization import START

fit, D, R = joint.fit, joint.D, joint.R
EVIDENCE = joint.HERE / "facilitator-passage-adaptive-fit-evidence"
MASKS = (R.SEND, R.SEND, D.CHAIR_LEGAL, D.FINAL_LEGAL)


def tail_features(points, masses):
    columns = zip(*(fit.features(p, m, fit.PERFECT) for p, m in zip(points, masses, strict=True)), strict=True)
    return tuple(torch.from_numpy(np.stack(values)) for values in columns)


def train(development):
    torch.set_num_threads(1)
    rows = [(public, target, R.TEST_PRIORS[label])
            for public, target in development.values() for label in fit.live.PRIORS]
    points = [public for public, _, _ in rows]
    left, right = zip(*(joint.inputs(public, prior)[0][:2] for public, _, prior in rows), strict=True)
    a, b = (torch.from_numpy(np.stack(values)) for values in (left, right))
    prior = torch.from_numpy(np.stack([law for _, _, law in rows]))
    reward = torch.from_numpy(np.stack([fit.value(target, fit.PERFECT) for _, target, _ in rows]))
    weights = [torch.nn.Parameter(torch.tensor(w, dtype=torch.float64)) for w in (START, START, *fit.OLD.INITIAL)]
    optimizer = torch.optim.Adam(weights, lr=.04)
    masks = tuple(map(torch.from_numpy, MASKS))
    send, ask_cost, transition, erasure = map(torch.from_numpy, (D.SEND_COST, D.QUERY_COST, D.FIRST, fit.ERASURE))
    trace = []
    for step in range(joint.UPDATES + 1):
        l, r = [(x @ w).masked_fill(~mask, -torch.inf).softmax(-1)
                for x, w, mask in zip((a, b), weights[:2], masks[:2], strict=True)]
        first = torch.einsum("nlr,nla,nrb,abm->nrbm", prior, l, r, transition)
        features = tail_features(points, first.detach().numpy())
        asks, replies = [(x @ w).masked_fill(~mask, -torch.inf).softmax(-1)
                         for x, w, mask in zip(features, weights[2:], masks[2:], strict=True)]
        heard = (1 - D.LOSS) * asks + D.LOSS * erasure
        end = torch.einsum("nrbm,nmt,nrbtc->nmtc", first, heard, replies)
        cost = ((prior.sum(2) * (l @ send)).sum(1) + (prior.sum(1) * (r @ send)).sum(1)
                + ((asks @ ask_cost) * first.sum((1, 2))).sum(1))
        objective = ((end * reward).sum((1, 2, 3)) - cost).mean()
        trace.append({"step": step, "net": float(objective.detach()),
                      "requests": float(((1 - asks[..., 0]) * first.sum((1, 2))).sum(1).mean().detach())})
        if step == joint.UPDATES:
            break
        optimizer.zero_grad()
        (-objective).backward()
        assert all(torch.isfinite(w.grad).all() for w in weights)
        trace[-1]["gradient_norms"] = [float(w.grad.norm()) for w in weights]
        optimizer.step()
    return {"weights": [w.detach().tolist() for w in weights], "trace": trace, "opening_learned": True}


def contextual_policies(points, prior, model):
    greedy, soft = joint.policies(points, prior, model)
    greedy_opening = joint.opening(*greedy[:2], prior)
    soft_opening = np.einsum("lr,la,rb,abm->rbm", prior, *soft[:2], D.FIRST)
    weights = model["weights"][2:]
    greedy[2:] = fit.action_policy(weights, points, greedy_opening, fit.PERFECT)
    for index, (features, weight, mask) in enumerate(zip(
            fit.features(points, soft_opening, fit.PERFECT), weights, MASKS[2:], strict=True), start=2):
        logits = np.where(mask, features @ weight, -np.inf)
        mass = np.exp(logits - logits.max(-1, keepdims=True))
        soft[index] = mass / mass.sum(-1, keepdims=True)
    return greedy, soft


def run():
    development = fit.OLD.base.cases()[0]
    held_cases = joint.held()
    assert not {tuple(p[0]) for p in held_cases.values()} & {tuple(p[0]) for p in development.values()}
    archive_path = joint.EVIDENCE / "weak-start.json"
    archive = joint.historic.read(archive_path)
    model = train(development)
    cases = {}
    for docket, (points, channel) in held_cases.items():
        cases[docket] = {}
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            controls = archive["cases"][docket][label]["policies"]
            reference = controls["fixed_opening_fit"]["team"][:2]
            quiet = controls["hindsight_no_request"]["net"]
            results = {k: controls[k] for k in ("joint_fit", "fixed_opening_fit", "declared_block_planner",
                                                "hindsight_no_request")}
            for name, params, policy in (
                ("adaptive", model, contextual_policies),
                ("adaptive_weights_static_context", model, joint.policies),
                ("archived_weights_refreshed_context", archive["fit"], contextual_policies),
            ):
                greedy, soft = policy(points, prior, params)
                score = joint.metric(greedy, prior, points, channel)
                score["stochastic_net"] = joint.soft_net(soft, prior, points, channel)
                score["advantage_over_hindsight_no_request"] = score["net"] - quiet
                score["opening_matches"] = [int(np.count_nonzero(a == b))
                                            for a, b in zip(greedy[:2], reference, strict=True)]
                score["team"] = [a.tolist() for a in greedy]
                results[name] = score
            cases[docket][label] = results
    sources = (Path(__file__).resolve(), archive_path, EVIDENCE / "protocol.md")
    return {"fit": model, "development": list(development), "cases": cases,
            "sha256": {str(p.relative_to(joint.HERE)): sha256(p.read_bytes()).hexdigest() for p in sources}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
