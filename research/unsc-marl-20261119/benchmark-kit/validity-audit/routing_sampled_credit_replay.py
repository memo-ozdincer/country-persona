"""Verify the frozen paired fit and score its policies under the existing inventory shifts."""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

import routing_sampled_credit as experiment

paired, base, route = experiment.paired, experiment.base, experiment.route
digest = experiment.space.runner.digest
PRIORS = experiment.space.OUT / "routing-prior-robustness/report.json"


def check_estimator():
    """Check ordered score-function gradients on one nontrivial source inventory pair."""
    dtype = torch.float64
    first_actions = np.flatnonzero(route.JOINT[3].ravel())
    second_actions = np.flatnonzero(route.SEND[6])
    a_q, a_send = first_actions // 4, first_actions % 4
    a_logits = torch.linspace(-.45, .35, len(first_actions), dtype=dtype).requires_grad_()
    b_logits = torch.linspace(-.3, .8, 4 * len(second_actions), dtype=dtype).reshape(4, -1).requires_grad_()
    a = a_logits.softmax(-1)
    b = b_logits.softmax(-1)[a_q]
    raw = np.arange(8, dtype=float) ** 1.4
    reward = torch.as_tensor(route.receipt_matrix(raw, 0.)[np.ix_(a_send, second_actions)], dtype=dtype)
    reward -= torch.as_tensor((a_q != 0)[:, None] * route.SIGNAL_COST)
    total = (a[:, None] * b * reward).sum()
    gold = torch.autograd.grad(total, (a_logits, b_logits), retain_graph=True)
    detached_a, detached_b = a.detach(), b.detach()
    conditional_a = (detached_b * reward).sum(-1)
    conditional_b = (detached_b * reward).sum(-1, keepdim=True)
    a_terms = detached_a * (conditional_a - (detached_a * conditional_a).sum()) * a.log()
    b_terms = detached_a[:, None] * detached_b * (reward - conditional_b) * b.log()
    actual = torch.autograd.grad(a_terms.sum() + b_terms.sum(), (a_logits, b_logits))
    errors = [float((x - y).abs().max()) for x, y in zip(gold, actual, strict=True)]
    assert max(errors) < 1e-12
    return errors


def summarize(directory):
    report = json.loads((directory / "report.json").read_text())
    launch = json.loads((directory / "launch.json").read_text())
    assert launch["code_sha256"] == {Path(file).name: digest(Path(file)) for file in
                                    (experiment.__file__, paired.__file__, base.__file__, route.__file__)}
    train = paired.curriculum()
    np.testing.assert_array_equal(train, report["training_profiles"])
    aligned, curve, rms = experiment.fit(train)
    assert curve == report["training_checkpoints"] and rms == report["advantage_rms"]
    frozen = {}
    for name in experiment.ARMS:
        path = directory / f"{name}.pt"
        assert digest(path) == report["weights_sha256"][name]
        net = paired.contrasts.load(path)
        assert all(torch.equal(net.state_dict()[key], value) for key, value in aligned[name].state_dict().items())
        frozen[name] = net
    assert experiment.evaluate(frozen) == report["historical_replay"]
    archive = json.loads(PRIORS.read_text())
    priors = {name: np.asarray(p) for group in ("prior_anchors", "prior_stress") for name, p in archive[group].items()}
    all_results = {}
    for case, checksum, profile, actual in base.held_out():
        original = archive["historical"][case]
        assert original["source_sha256"] == checksum
        policies = {key: base.choose(net, profile) for key, net in frozen.items()}
        all_results[case] = {}
        for name, prior in priors.items():
            reference = original["results"][name]
            row = {key: route.evaluate(policy, prior, actual, route.TRAIN_LOSS)
                   for key, policy in policies.items()}
            assert all(record["net"] <= reference["exact_query"] + 1e-8 for record in row.values())
            all_results[case][name] = {
                **row,
                "difference_vs_team_return": row["counterfactual"]["net"] - row["team_return"]["net"],
                "difference_vs_independence": row["counterfactual"]["net"] - reference["independent"],
                "optimized_independence": reference["independent"], "exact_optional": reference["exact_query"],
            }
    return {
        "scope": "One paired CPU fit replayed exactly and evaluated under all previously declared anchor and "
                 "stress priors. Both agents' policies were frozen before scoring.",
        "fit_report_sha256": digest(directory / "report.json"), "prior_report_sha256": digest(PRIORS),
        "ordered_gradient_check_max_error_each_agent": check_estimator(),
        "deterministic_refit": True, "cases": all_results,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    print(json.dumps(summarize(args.directory), indent=2))
