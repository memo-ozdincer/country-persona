"""Optimize a response policy and a silence-relative chair reserve."""
import json
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np
import torch

import facilitator_budget_policy as budget

adaptive, joint, fit, D, R = budget.adaptive, budget.joint, budget.fit, budget.D, budget.R
HERE = joint.HERE
EVIDENCE = HERE / "facilitator-silence-joint-evidence"
OLD = budget.EVIDENCE / "results.json"
MEDIATED = HERE / "haiti2466-budget-transfer/mediated-delivery"
sys.path.insert(0, str(MEDIATED))
import replay_delivery as mediated

TEMPERATURE = .15
UPDATES = 96
ALLOWED = (D.CHAIR_LEGAL, D.FINAL_LEGAL)


def opening(public, prior, original):
    return tuple(adaptive.contextual_policies(public, prior, original)[0][:2])


def action_advantage(mass, values, replies):
    after = np.einsum("rbm,rbtc,mtc->mt", mass, replies, values, optimize=True)
    visiting = np.maximum(mass.sum((0, 1)), 1e-12)
    return (1 - D.LOSS) * (after - after[:, :1]) / visiting[:, None] - D.QUERY_COST


def training_rows(original):
    sets, _, _ = budget.development()
    batch = []
    for public, target in sets["budget_fit"].values():
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            mass = joint.opening(*opening(public, prior, original), prior)
            features = fit.features(public, mass, fit.PERFECT)
            batch.append((*features, mass, fit.value(public, fit.PERFECT), fit.value(target, fit.PERFECT)))
    return [torch.from_numpy(np.stack(x)) for x in zip(*batch, strict=True)]


def train(batch, original, aware):
    x, y, mass, predicted, scored = batch
    request_mask, reply_mask = map(torch.from_numpy, ALLOWED)
    query_cost = torch.from_numpy(D.QUERY_COST)
    erasure = torch.from_numpy(fit.ERASURE)
    visit = mass.sum((1, 2))
    request_weights = torch.nn.Parameter(torch.tensor(original["weights"][2], dtype=torch.float64))
    responder = torch.nn.Parameter(torch.tensor(original["weights"][3], dtype=torch.float64))
    reserve = torch.nn.Parameter(torch.tensor(-4., dtype=torch.float64))
    parameters = (reserve, responder) if aware else (request_weights, responder)
    optimizer = torch.optim.Adam(parameters, lr=.04)
    trace = []
    for step in range(UPDATES + 1):
        replies = (y @ responder).masked_fill(~reply_mask, -torch.inf).softmax(-1)
        if aware:
            marginal = torch.einsum("nrbm,nrbtc,nmtc->nmt", mass, replies, predicted)
            advantage = (1 - D.LOSS) * (marginal - marginal[..., :1]) / visit.clamp_min(1e-12)[..., None]
            extra = torch.nn.functional.softplus(reserve)
            logits = (advantage - query_cost - extra * (query_cost != 0)) / TEMPERATURE
        else:
            logits = x @ request_weights
        ask = logits.masked_fill(~request_mask, -torch.inf).softmax(-1)
        heard = (1 - D.LOSS) * ask + D.LOSS * erasure
        sent = torch.einsum("nrbm,nmt,nrbtc->nmtc", mass, heard, replies)
        reward = (sent * scored).sum((1, 2, 3)) - ((ask @ query_cost) * visit).sum(1)
        objective = reward.mean()
        trace.append({"step": step, "followup_net": float(objective.detach()),
                      "queries": float(((1 - ask[..., 0]) * visit).sum(1).mean().detach())})
        if step == UPDATES:
            break
        optimizer.zero_grad()
        (-objective).backward()
        assert all(torch.isfinite(p.grad).all() for p in parameters)
        trace[-1]["gradient_norms"] = [float(p.grad.norm()) for p in parameters]
        optimizer.step()
    return {"response": responder.detach().tolist(), "trace": trace,
            "request": None if aware else request_weights.detach().tolist(),
            "reserve": float(torch.nn.functional.softplus(reserve).detach()) if aware else 0.}


def tail(public, mass, model):
    x, y = fit.features(public, mass, fit.PERFECT)
    replies = np.where(ALLOWED[1], y @ model["response"], -np.inf).argmax(-1)
    if model["request"] is None:
        logits = action_advantage(mass, fit.value(public, fit.PERFECT), D.one_hot(replies))
        logits -= model["reserve"] * (D.QUERY_COST != 0)
    else:
        logits = x @ model["request"]
    return np.where(ALLOWED[0], logits, -np.inf).argmax(-1), replies


