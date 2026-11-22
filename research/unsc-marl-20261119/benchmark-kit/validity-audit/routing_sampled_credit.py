"""Compare sampled team returns and action-marginalized credit for evidence routing."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np
import torch

import routing_paired_reward_fit as paired

base, route = paired.base, paired.route
space = base.space
UPDATES, BATCH, SEED = 160, 384, base.SEED + 320
ARMS = ("team_return", "counterfactual")
BATCH_ROWS = torch.arange(BATCH)
ACTIONS = torch.arange(4)
QUERIES = torch.arange(16) // 4
FIRST_FIELDS = torch.arange(16) % 4
BITS = torch.as_tensor(route.BITS)
LEGAL_LEFT = torch.as_tensor(route.JOINT.reshape(8, 16))
LEGAL_RIGHT = torch.as_tensor(route.SEND)


def select(probability, uniform):
    cumulative = probability.cumsum(-1)
    return (uniform.unsqueeze(-1) >= cumulative / cumulative[..., -1:]).sum(-1)


def score_links(payoffs, queries, first, second, keep_first, keep_second):
    receipt = (BITS[first] * keep_first) | (BITS[second] * keep_second)
    attempted = (first != 0).float() + (second != 0).float()
    return payoffs.gather(-1, receipt) - route.SIGNAL_COST * (queries != 0) - route.DELIVERY_COST * attempted


def trial(network, bank, profile, inventory, uniform, keep):
    first_logits, second_logits = network(bank[profile] / base.SCALE).chunk(2, dim=-1)
    first_logits = first_logits.reshape(-1, 8, 16)[BATCH_ROWS, inventory[:, 0]]
    second_logits = second_logits.reshape(-1, 8, 4, 4)[BATCH_ROWS, inventory[:, 1]]
    first = first_logits.masked_fill(~LEGAL_LEFT[inventory[:, 0]], -torch.inf).log_softmax(-1)
    second = second_logits.masked_fill(~LEGAL_RIGHT[inventory[:, 1], None, :], -torch.inf).log_softmax(-1)
    with torch.no_grad():
        probabilities = first.exp(), second.exp()
        left = select(probabilities[0], uniform[:, 0])
        # Reuse a random draw across all possible received questions. Its marginal
        # distribution is the correct policy action distribution in every branch.
        right_by_question = select(probabilities[1], uniform[:, 1, None].expand(-1, 4))
        question_arrivals = QUERIES[None, :] * keep[:, 0, None]
        received = question_arrivals[BATCH_ROWS, left]
        right = right_by_question[BATCH_ROWS, received]
        payoffs = bank[profile]
        left_alternatives = score_links(payoffs, QUERIES[None, :], FIRST_FIELDS[None, :],
                                        right_by_question.gather(1, question_arrivals),
                                        keep[:, 1, None], keep[:, 2, None])
        right_alternatives = score_links(payoffs, QUERIES[left, None], FIRST_FIELDS[left, None],
                                         ACTIONS[None, :], keep[:, 1, None], keep[:, 2, None])
        reward = left_alternatives[BATCH_ROWS, left]
        assert torch.equal(reward, right_alternatives[BATCH_ROWS, right])
        action_means = torch.stack(((probabilities[0] * left_alternatives).sum(-1),
                                    (probabilities[1][BATCH_ROWS, received] * right_alternatives).sum(-1)), dim=1)
    log_choice = torch.stack((first[BATCH_ROWS, left], second[BATCH_ROWS, received, right]), dim=1)
    return log_choice, reward, action_means


def objective(network, fields, matrix, normalization):
    with torch.inference_mode():
        first, second = network(fields).chunk(2, dim=-1)
        a = first.reshape(-1, 8, 16).masked_fill(~LEGAL_LEFT, -torch.inf).softmax(-1).reshape(-1, 8, 4, 4)
        b = second.reshape(-1, 8, 4, 4).masked_fill(~LEGAL_RIGHT[:, None, :], -torch.inf).softmax(-1)
        available = (1 - route.TRAIN_LOSS) * b + route.TRAIN_LOSS * b[:, :, :1]
        proceeds = torch.einsum("plqa,prqb,pab->p", a, available, matrix) / 64
        cost = route.SIGNAL_COST * a[:, :, 1:].sum(dim=(1, 2, 3)) / 8
        return float(((proceeds - cost) / normalization).mean())


def fit(train):
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    generator = torch.Generator().manual_seed(SEED + 1)
    original = paired.contrasts.make_net()
    teams = {key: paired.contrasts.make_net() for key in ARMS}
    for net in teams.values():
        net.load_state_dict(original.state_dict())
    optim = {key: torch.optim.Adam(net.parameters(), lr=.012) for key, net in teams.items()}
    bank = torch.as_tensor(train, dtype=torch.float32)
    norm = torch.maximum(bank[:, -1], torch.tensor(.25))
    matrix = torch.tensor(np.stack([route.receipt_matrix(v, route.TRAIN_LOSS) for v in train]), dtype=bank.dtype)
    fields = bank / base.SCALE
    trace = []
    # The global-reward arm uses profile-specific running means from past episodes.
    running_mean = torch.zeros(len(bank))
    advantage_rms = {key: 0. for key in ARMS}
    for step in range(UPDATES):
        profile = torch.randint(len(bank), (BATCH,), generator=generator)
        inventory = torch.randint(8, (BATCH, 2), generator=generator)
        uniform = torch.rand(BATCH, 2, generator=generator)
        keep = torch.rand(BATCH, 3, generator=generator) >= route.TRAIN_LOSS
        for name, net in teams.items():
            log_choice, reward, counterfactual = trial(net, bank, profile, inventory, uniform, keep)
            baseline = running_mean[profile, None] if name == "team_return" else counterfactual
            advantage = (reward[:, None] - baseline) / norm[profile, None]
            advantage_rms[name] += float(advantage.square().mean())
            loss = -(advantage * log_choice).sum(1).mean()
            assert torch.isfinite(loss)
            optim[name].zero_grad()
            loss.backward()
            assert all(torch.isfinite(p.grad).all() for p in net.parameters())
            optim[name].step()
            if name == "team_return":
                sums = torch.zeros(len(bank)).scatter_add_(0, profile, reward)
                counts = profile.bincount(minlength=len(bank))
                seen = counts > 0
                running_mean[seen] = .93 * running_mean[seen] + .07 * (sums[seen] / counts[seen])
        if (step + 1) % 40 == 0:
            trace.append({"update": step + 1, "normalized_exact": {
                name: objective(net, fields, matrix, norm) for name, net in teams.items()}})
    return {name: net.eval() for name, net in teams.items()}, trace, {
        key: (value / UPDATES) ** .5 for key, value in advantage_rms.items()
    }


def evaluate(teams):
    cases = {}
    prior = route.TEST_PRIORS["uniform"]
    for case, sha, announced, actual in base.held_out():
        entries = {}
        for name, net in teams.items():
            policy = base.choose(net, announced)
            entries[name] = {
                "policy": [a.tolist() for a in policy],
                "net": route.evaluate(policy, prior, actual, route.TRAIN_LOSS),
                "erased": route.evaluate(policy, prior, actual, route.TRAIN_LOSS, force_missing=True),
            }
        silent = route.best_silent(prior, route.receipt_matrix(actual, route.TRAIN_LOSS))
        entries["exact_independence"] = route.evaluate(silent, prior, actual, route.TRAIN_LOSS)
        entries["source_sha256"] = sha
        cases[case] = entries
    return cases


def run(directory):
    directory.mkdir()
    launch = {"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU",
              "gpu_uuids": [], "seed": SEED, "updates_each": UPDATES, "command": [sys.executable, *sys.argv],
              "run_directory": str(directory.resolve()), "torch": torch.__version__,
              "code_sha256": {Path(file).name: space.runner.digest(Path(file)) for file in
                              (__file__, paired.__file__, base.__file__, route.__file__)},
              }
    launch["process_start"] = subprocess.check_output(
        ["ps", "-o", "lstart=", "-p", str(launch["pid"])], text=True).strip()
    (directory / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    train = paired.curriculum()
    teams, trace, scale = fit(train)
    checksums = {}
    for name, net in teams.items():
        path = directory / f"{name}.pt"
        torch.save(net.state_dict(), path)
        checksums[name] = space.runner.digest(path)
    report = {
        "scope": "Paired sampled centralized training of decentralized sender and responder. Training profiles "
                 "and local inventories are simulated, while evaluation reuses measured UN record banks. "
                 "The estimator uses exact model access to the short training environment.",
        "seed": SEED, "batch": BATCH, "updates_each": UPDATES, "training_profiles": train.tolist(),
        "advantage_rms": scale, "training_checkpoints": trace, "weights_sha256": checksums,
        "historical_replay": evaluate(teams),
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    run(args.directory)
