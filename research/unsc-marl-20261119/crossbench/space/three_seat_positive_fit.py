"""Fit disclosure on four positive controls and replay four reserved grids."""
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

import three_seat_positive as suite

HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "evidence/three-seat-positive.json"
shared = suite.shared
base = shared.base


def fixture(entry):
    return (tuple(entry["packages"]), tuple(map(tuple, entry["cards_a"])),
            tuple(map(tuple, entry["cards_b"])), tuple(entry["public"]))


def data_for(grid):
    result = shared.Experiment(grid, True)
    # The chair has no active follow-up at this endpoint.
    for state, role in enumerate(result.roles):
        if role == 2:
            result.mask[state, 1:] = False
    return result


def learn(data):
    weights = torch.zeros((3, shared.FEATURES), dtype=torch.float64, requires_grad=True)
    optimizer = torch.optim.Adam([weights], lr=.08)
    paths = [torch.as_tensor(d.path_ids) for d in data]
    returns = [torch.as_tensor(d.mass * (d.outcomes[:, 1] - d.outcomes[:, 0])) for d in data]
    trace = []
    for step in range(base.STEPS + 1):
        values = []
        for d, indices, reward in zip(data, paths, returns, strict=True):
            p = torch.cat((d.probabilities(weights).flatten(), weights.new_ones(1)))
            values.append((p[indices].prod(dim=1) * reward).sum())
        mean = torch.stack(values).mean()
        if step in (0, 30, 90, base.STEPS):
            trace.append({"step": step, "mean_net": float(mean.detach())})
        if step < base.STEPS:
            optimizer.zero_grad()
            (-mean).backward()
            optimizer.step()
    return weights.detach(), trace


def exact_policy(data, recorded):
    weights = np.zeros((len(data.states), shared.MAX_ACTIONS))
    for state, index in data.states.items():
        role = state[0]
        if role == "A":
            choice = recorded["first_actions"][state[1]]
        elif role == "B":
            choice = recorded["second_actions"][state[1]][suite.RECEIPTS.index(state[2])]
        else:
            choice = 0
        weights[index, choice] = 1.
    return data.metrics(weights)


def evaluate(data, weights):
    policy = data.probabilities(weights).numpy()
    erased = policy.copy()
    for key, row in data.states.items():
        if key[0] == "B" and key[2] is not None:
            erased[row] = policy[data.states["B", key[1], None]]
    return {"fitted": data.metrics(policy), "same_policy_peer_erased": data.metrics(erased),
            "initialized": data.metrics(data.probabilities(torch.zeros_like(weights)).numpy())}


def targets(rows, selected, weights):
    reports = []
    for item in selected:
        entry = rows[item]
        with patch.dict(shared.FIXTURES, {"target": fixture(entry)}):
            d = data_for(shared.Grid("target"))
            dials = evaluate(d, weights)
            for mode in ("peer", "independent"):
                dials[f"exact_{mode}"] = exact_policy(d, entry[mode])
                assert abs(dials[f"exact_{mode}"]["net"] - entry[mode]["net"]) < 1e-9
            errors = []
            for perm in permutations(range(3)):
                alias = evaluate(data_for(shared.Grid("target", perm)), weights)
                errors.append(abs(alias["fitted"]["net"] - dials["fitted"]["net"]))
            assert max(errors) < 1e-9
            reports.append({"grid_id": item, "max_order_deviation": max(errors), "results": dials})
    return reports


def run():
    torch.set_num_threads(1)
    registry = json.loads(REGISTRY.read_text())
    index = {r["draw"]: r for r in registry["accepted"]}
    fit, reserved = (registry["partition"][k] for k in ("fit", "reserved"))
    assert len(fit) == len(reserved) == 4 and not set(fit) & set(reserved)
    training = []
    for item in fit:
        with patch.dict(shared.FIXTURES, {"target": fixture(index[item])}):
            training.append(data_for(shared.Grid("target")))
    weights, trace = learn(training)
    fit_replay = targets(index, fit, weights)
    assert abs(trace[-1]["mean_net"] - np.mean([item["results"]["fitted"]["net"]
                                                 for item in fit_replay])) < 1e-9
    return {"scope": "One feature-policy fit on four capacity-screened fictional outer-space variants. "
                     "Four reserved variants are evaluated only after fitting. All selections are truthful "
                     "single-grade evidence, under balanced world priors and no chair request.",
            "registry_sha256": sha256(REGISTRY.read_bytes()).hexdigest(), "training": trace,
            "fit": fit_replay, "reserved": targets(index, reserved, weights), "weights": weights.tolist()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
