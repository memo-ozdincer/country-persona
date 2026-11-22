"""Distinguish policy improvement from sharpening an existing disclosure rule."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import warrant_three as study

TEMPERATURE_CHOICES = (1., 3., 6., 12., 24., 48., 96., 0.)


def actions(feature, weights, inverse_temperature):
    score = (feature * weights[:, None, None]).sum(-1)
    if inverse_temperature == 0.:
        return np.eye(3)[score.argmax(-1)]
    logits = (score - score.max(-1, keepdims=True)) * inverse_temperature
    prob = np.exp(logits)
    return prob / prob.sum(-1, keepdims=True)


def measure(task, feature, p, weights, inverse_temperature):
    chosen = actions(feature, weights, inverse_temperature)
    mass = task.weights(chosen, p)
    result = task.metrics(mass, task.requests(mass))
    result["opening_entropy_nats"] = float(-np.sum(chosen * np.log(np.maximum(chosen, 1e-300)), axis=-1).mean())
    return result


def run(path):
    learned = np.asarray(json.loads(path.read_text())["fitted_weights"])
    domains = list(study.domains())
    p = study.prior(False)
    trials = {scale: [] for scale in TEMPERATURE_CHOICES}
    stochastic_fit = []
    for cards in domains[:study.N_TRAIN]:
        task = study.Workshop(cards)
        inputs = task.features(p)
        stochastic_fit.append(measure(task, inputs, p, learned, 6.)["net"])
        for scale in trials:
            trials[scale].append(measure(task, inputs, p, study.INITIAL, scale)["net"])
    selected = max(trials, key=lambda scale: np.mean(trials[scale]))
    evaluations = []
    for i, cards in enumerate(domains[study.N_TRAIN:]):
        task = study.Workshop(cards)
        for label, correlated in (("uniform", False), ("correlated", True)):
            actual = study.prior(correlated)
            feat = task.features(actual)
            candidates = {
                "initial_same_scale": (study.INITIAL, 6.),
                "initial_tuned_scale": (study.INITIAL, selected),
                "initial_deterministic": (study.INITIAL, 0.),
                "learned_stochastic": (learned, 6.),
                "learned_deterministic": (learned, 0.),
            }
            metrics = {key: measure(task, feat, actual, weights, scale) for key, (weights, scale) in candidates.items()}
            evaluations.append({"domain": i, "prior": label, "arms": metrics})
    return {"zero_inverse_temperature_code": "Deterministic maximum, not a uniform softmax.",
            "training_initial_grid": {str(temp): float(np.mean(net)) for temp, net in trials.items()},
            "training_stochastic_fit": float(np.mean(stochastic_fit)), "chosen_inverse_temperature": selected,
            "held": evaluations, "sha256": {p.name: sha256(p.read_bytes()).hexdigest()
                                           for p in (Path(__file__), Path(study.__file__), path)}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit", type=Path)
    print(json.dumps(run(cli.parse_args().fit), indent=2))
