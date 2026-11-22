"""Infer unfamiliar workshop opening strategies from prior public receipts."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import warrant_requester_headroom as design

world = design.world
STEPS = (0, 1, 4, 16)
REPLICAS = 32
SEED = 17102
CONTAMINATION = .10


def models(task, p, style, factor):
    keys = design.TRAIN_PARTNERS
    products = list(product(keys, repeat=3)) if factor else [(key,) * 3 for key in keys]
    random = task.weights(np.full((3, 4, 3), 1 / 3.), p)
    utility, prevalence = [], []
    for pattern in products:
        table = np.stack([style[name][role] for role, name in enumerate(pattern)])
        mass = (1 - CONTAMINATION) * task.weights(np.eye(3)[table], p) + CONTAMINATION * random
        u, f = design.returns(task, mass)
        utility.append(u)
        prevalence.append(f)
    return np.asarray(utility), np.asarray(prevalence)


def posterior(likelihood, history):
    values = likelihood[:, history]
    assert np.all(values > 0.)
    log = np.log(values).sum(-1).T
    exp = np.exp(log - log.max(1, keepdims=True))
    return exp / exp.sum(1, keepdims=True)


def observations(task, mass, draws):
    _, f = design.returns(task, mass)
    cdf = np.cumsum(f)
    seen = np.searchsorted(cdf, draws, side="right")
    assert seen.max() < len(f) and np.all(f[seen] > 0)
    assert abs(f.sum() - 1.) < 1e-12
    return seen


def exact_evaluate(task, mass, numerator, prevalence, choices):
    """Average exact episode returns across varied prior observation histories."""
    count = len(choices)
    row = np.arange(task.num_states)
    net = numerator[row, choices].sum(1)
    requests = ((choices != 0) * prevalence).sum(1)
    assert np.all(task.legal[row, choices])
    certified = net + world.two.REPLY_COST * requests
    result = {"mean_net": float(net.mean()), "mean_requests": float(requests.mean()),
              "mean_certified": float(certified.mean()), "min_history_net": float(net.min()),
              "max_history_net": float(net.max()), "histories": count}
    if count == 1:
        raw = task.metrics(mass, choices[0])
        assert abs(raw["net"] - result["mean_net"]) < 1e-12
    return result


def panel(task, p, weights, coordinate, draws):
    style = design.partners(task, p, weights, coordinate)
    fits = {label: models(task, p, style, factor) for label, factor in (("homogeneous", False), ("role_factored", True))}
    mass_by_team = {key: task.weights(np.eye(3)[value], p) for key, value in style.items()}
    grade_only = task.requests(task.weights(np.full((3, 4, 3), 1 / 3.), p))
    standard_fit = task.requests(mass_by_team["fitted"])
    results = {}
    for name, actual in mass_by_team.items():
        history = observations(task, actual, draws)
        utility, prevalence = design.returns(task, actual)
        best = task.requests(actual)
        outcome = {key: exact_evaluate(task, actual, utility, prevalence, q[None]) for key, q in (
                    ("grade_only", grade_only), ("fit_assumed", standard_fit), ("partner_known", best))}
        for kind, (available, likelihood) in fits.items():
            outcome[kind] = {}
            for n in STEPS:
                post = posterior(likelihood, history[:, :n])
                blended = np.einsum("rh,hsa->rsa", post, available)
                queries = design.choose(task, blended)
                result = exact_evaluate(task, actual, utility, prevalence, queries)
                assert result["mean_net"] <= outcome["partner_known"]["mean_net"] + 1e-12
                result["mean_posterior_entropy"] = float(-(post * np.log(np.maximum(post, 1e-300))).sum(1).mean())
                outcome[kind][str(n)] = result
        results[name] = outcome
    return results


def run(fit):
    archive = json.loads(fit.read_text())
    weights = np.asarray(archive["fitted_weights"])
    rng = np.random.default_rng(SEED)
    reports = []
    for item in archive["results"]:
        task = world.Workshop(np.asarray(item["cards"]))
        priors = {}
        for label, prior_result in item["priors"].items():
            p = world.prior(label == "correlated")
            draws = rng.random((REPLICAS, STEPS[-1]))
            coordinate = prior_result["arms"]["coordinate"]["opening_table"]
            priors[label] = panel(task, p, weights, coordinate, draws)
        reports.append({"domain": item["i"], "priors": priors})
    paths = (Path(__file__), Path(design.__file__), Path(world.__file__), fit, design.EVIDENCE / "protocol.md")
    return {"seed": SEED, "history_lengths": STEPS, "paired_histories": REPLICAS, "contamination": CONTAMINATION,
            "rows": reports, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fit", type=Path, default=design.PREVIOUS, nargs="?")
    print(json.dumps(run(parser.parse_args().fit), indent=2))
