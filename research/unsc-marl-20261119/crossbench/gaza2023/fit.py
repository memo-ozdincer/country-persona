"""Fit two local policies against the shared record-evidence reward on one prior."""
import json
from pathlib import Path
import socket

import numpy as np
import torch

import routing

TRAIN = "correlated_development"
SEED = 20231120
UPDATES = 96


def convert(probability):
    return torch.as_tensor(probability, dtype=torch.float64)


def train(prior):
    q_loss, r_loss, q_cost, r_cost = routing.config()
    torch.set_num_threads(1)
    generator = torch.Generator().manual_seed(SEED)
    requester = torch.nn.Parameter(.02 * torch.randn(4, 2, generator=generator, dtype=torch.float64))
    responder = torch.nn.Parameter(.02 * torch.randn(6, 2, 2, generator=generator, dtype=torch.float64))
    optimizer = torch.optim.Adam([requester, responder], lr=.12)
    local = convert(np.eye(4)[routing.PAIR])
    distribution = convert(prior)
    unsent = convert([1, 0])
    rewards = []
    initial = None
    for step in range(UPDATES + 1):
        outgoing = requester.softmax(dim=-1)
        delivered = (1 - q_loss) * outgoing + q_loss * unsent
        reply = responder.softmax(dim=-1)
        match = torch.einsum("ir,iq,rqa,rai->", distribution, delivered, reply, local)
        expected = 42 + 28 * (1 - r_loss) * match - q_cost * (distribution.sum(dim=1) @ outgoing[:, 1]) - r_cost
        rewards.append(float(expected.detach()))
        if step == 0:
            initial = extract(requester, responder)
        if step == UPDATES:
            break
        optimizer.zero_grad()
        (-expected).backward()
        for parameter in (requester, responder):
            assert torch.isfinite(parameter.grad).all()
        optimizer.step()
    return initial, extract(requester, responder), rewards


def extract(requester, responder):
    choices = responder.detach().argmax(dim=-1).numpy()
    return requester.detach().argmax(dim=-1).numpy(), routing.PAIR[np.arange(6)[:, None], choices]


def run():
    baseline_path = routing.HERE / "routing-results.json"
    baseline = json.loads(baseline_path.read_text())
    assert baseline == routing.report()
    priors = dict(routing.priors())
    initial, learned, steps = train(priors[TRAIN])
    trained_ref = baseline["results"][TRAIN]["policies"]
    fixed_scripts = {key: (np.asarray(entry["sender"]), np.asarray(entry["receiver"]))
                     for key, entry in trained_ref.items()}
    results = {}
    for name, prior in priors.items():
        captures = {"initial": initial, "learned": learned,
                    "question_erased": (learned[0], np.repeat(learned[1][:, :1], 2, axis=1)),
                    **{f"train_frozen_{key}": policy for key, policy in fixed_scripts.items()}}
        entries = {key: routing.measure(prior, *policy) for key, policy in captures.items()}
        exact = baseline["results"][name]["policies"]
        assert all(entry["net"] <= exact["exact_interactive"]["net"] + 1e-8 for entry in entries.values())
        results[name] = {"scores": entries,
                         "learned_minus_optimal_priority": entries["learned"]["net"] - exact["independent_priority_by_request"]["net"],
                         "learned_minus_exact_interactive": entries["learned"]["net"] - exact["exact_interactive"]["net"]}
    return {"scope": "Centralized training via the exact expected team reward. At execution each policy uses only its local view. "
                     "Only the declared development prior enters gradients. No language-model weights or source judgments are trained.",
            "host": socket.gethostname(), "device": "CPU", "torch": torch.__version__, "seed": SEED, "updates": UPDATES,
            "training_prior": TRAIN, "routing_sha256": routing.digest(Path(routing.__file__)),
            "fit_sha256": routing.digest(Path(__file__)), "baseline_sha256": routing.digest(baseline_path),
            "expected_training_reward": steps,
            "initial_policy": [table.tolist() for table in initial], "learned_policy": [table.tolist() for table in learned],
            "evaluations": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
