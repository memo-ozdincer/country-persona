"""Fit only the no-question responder while holding the deployed chair fixed."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

import facilitator_silence_joint_fit as study

D, fit, joint, R = study.D, study.fit, study.joint, study.R
EVIDENCE = study.HERE / "facilitator-first-send-evidence"
LEGAL = D.FINAL_LEGAL[:, :, 0]


def counterfactuals(mass, question, values):
    unheard = fit.heard(D.one_hot(question))[:, 0]
    return np.einsum("rbm,m,mc->rbc", mass, unheard, values[:, 0])


def prepare(public, mass, question, target=None):
    features = fit.features(public, mass, fit.PERFECT)[1][:, :, 0]
    values = fit.value(public if target is None else target, fit.PERFECT)
    reward = counterfactuals(mass, question, values)
    return features, reward - reward[..., :1]


def replace(response, first):
    new = response.copy()
    new[:, :, 0] = first
    assert np.array_equal(response[:, :, 1:], new[:, :, 1:])
    assert np.take_along_axis(np.broadcast_to(LEGAL, first.shape + (4,)), first[..., None], -1).all()
    return new


def train(original, aware):
    sets, _, _ = study.budget.development()
    rows = []
    for public, target in sets["budget_fit"].values():
        for prior in R.TEST_PRIORS.values():
            mass = joint.opening(*study.opening(public, prior, original), prior)
            question, _ = study.tail(public, mass, aware)
            rows.append(prepare(public, mass, question, target))
    features, rewards = [torch.from_numpy(np.stack(column)) for column in zip(*rows, strict=True)]
    weights = torch.nn.Parameter(torch.tensor(aware["response"], dtype=torch.float64))
    legal = torch.from_numpy(LEGAL)
    optimizer = torch.optim.Adam([weights], lr=.04)
    trace = []
    for step in range(study.UPDATES + 1):
        logits = (features @ weights).masked_fill(~legal, -torch.inf)
        expected = (logits.softmax(-1) * rewards).sum((1, 2, 3)).mean()
        greedy = torch.gather(rewards, -1, logits.argmax(-1, keepdim=True)).sum((1, 2, 3)).mean()
        trace.append({"step": step, "expected_margin": float(expected.detach()),
                      "greedy_margin": float(greedy)})
        if step < study.UPDATES:
            optimizer.zero_grad()
            (-expected).backward()
            assert torch.isfinite(weights.grad).all()
            optimizer.step()
    return {"weights": weights.detach().tolist(), "training_rows": len(rows), "trace": trace}


def compare(public, mass, reference, weights):
    left, right, question, response = reference
    features, payoff = prepare(public, mass, question)
    first = np.where(LEGAL, features @ weights, -np.inf).argmax(-1)
    exact = np.where(LEGAL, payoff, -np.inf).argmax(-1)
    exact = np.where(np.ptp(payoff, axis=-1) == 0, response[:, :, 0], exact)
    return {
        "response_aware": reference,
        "first_send_fit": (left, right, question, replace(response, first)),
        "declared_first_send": (left, right, question, replace(response, exact)),
    }


def record(teams, measure, archived, mass, values, receipt=None):
    reference = teams["response_aware"]
    question = reference[2] if receipt is None else reference[2][receipt]
    unheard = fit.heard(D.one_hot(question))[:, 0]
    visit = np.einsum("rbm,m->rb", mass, unheard)
    best = np.where(LEGAL, counterfactuals(mass, question, values), -np.inf).argmax(-1)
    best = np.where(visit > 0, best, reference[3][:, :, 0])
    teams = {**teams, "hindsight_first_send": (*reference[:3], replace(reference[3], best))}
    result = {}
    for name, team in teams.items():
        score = measure(team)
        assert np.array_equal(reference[2], team[2])
        assert score["net"] <= archived["hindsight_exact_joint"]["net"] + 1e-10
        first = team[3][:, :, 0]
        result[name] = {
            "net": score["net"], "net_over_no_request": score["net"] - archived["hindsight_no_request"]["net"],
            "net_change": score["net"] - archived["response_aware"]["net"],
            "first_send": first.tolist(),
            "changed_first_send_probability": float(visit[first != reference[3][:, :, 0]].sum()),
        }
    assert abs(result["response_aware"]["net_change"]) < 1e-10
    assert all(x["net"] <= result["hindsight_first_send"]["net"] + 1e-10 for x in result.values())
    return result


def evaluate(base, original, old, weights):
    cases = {}
    for case, (_, channel) in joint.held().items():
        cases[case] = {}
        for cap, laws in old["cases"][case].items():
            bank = base["cases"][case]["outcomes"][cap]
            public, target = map(np.asarray, (bank["public_scores"], bank["terminal_scores"]))
            cases[case][cap] = {}
            for law, archived in laws.items():
                prior = R.TEST_PRIORS[law]
                teams = policies(original, public, prior, archived, weights)
                mass = joint.opening(*teams["response_aware"][:2], prior)
                cases[case][cap][law] = record(
                    teams, lambda t: joint.metric(t, prior, target, channel), archived, mass, fit.value(target, channel))
    return cases


def policies(original, public, prior, archived, weights):
    reference = tuple(np.asarray(archived["response_aware"]["policy"][name])
                      for name in ("left", "right", "request", "response"))
    assert all(np.array_equal(a, b) for a, b in zip(reference[:2], study.opening(public, prior, original), strict=True))
    return compare(public, joint.opening(*reference[:2], prior), reference, weights)


def evaluate_2466(original, old, weights):
    mediated = study.mediated
    read = study.budget.read
    public = np.asarray(read(mediated.base.FORECAST)["curves"]["70"]["prefix"])
    ordinary = read(study.MEDIATED / "bare-admission.json")
    stress = read(study.MEDIATED / "stress-results.json")["identity"]["1/2/3"]
    value, _ = mediated.budget_values(read(mediated.base.PACKET))
    cases = {}
    for case, source in (("ordinary", ordinary), ("withholding_stress", stress)):
        observed = np.asarray(source["admitted_masks"])
        values = ((1 - D.LOSS) * value[mediated.MASKS[:, None, None] | observed[None, :, :]]
                  + D.LOSS * value[:, None, None] - D.SEND_COST)
        cases[case] = {}
        for law, archived in old["cases"]["2466"][case].items():
            prior = R.TEST_PRIORS[law]
            teams = policies(original, public, prior, archived, weights)
            mass = mediated.first_mass(*teams["response_aware"][:2], prior, observed[0])
            cases[case][law] = record(
                teams, lambda t: mediated.measure(t, prior, value, observed[0], observed),
                archived, mass, values, mediated.PRESENT)
    return cases


def run():
    torch.set_num_threads(1)
    base = study.budget.read(study.OLD)
    original = base["training"]["budget_fit"]
    old_path = study.EVIDENCE / "results.json"
    old = study.budget.read(old_path)
    model = train(original, old["fit"]["response_aware"])
    cases = evaluate(base, original, old, model["weights"])
    cases["2466"] = evaluate_2466(original, old, model["weights"])
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", old_path, study.OLD)
    return {"fit": model, "cases": cases,
            "sha256": {str(p.relative_to(study.HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
