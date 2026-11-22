"""One reward-conditioned MARL fit on synthetic rubrics, replayed on frozen UN cases."""
import json
import os
from itertools import permutations
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np

import source_request_policy as route
import space_transfer_episode as space
from myanmar_protected_transfer import remap_policy

OUT = space.OUT / "rubric-conditioned-routing"
ORDERS = tuple(permutations(range(3)))
SEED = 782311
UPDATES = 320
SYNTHETIC_COUNT = 96
SCALE = 35.


def canonical(values):
    options = []
    for order in ORDERS:
        masks = [sum(1 << order[i] for i in range(3) if m & (1 << i)) for m in route.STATES]
        options.append((tuple(values[masks]), order))
    selected, order = max(options, key=lambda choice: choice[0])
    return np.asarray(selected), order


def training_values():
    rng = np.random.default_rng(SEED)
    seen = set()
    rows = []
    while len(rows) < SYNTHETIC_COUNT:
        weights = tuple(map(int, rng.integers(0, 19, size=3)))
        joint = 7 - (1 << int(rng.integers(3)))
        bonus = int(rng.integers(0, 21))
        values, _ = canonical(route.points({"weights": weights, "joint": (joint, bonus)}))
        key = tuple(values)
        if key not in seen:
            rows.append(values)
            seen.add(key)
    return np.stack(rows)


def fit(train):
    import torch

    torch.manual_seed(SEED)
    torch.set_num_threads(1)
    net = torch.nn.Sequential(torch.nn.Linear(8, 48), torch.nn.Tanh(),
                              torch.nn.Linear(48, 48), torch.nn.Tanh(), torch.nn.Linear(48, 256))
    optimizer = torch.optim.Adam(net.parameters(), lr=.012)
    features = torch.as_tensor(train / SCALE, dtype=torch.float32)
    matrix = torch.as_tensor(np.stack([route.receipt_matrix(v, route.TRAIN_LOSS) for v in train]),
                             dtype=torch.float32)
    prior = torch.as_tensor(route.TEST_PRIORS["uniform"], dtype=torch.float32)
    legal_left = torch.as_tensor(route.JOINT.reshape(8, 16))
    legal_right = torch.as_tensor(route.SEND[:, None, :])
    fees = route.SIGNAL_COST * torch.arange(4).ne(0)
    trace = []
    for _ in range(UPDATES):
        left, right = net(features).chunk(2, dim=-1)
        a = left.reshape(-1, 8, 16).masked_fill(~legal_left, -torch.inf).softmax(-1).reshape(-1, 8, 4, 4)
        b = right.reshape(-1, 8, 4, 4).masked_fill(~legal_right, -torch.inf).softmax(-1)
        observed = (1 - route.TRAIN_LOSS) * b + route.TRAIN_LOSS * b[:, :, :1, :]
        outcome = torch.einsum("plqa,prqb,pab,lr->p", a, observed, matrix, prior)
        cost = torch.einsum("plqa,q,l->p", a, fees, prior.sum(dim=1))
        objective = (outcome - cost).mean()
        assert torch.isfinite(objective)
        optimizer.zero_grad()
        (-objective).backward()
        optimizer.step()
        trace.append(float(objective.detach()))
    return net.eval(), trace


def held_out():
    evidence = space.OUT
    examples = [
        ("unifil", "unifil-final-transfer/verified-transport.json",
         {"weights": (7, 7, 7), "joint": (3, 14)},
         lambda x: [x["bank"][f"team-{m}"]["release_points"] for m in route.STATES]),
        ("outer_space", "space-protected-receipt-bank/compiled.json", space.intended(),
         lambda x: x["compiled_team_points"]),
        ("mali", "mali-protected-writer/score-trusted-citations.json",
         {"weights": (7, 7, 0), "joint": (0, 0)},
         lambda x: [row["release_points"] for row in x["records"]]),
        ("myanmar", "myanmar-sponsorship-probe/score.json",
         {"weights": (7, 7, 7), "joint": (3, 7)}, lambda x: x["revised_points"]),
    ]
    for name, location, rubric, extract in examples:
        path = evidence / location
        actual = np.array(extract(json.loads(path.read_text())), dtype=int)
        assert actual.shape == (8,)
        yield name, space.runner.digest(path), route.points(rubric), actual


def choose(net, values):
    import torch

    scaled, order = canonical(values)
    with torch.inference_mode():
        left, right = net(torch.as_tensor(scaled / SCALE, dtype=torch.float32)).numpy().reshape(2, 8, 4, 4)
    a = np.where(route.JOINT, left, -np.inf).reshape(8, 16).argmax(-1)
    b = np.where(route.SEND[:, None, :], right, -np.inf).argmax(-1)
    return remap_policy((a // 4, a % 4, b), order)


def evaluate(net, train):
    result = {}
    seen = {tuple(row) for row in train}
    for name, checksum, intended, observed in held_out():
        encoded, _ = canonical(intended)
        assert tuple(encoded) not in seen, name
        raw = choose(net, intended)
        assessed = {}
        for prior_name, prior in route.TEST_PRIORS.items():
            matrix = route.receipt_matrix(observed, route.TRAIN_LOSS)
            independent = route.best_silent(prior, matrix)
            bound, examined = route.exact_optional(prior, matrix, route.TRAIN_LOSS)
            policies = {"fit": raw, "independent": independent, "exact_optional": bound,
                        "script": route.scripted()}
            stats = {k: route.evaluate(policy, prior, observed, route.TRAIN_LOSS) for k, policy in policies.items()}
            stats["question_erased"] = route.evaluate(raw, prior, observed, route.TRAIN_LOSS, force_missing=True)
            assert stats["fit"]["net"] <= stats["exact_optional"]["net"] + 1e-9
            assessed[prior_name] = {**stats, "exact_request_maps": examined}
        result[name] = {"source_sha256": checksum, "public_rubric": intended.tolist(),
                        "observed_points": observed.tolist(), "greedy_policy": [p.tolist() for p in raw],
                        "priors": assessed}
    return result


def run():
    import torch

    OUT.mkdir()
    lock = (Path(__file__), Path(route.__file__), Path(space.__file__))
    start = {"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
             "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                      text=True).strip(),
             "command": [sys.executable, *sys.argv], "run_directory": str(OUT.resolve()),
             "seed": SEED, "updates_planned": UPDATES,
             "sha256": {p.name: space.runner.digest(p) for p in lock}}
    (OUT / "launch.json").write_text(json.dumps(start, indent=2) + "\n")
    train = training_values()
    net, trace = fit(train)
    weights = OUT / "weights.pt"
    torch.save(net.state_dict(), weights)
    result = evaluate(net, train)
    report = {"scope": "One synthetic-rubric MARL fit, uniform training inventories. The greedy agents "
                       "select local rows of public-rubric-conditioned tables. Historical dossiers and "
                       "observed bank scores are loaded for evaluation only.",
              "weights_sha256": space.runner.digest(weights),
              "training_rewards": train.tolist(), "updates": len(trace), "training_trace": trace,
              "held_out": result}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    run()
