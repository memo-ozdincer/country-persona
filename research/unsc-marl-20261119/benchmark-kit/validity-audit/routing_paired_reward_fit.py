"""Train on matched changes in target dependencies and communication stakes."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np

import routing_reward_contrasts as contrasts

base, route = contrasts.base, contrasts.route
OUT = base.space.OUT / "routing-paired-reward-fit"


def curriculum():
    rng = np.random.default_rng(base.SEED + 1)
    bank = []
    for _ in range(24):
        weights = tuple(sorted(map(int, rng.choice(np.arange(3, 19), size=3, replace=False)), reverse=True))
        bonus = float(rng.uniform(5, 20))
        scale = float(rng.uniform(.001, .048))
        values = [route.points({"weights": weights, "joint": (m, bonus)}) for m in (3, 6)]
        bank.extend([*values, *(v * scale for v in values)])
    matrix = np.stack(bank)
    assert matrix.shape == (96, 8)
    held = [*contrasts.rewards().values(), *(base.canonical(x[2])[0] for x in base.held_out())]
    assert not any(np.array_equal(x, y) for x in held for y in matrix)
    return matrix


def fit(train):
    import torch

    torch.manual_seed(base.SEED)
    torch.set_num_threads(1)
    net = contrasts.make_net()
    optimizer = torch.optim.Adam(net.parameters(), lr=.012)
    features = torch.as_tensor(train / base.SCALE, dtype=torch.float32)
    matrices = torch.as_tensor(np.stack([route.receipt_matrix(v, route.TRAIN_LOSS) for v in train]),
                               dtype=torch.float32)
    normalization = torch.as_tensor(np.maximum(train[:, -1], .25), dtype=torch.float32)
    prior = torch.as_tensor(route.TEST_PRIORS["uniform"], dtype=torch.float32)
    legal_left = torch.as_tensor(route.JOINT.reshape(8, 16))
    legal_right = torch.as_tensor(route.SEND[:, None, :])
    fees = route.SIGNAL_COST * torch.arange(4).ne(0)
    trace = []
    for _ in range(base.UPDATES):
        left, right = net(features).chunk(2, dim=-1)
        a = left.reshape(-1, 8, 16).masked_fill(~legal_left, -torch.inf).softmax(-1).reshape(-1, 8, 4, 4)
        b = right.reshape(-1, 8, 4, 4).masked_fill(~legal_right, -torch.inf).softmax(-1)
        observed = (1 - route.TRAIN_LOSS) * b + route.TRAIN_LOSS * b[:, :, :1, :]
        proceeds = torch.einsum("plqa,prqb,pab,lr->p", a, observed, matrices, prior)
        costs = torch.einsum("plqa,q,l->p", a, fees, prior.sum(dim=1))
        margin = proceeds - costs
        utility = margin / normalization
        expected = utility.mean()
        assert torch.isfinite(expected)
        optimizer.zero_grad()
        (-expected).backward()
        optimizer.step()
        trace.append({"normalized": float(expected.detach()), "high_net": float(margin[torch.arange(len(train)) % 4 < 2].mean().detach()),
                      "low_net": float(margin[torch.arange(len(train)) % 4 >= 2].mean().detach())})
    return net.eval(), trace


def evaluate(net, train, baseline):
    results = {}
    reference = base.choose(net, train.mean(axis=0))
    for name, value in contrasts.rewards().items():
        selected = base.choose(net, value)
        priors = {}
        for prior_name, prior in route.TEST_PRIORS.items():
            backed = baseline["profile"][name]["priors"][prior_name]
            measured = {"revised": contrasts.measure(selected, value, prior),
                        "constant_input": contrasts.measure(reference, value, prior),
                        "erase_question": route.evaluate(selected, prior, value, route.TRAIN_LOSS, force_missing=True)}
            assert max(v["net"] for v in measured.values()) <= backed["exact_query"]["net"] + 1e-9
            priors[prior_name] = {**measured, "frozen": backed["frozen"]["net"], "ceiling": backed["exact_query"]["net"],
                                  "independent": backed["independent"]["net"]}
        results[name] = {"policy": [a.tolist() for a in selected], "priors": priors}
    return results


def main():
    import torch

    OUT.mkdir()
    code = (Path(__file__), Path(base.__file__), Path(route.__file__), Path(contrasts.__file__))
    meta = {"host": socket.gethostname(), "pid": os.getpid(),
            "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                     text=True).strip(),
            "device": "CPU", "gpu_uuids": [], "command": [sys.executable, *sys.argv],
            "run_directory": str(OUT.resolve()), "planned_updates": base.UPDATES, "seed": base.SEED,
            "sha256": {p.name: base.space.runner.digest(p) for p in code}}
    (OUT / "launch.json").write_text(json.dumps(meta, indent=2) + "\n")
    train = curriculum()
    net, trace = fit(train)
    weights = OUT / "weights.pt"
    torch.save(net.state_dict(), weights)
    panel = contrasts.OUT / "panel.json"
    baseline = json.loads(panel.read_text())
    result = {"scope": "One synthetic paired-rubric fit. Public profile input, uniform training inventories, "
                       "and unchanged message mechanics. Both the sample mix and per-profile reward normalization "
                       "differ from the earlier fit. Historical reward banks supply evaluation only.",
              "profile_bank": train.tolist(), "updates": len(trace), "training_trace": trace,
              "panel_sha256": base.space.runner.digest(panel), "weights_sha256": base.space.runner.digest(weights),
              "contrast_outcomes": evaluate(net, train, baseline),
              "historical_replay": base.evaluate(net, train)}
    (OUT / "report.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