def players(public, prior, original, fits):
    left, right = opening(public, prior, original)
    mass = joint.opening(left, right, prior)
    initial = {"request": original["weights"][2], "response": original["weights"][3], "reserve": 0.}
    aware = fits["response_aware"]
    treatments = {
        **fits, "archived": initial,
        "trained_responder_zero_reserve": dict(aware, reserve=0.),
        "initial_responder_trained_reserve": dict(aware, response=initial["response"]),
        "initial_responder_zero_reserve": dict(aware, reserve=0., response=initial["response"]),
    }
    teams = {key: (left, right, *tail(public, mass, model)) for key, model in treatments.items()}
    teams["declared_exact_joint"] = (left, right, *fit.exact(public, mass, fit.PERFECT))
    return teams


def summary(teams, evaluate):
    rows = {}
    for name, team in teams.items():
        score = evaluate(team)
        net = score["net"]
        saved = {k: np.asarray(p).tolist() for k, p in zip(("left", "right", "request", "response"), team, strict=True)}
        rows[name] = {"net": net, "queries": score.get("queries", score.get("expected_requests")), "policy": saved}
    silence = rows["hindsight_no_request"]["net"]
    for row in rows.values():
        row["net_over_hindsight_no_request"] = row["net"] - silence
    assert all(r["net"] <= rows["hindsight_exact_joint"]["net"] + 1e-10 for r in rows.values())
    return rows


def evaluate_held(base, original, fits):
    held = joint.held()
    cases = {}
    for case, (_, channel) in held.items():
        cases[case] = {}
        for cap in ("70", "90"):
            prior_rows = {}
            bank = base["cases"][case]["outcomes"][cap]
            public, target = (np.asarray(bank[k]) for k in ("public_scores", "terminal_scores"))
            for label in fit.live.PRIORS:
                prior = R.TEST_PRIORS[label]
                teams = players(public, prior, original, fits)
                l, r = teams["archived"][:2]
                mass = joint.opening(l, r, prior)
                teams["hindsight_no_request"] = (l, r, *fit.exact(target, mass, channel, independent=True))
                teams["hindsight_exact_joint"] = (l, r, *fit.exact(target, mass, channel))
                prior_rows[label] = summary(teams, lambda team: joint.metric(team, prior, target, channel))
            cases[case][cap] = prior_rows
    return cases


def evaluate_2466(original, fits):
    packet = budget.read(mediated.base.PACKET)
    public = np.asarray(budget.read(mediated.base.FORECAST)["curves"]["70"]["prefix"])
    recorded = budget.read(MEDIATED / "bare-admission.json")
    stress = budget.read(MEDIATED / "stress-results.json")["identity"]["1/2/3"]
    value, _ = mediated.budget_values(packet)
    rows = {}
    for case, source in (("ordinary", recorded), ("withholding_stress", stress)):
        observed = np.asarray(source["admitted_masks"])
        rows[case] = {}
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            teams = players(public, prior, original, fits)
            l, r = teams["archived"][:2]
            mass = mediated.first_mass(l, r, prior, observed[0])
            teams["hindsight_no_request"] = (l, r, *mediated.exact(mass, value, observed, quiet=True))
            teams["hindsight_exact_joint"] = (l, r, *mediated.exact(mass, value, observed))
            result = summary(teams, lambda team: mediated.measure(team, prior, value, observed[0], observed))
            for mode in ("archived", "response_aware"):
                assert abs(result[mode]["net"] - mediated.direct_net(teams[mode], prior, value, observed[0], observed)) < 1e-10
            rows[case][label] = result
    return rows


def run():
    torch.set_num_threads(1)
    base = budget.read(OLD)
    original = base["training"]["budget_fit"]
    batch = training_rows(original)
    models = {name: train(batch, original, mode)
              for name, mode in (("feature_fit", False), ("response_aware", True))}
    fit_free = evaluate_held(base, original, models)
    fit_free["2466"] = evaluate_2466(original, models)
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", OLD,
             MEDIATED / "bare-admission.json", MEDIATED / "stress-results.json")
    return {"training_rows": len(batch[0]), "updates_per_arm": UPDATES, "fit": models, "cases": fit_free,
            "sha256": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
