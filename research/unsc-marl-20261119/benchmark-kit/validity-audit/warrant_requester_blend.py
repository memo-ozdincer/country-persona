"""Blend partner models using reserved receipt likelihood, without style labels."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import warrant_requester_em as flexible

adapt = flexible.prior
design = adapt.design
world = adapt.world
PREFIX = 12


def validation_discrete(likelihood, history):
    weights = adapt.posterior(likelihood, history[:, :PREFIX])
    log = np.log(weights) + np.log(likelihood[:, history[:, PREFIX:]]).sum(-1).T
    peak = log.max(1)
    return peak + np.log(np.exp(log - peak[:, None]).sum(1))


def measurement(task, p, learned, coordinate, draws):
    styles = design.partners(task, p, learned, coordinate)
    likelihood_utility, likelihood = adapt.models(task, p, styles, factor=True)
    ledger, support = flexible.registry(task)
    warm = (1 - adapt.CONTAMINATION) * np.stack([np.eye(3)[styles[k]] for k in design.TRAIN_PARTNERS]).mean(0) + adapt.CONTAMINATION / 3.
    outcomes = {}
    for name, table in styles.items():
        true = task.weights(np.eye(3)[table], p)
        actual, prevalence = design.returns(task, true)
        seen = adapt.observations(task, true, draws)
        hypothesis_fit = validation_discrete(likelihood, seen)
        flexible_fit = flexible.fit_histories(ledger, support, seen[:, :PREFIX], p, warm)
        validate = []
        for r, params in enumerate(flexible_fit):
            _, predictive = design.returns(task, task.weights(params, p))
            validate.append(np.log(predictive[seen[r, PREFIX:]]).sum())
        difference = np.clip(np.asarray(validate) - hypothesis_fit, -700., 700.)
        probability = 1. / (1. + np.exp(-difference))
        discrete = np.einsum("rh,hsa->rsa", adapt.posterior(likelihood, seen), likelihood_utility)
        refit = flexible.fit_histories(ledger, support, seen, p, warm)
        free = np.stack([design.returns(task, task.weights(params, p))[0] for params in refit])
        blended = (1 - probability[:, None, None]) * discrete + probability[:, None, None] * free
        tailored = design.choose(task, blended)
        result = adapt.exact_evaluate(task, true, actual, prevalence, tailored)
        assert result["mean_net"] <= task.metrics(true, task.requests(true))["net"] + 1e-12
        outcomes[name] = {**result, "mean_flexible_model_weight": float(probability.mean())}
    return outcomes


def run(path):
    frozen = json.loads(path.read_text())
    weights = np.asarray(frozen["fitted_weights"])
    rng = np.random.default_rng(adapt.SEED)
    results = []
    for row in frozen["results"]:
        task = world.Workshop(np.asarray(row["cards"]))
        for label, metrics in row["priors"].items():
            p = world.prior(label == "correlated")
            random = rng.random((adapt.REPLICAS, adapt.STEPS[-1]))
            control = metrics["arms"]["coordinate"]["opening_table"]
            results.append({"domain": row["i"], "prior": label,
                            "teams": measurement(task, p, weights, control, random)})
    files = (Path(__file__), Path(flexible.__file__), Path(adapt.__file__), path)
    return {"history_for_initial_models": PREFIX, "reserved_validation_receipts": adapt.STEPS[-1] - PREFIX,
            "rows": results, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit", type=Path, nargs="?", default=design.PREVIOUS)
    print(json.dumps(run(cli.parse_args().fit), indent=2))
