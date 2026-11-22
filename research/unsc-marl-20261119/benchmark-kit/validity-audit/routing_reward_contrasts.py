"""Exact contrasts for reward adaptation with fixed evidence roles."""
import argparse
import json
from pathlib import Path

import numpy as np

import rubric_conditioned_routing as base

route = base.route
OUT = base.space.OUT / "routing-reward-contrasts"
SPECS = {
    "balanced_first_pair": ((9, 8, 7), 3, 16, 1.),
    "balanced_last_pair": ((9, 8, 7), 6, 16, 1.),
    "steep_first_pair": ((12, 8, 4), 3, 16, 1.),
    "steep_last_pair": ((12, 8, 4), 6, 16, 1.),
    "low_stakes": ((9, 8, 7), 3, 16, .004),
}
PAIRS = {
    "balanced_reweighting": ("balanced_first_pair", "balanced_last_pair"),
    "steep_reweighting": ("steep_first_pair", "steep_last_pair"),
    "scale_change": ("balanced_first_pair", "low_stakes"),
}


def rewards():
    rows = {}
    for name, (weights, mask, bonus, scale) in SPECS.items():
        value = route.points({"weights": weights, "joint": (mask, bonus)}) * scale
        np.testing.assert_array_equal(base.canonical(value)[0], value)
        assert base.canonical(value)[1] == (0, 1, 2)
        rows[name] = value
    return rows


def make_net():
    import torch

    return torch.nn.Sequential(torch.nn.Linear(8, 48), torch.nn.Tanh(), torch.nn.Linear(48, 48),
                               torch.nn.Tanh(), torch.nn.Linear(48, 256))


def load(path):
    import torch

    net = make_net()
    net.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    return net.eval()


def read_frozen():
    report = json.loads((base.OUT / "report.json").read_text())
    checkpoint = base.OUT / "weights.pt"
    assert base.space.runner.digest(checkpoint) == report["weights_sha256"]
    response = load(checkpoint)
    mean = np.asarray(report["training_rewards"]).mean(axis=0)
    assert all(tuple(v) not in {tuple(x) for x in report["training_rewards"]} for v in rewards().values())
    return response, mean


def exact_priors(profile):
    loss = route.TRAIN_LOSS
    matrix = route.receipt_matrix(profile, loss)
    return {name: {"independent": route.best_silent(p, matrix),
                   "exact_query": route.exact_optional(p, matrix, loss)[0]}
            for name, p in route.TEST_PRIORS.items()}


def measure(policy, profile, prior):
    return route.evaluate(policy, prior, profile, route.TRAIN_LOSS)


def panel():
    values = rewards()
    net, mean = read_frozen()
    result = {}
    for name, score in values.items():
        frozen = base.choose(net, score)
        constant = base.choose(net, mean)
        profiles = {}
        for prior_name, exact in exact_priors(score).items():
            prior = route.TEST_PRIORS[prior_name]
            methods = {"frozen": frozen, "constant_input": constant, **exact}
            trial = {k: measure(action, score, prior) for k, action in methods.items()}
            assert max(x["net"] for x in trial.values()) <= trial["exact_query"]["net"] + 1e-9
            profiles[prior_name] = {**trial, "exact_query_policy": [p.tolist() for p in exact["exact_query"]]}
        result[name] = {"payoff": score.tolist(), "frozen_greedy_policy": [p.tolist() for p in frozen],
                        "priors": profiles}
    pairs = {}
    for label, names in PAIRS.items():
        first, second = (values[name] for name in names)
        common_payoff = (first + second) / 2
        common = {}
        for prior_name, prior in route.TEST_PRIORS.items():
            policy, count = route.exact_optional(prior, route.receipt_matrix(common_payoff, route.TRAIN_LOSS),
                                                 route.TRAIN_LOSS)
            records = {}
            for name, score in zip(names, (first, second), strict=True):
                endpoint = result[name]["priors"][prior_name]
                common_net = measure(policy, score, prior)["net"]
                records[name] = {"fixed_policy_net": common_net, "regret": endpoint["exact_query"]["net"] - common_net}
            common[prior_name] = {"results": records, "request_maps_examined": count,
                                  "mean_fixed_policy_regret": sum(x["regret"] for x in records.values()) / 2}
        pairs[label] = common
    assert pairs["balanced_reweighting"]["uniform"]["mean_fixed_policy_regret"] > .5
    assert result["low_stakes"]["priors"]["uniform"]["exact_query"]["net"] == 0
    return {"scope": "Synthetic reward retuning on the same three protected slots. The canonical permutation, "
                     "link loss and message fees are fixed. Exact enumeration certifies the cost of a shared "
                     "policy in each pair. No historical interpretation or new model generation is scored here.",
            "frozen_checkpoint_sha256": base.space.runner.digest(base.OUT / "weights.pt"), "profile": result,
            "pairs": pairs, "contrast_code_sha256": base.space.runner.digest(Path(__file__))}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--save", action="store_true")
    args = cli.parse_args()
    out = panel()
    if args.save:
        OUT.mkdir()
        (OUT / "panel.json").write_text(json.dumps(out, indent=2) + "\n")
    else:
        print(json.dumps(out, indent=2))
