"""Separate lower traffic from selective signaling and compare frozen scripts."""
import json
from pathlib import Path

import optional_peer_policy as experiment

HERE = Path(__file__).resolve().parent
base = experiment.base
SOURCE = HERE / "evidence/optional-peer-policy.json"


def uniform_thinning(weights, focus, fee, rate):
    """Keep the archived card policy and randomize the decision to signal."""
    always = experiment.lift(weights, focus, fee, True)
    no_send = experiment.lift(weights, focus, fee, False)
    return {key: [rate * a + (1 - rate) * b for a, b in zip(prob, no_send[key], strict=True)]
            for key, prob in always.items()}


def shuffle_send_gate(weights, focus, fee, rate):
    """Keep learned excerpt marginals and replies while removing selective sending."""
    randomized = dict(weights)
    for holding in base.PAIRS:
        key = ("sender", fee, focus, holding)
        original = weights[key]
        excerpt_probability = [original[0] + original[1], original[2] + original[3]]
        randomized[key] = [excerpt_probability[choice] * (rate if pay else 1 - rate)
                           for choice, pay in experiment.ACTIONS]
    return randomized


def run():
    original = json.loads(SOURCE.read_text())
    learned = experiment.restore(SOURCE)
    mandatory = experiment.restore(experiment.PARENT_POLICY)
    writer = {}
    ids = experiment.synthesis.contract.previous.SOURCE_IDS
    for label, row in json.loads(experiment.TABLE_PATH.read_text())["terminal_records"].items():
        held = frozenset() if label == "public" else frozenset(ids.index(s) for s in label.split(","))
        writer[held] = row
    fitted_prior = base.roster("training")
    output = {}
    frozen_scripts = {(fee, focus): experiment.exact_script(focus, fitted_prior, fee)[1]
                      for fee in experiment.FEES for focus in base.PAIRS}
    for label, condition in original["conditions"].items():
        regime, raw_fee = label.split("/")
        fee = float(raw_fee)
        prior = base.roster(regime)
        cases = []
        for focus, logged in zip(base.PAIRS, condition["cases"], strict=True):
            assert focus == tuple(logged["focus"])
            record = logged["metrics"]["optional_fit"]
            selected = experiment.replay(learned, fee, focus, prior, writer)
            assert all(abs(selected[key] - value) < 1e-9 for key, value in record.items())
            budget = record["peer_attempt_rate"]
            thinned = uniform_thinning(mandatory, focus, fee, min(1., budget))
            shuffled = shuffle_send_gate(learned, focus, fee, min(1., budget))
            alternatives = {
                "learned": record,
                "matched_random_thinning": experiment.replay(thinned, fee, focus, prior, writer),
                "same_fit_random_send_gate": experiment.replay(shuffled, fee, focus, prior, writer),
                "frozen_uniform_prior_script": experiment.replay(frozen_scripts[fee, focus], fee, focus, prior, writer),
                "known_shift_prior_script": logged["metrics"]["known_prior_optional"],
            }
            assert abs(alternatives["matched_random_thinning"]["peer_attempt_rate"] - budget) < 1e-9
            assert abs(alternatives["same_fit_random_send_gate"]["peer_attempt_rate"] - budget) < 1e-9
            cases.append({"focus": focus, "metrics": alternatives})
        output[label] = {"cases": cases, "mean": {
            name: {key: sum(r["metrics"][name][key] for r in cases) / len(cases) for key in metrics}
            for name, metrics in cases[0]["metrics"].items()}}
    return {
        "scope": "No further fit. Source-independent Bernoulli controls match the learned send rate per "
                 "public request and prior. One keeps the previous mandatory policies. The other keeps "
                 "the new learned excerpt marginals and the new learned recipient policy. The frozen script "
                 "is optimized on the same uniform prior as the fit.",
        "conditions": output,
        "pins": {p.name: experiment.synthesis.contract.runner.digest(p) for p in (
            SOURCE, Path(__file__), experiment.TABLE_PATH)},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
