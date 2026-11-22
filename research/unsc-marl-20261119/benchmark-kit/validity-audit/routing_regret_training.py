"""Train prior-blind routing against the weakest inventory groups."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np
import torch

import routing_sampled_credit as sampled

base, route, paired = sampled.base, sampled.route, sampled.paired
digest = sampled.space.runner.digest
ROOT = sampled.space.OUT
PREVIOUS = ROOT / "routing-sampled-credit"
PRIORS = ROOT / "routing-prior-robustness/report.json"
TEMPERATURE = .025
GROUP_ARMS = ("mean", "worst_group")


def training_priors():
    uniform = route.TEST_PRIORS["uniform"]
    first = route.product_prior((.76, .27, .58), (.32, .73, .41))
    second = route.product_prior((.38, .68, .81), (.65, .44, .24))
    duplicate_mix = .35 * np.eye(8) / 8 + .65 * uniform
    complement_mix = .42 * np.eye(8)[:, ::-1] / 8 + .58 * uniform
    priors = np.stack([uniform, first, first.T, second, second.T, duplicate_mix, complement_mix])
    assert np.all(priors >= 0) and np.allclose(priors.sum(axis=(1, 2)), 1)
    return priors


def tensors(training, priors):
    bank = torch.as_tensor(training, dtype=torch.float32)
    scale = torch.maximum(bank[:, -1], torch.tensor(.25))
    matrix = np.stack([route.receipt_matrix(p, route.TRAIN_LOSS) for p in training])
    reference = []
    for prior in priors:
        values = []
        for reward in matrix:
            _, send, reply = route.best_silent(prior, reward)
            per_world = reward[send[:, None], reply[None, :, 0]]
            values.append((prior * per_world).sum())
        reference.append(values)
    return bank, scale, torch.tensor(matrix, dtype=bank.dtype), torch.tensor(reference, dtype=bank.dtype)


def group_objectives(network, bank, scale, matrix, priors, independent):
    with torch.inference_mode():
        raw_a, raw_b = network(bank / base.SCALE).chunk(2, dim=-1)
        a = raw_a.reshape(-1, 8, 16).masked_fill(~sampled.LEGAL_LEFT, -torch.inf).softmax(-1)
        a = a.reshape(-1, 8, 4, 4)
        b = raw_b.reshape(-1, 8, 4, 4).masked_fill(~sampled.LEGAL_RIGHT[:, None, :], -torch.inf).softmax(-1)
        observed = (1 - route.TRAIN_LOSS) * b + route.TRAIN_LOSS * b[:, :, :1]
        world_returns = torch.einsum("plqa,prqb,pab->plr", a, observed, matrix)
        world_returns -= route.SIGNAL_COST * a[:, :, 1:].sum(dim=(2, 3)).unsqueeze(-1)
        values = torch.einsum("plr,glr->gp", world_returns, priors)
        return ((values - independent) / scale).mean(dim=1)


def fit(training, priors):
    torch.set_num_threads(1)
    torch.manual_seed(sampled.SEED)
    generator = torch.Generator().manual_seed(sampled.SEED + 1)
    initial = paired.contrasts.make_net()
    networks = {name: paired.contrasts.make_net() for name in GROUP_ARMS}
    for net in networks.values():
        net.load_state_dict(initial.state_dict())
    optimizers = {name: torch.optim.Adam(net.parameters(), lr=.012) for name, net in networks.items()}
    bank, scale, matrix, independent = tensors(training, priors)
    priors = torch.as_tensor(priors, dtype=torch.float32)
    groups = torch.arange(sampled.BATCH) % len(priors)
    group_size = groups.bincount()[groups]
    distribution = priors[groups].reshape(sampled.BATCH, 64)
    weights = {name: torch.full((len(priors),), 1 / len(priors)) for name in GROUP_ARMS}
    snapshots = []

    def record(update):
        row = {name: group_objectives(net, bank, scale, matrix, priors, independent).tolist()
               for name, net in networks.items()}
        snapshots.append({"update": update, "normalized_gain_over_independence": row,
                          "weights": {name: weight.tolist() for name, weight in weights.items()}})

    record(0)
    for step in range(sampled.UPDATES):
        profile = torch.randint(len(bank), (sampled.BATCH,), generator=generator)
        world = sampled.select(distribution, torch.rand(sampled.BATCH, generator=generator))
        views = torch.stack((world // 8, world % 8), dim=1)
        uniforms = torch.rand(sampled.BATCH, 2, generator=generator)
        links = torch.rand(sampled.BATCH, 3, generator=generator) >= route.TRAIN_LOSS
        for name, net in networks.items():
            log_choice, reward, localized = sampled.trial(net, bank, profile, views, uniforms, links)
            advantage = (reward[:, None] - localized) / scale[profile, None]
            loss = -((advantage * log_choice).sum(dim=1) * weights[name][groups] / group_size).sum()
            assert torch.isfinite(loss)
            optimizers[name].zero_grad()
            loss.backward()
            assert all(torch.isfinite(p.grad).all() for p in net.parameters())
            optimizers[name].step()
        if (step + 1) % 8 == 0:
            gaps = group_objectives(networks["worst_group"], bank, scale, matrix, priors, independent)
            weights["worst_group"] = (-gaps / TEMPERATURE).softmax(dim=0)
        if (step + 1) % 40 == 0:
            record(step + 1)
    return networks, snapshots


def evaluate(networks, archive, old):
    priors = {key: np.asarray(value) for group in ("prior_anchors", "prior_stress")
              for key, value in archive[group].items()}
    matrix = training_priors()
    assert all(not any(np.array_equal(p, t) for t in matrix[1:]) for p in priors.values())
    historical = {}
    for case, checksum, intended, realized in base.held_out():
        anchor = archive["historical"][case]
        old_case = old["historical_replay"][case]
        assert checksum == old_case["source_sha256"] == anchor["source_sha256"]
        policies = {name: base.choose(net.eval(), intended) for name, net in networks.items()}
        policies["uniform_training"] = base.space.as_policy(old_case["counterfactual"]["policy"])
        cases = {}
        for name, prior in priors.items():
            existing = anchor["results"][name]
            independence = existing["independent"]
            results = {}
            for arm, policy in policies.items():
                current = route.evaluate(policy, prior, realized, route.TRAIN_LOSS)
                erased = route.evaluate(policy, prior, realized, route.TRAIN_LOSS, force_missing=True)
                assert current["net"] <= existing["exact_query"] + 1e-9
                results[arm] = {
                    "net": current["net"], "new_value_vs_independence": current["net"] - independence,
                    "request_value_vs_erasure": current["net"] - erased["net"], "requests": current["requests"],
                }
            cases[name] = {"optimized_independence": independence, "exact_optional": existing["exact_query"],
                           "arms": results}
        historical[case] = {"source_sha256": checksum, "policies": {
            arm: [row.tolist() for row in policy] for arm, policy in policies.items()}, "priors": cases}
    return historical


def run(directory):
    directory.mkdir()
    script = Path(__file__).resolve()
    meta = {"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
            "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                     text=True).strip(),
            "command": [sys.executable, *sys.argv], "run_directory": str(directory.resolve()),
            "seed": sampled.SEED, "updates_per_arm": sampled.UPDATES,
            "locks": {p.name: digest(p) for p in (script, Path(sampled.__file__), Path(route.__file__),
                                                   Path(paired.__file__), Path(base.__file__), PRIORS,
                                                   PREVIOUS / "report.json")}}
    (directory / "launch.json").write_text(json.dumps(meta, indent=2) + "\n")
    training = paired.curriculum()
    priors = training_priors()
    networks, checkpoints = fit(training, priors)
    files = {name: directory / f"{name}.pt" for name in networks}
    for name, net in networks.items():
        torch.save(net.state_dict(), files[name])
    report = {
        "scope": "Matched counterfactual estimates on the same hidden synthetic training priors. "
                 "The mean arm uses equal group weights. The other weights groups by soft minimum of "
                 "mean normalized exact gain above group-informed optimized independence. At deployment no "
                 "inventory distribution is supplied. All measured historical record banks are used for scoring only.",
        "temperature": TEMPERATURE, "train_priors": priors.tolist(), "training_profiles": training.tolist(),
        "training_checkpoints": checkpoints, "weight_sha256": {name: digest(path) for name, path in files.items()},
        "historical_replay": evaluate(networks, json.loads(PRIORS.read_text()),
                                      json.loads((PREVIOUS / "report.json").read_text())),
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    run(cli.parse_args().directory)
