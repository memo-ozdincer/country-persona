"""Test a capped learned residual around the public-information team."""
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

import three_seat_transfer as transfer

HERE = Path(__file__).resolve().parent
REGISTRATION = HERE / "three_seat_residual_cases.json"
BASELINE = HERE / "evidence/three-seat-transfer.json"
EXPLORATION = .15
RESIDUAL_SHARE = .35
LOGIT_LIMIT = 3.


def public_team(data):
    policy = data.public_emitters("information", False)
    for i, role in enumerate(data.roles):
        if role != 2:
            continue
        scores = np.array([f[0] - transfer.protocol.FEE * f[1] for f in data.features[i]])
        winners = np.flatnonzero(scores.max() - scores <= 1e-12)
        policy[i] = 0
        policy[i, winners] = 1. / len(winners)
    return policy


class Residual:
    def __init__(self, data):
        self.data = data
        self.core = torch.as_tensor(public_team(data))
        uniform = data.mask / data.mask.sum(dim=-1, keepdim=True)
        warm = (1 - EXPLORATION) * self.core + EXPLORATION * uniform
        self.offset = warm.log()

    def policy(self, weights):
        logits = (self.data.arrays * weights[self.data.role_ids].unsqueeze(1)).sum(-1)
        changed = (self.offset + LOGIT_LIMIT * (logits / LOGIT_LIMIT).tanh()).softmax(-1)
        return (1 - RESIDUAL_SHARE) * self.core + RESIDUAL_SHARE * changed


def fit(data):
    model = Residual(data)
    params = torch.zeros((3, transfer.FEATURES), dtype=torch.float64, requires_grad=True)
    optimizer = torch.optim.Adam([params], lr=.08)
    domain = torch.as_tensor(data.path_ids)
    values = torch.as_tensor(data.mass * (data.outcomes[:, 1] - data.outcomes[:, 0]))
    history = []
    for step in range(transfer.base.STEPS + 1):
        policy = torch.cat((model.policy(params).flatten(), params.new_ones(1)))
        reward = (policy[domain].prod(dim=1) * values).sum()
        if step in (0, 30, 90, transfer.base.STEPS):
            history.append({"step": step, "expected_net": float(reward.detach())})
        if step < transfer.base.STEPS:
            optimizer.zero_grad()
            (-reward).backward()
            optimizer.step()
    return params.detach(), history


def evaluate(grid, weights, old, balanced=False):
    data = transfer.Experiment(grid, balanced)
    model = Residual(data)
    anchored = model.policy(weights).numpy()
    control = model.core.numpy()
    original = data.probabilities(old).numpy()
    opening_swap = control.copy()
    chair_swap = control.copy()
    for i, role in enumerate(data.roles):
        if role == 2:
            chair_swap[i] = anchored[i]
        else:
            opening_swap[i] = anchored[i]
    routes = {
        "script": control, "old_learned": original, "anchored_learned": anchored,
        "anchored_initial": model.policy(torch.zeros_like(weights)).numpy(),
        "learned_openings_only": opening_swap, "learned_chair_only": chair_swap,
    }
    for policy in routes.values():
        assert np.allclose(policy.sum(axis=-1), 1.)
        assert (policy[~data.mask.numpy()] == 0).all()
    assert (anchored + 1.e-12 >= (1 - RESIDUAL_SHARE) * control).all()
    return {name: data.metrics(policy) for name, policy in routes.items()}


def fixture_cases():
    raw = json.loads(REGISTRATION.read_text())
    assert raw["train"] == "space"
    fixtures = {}
    for name, case in raw["targets"].items():
        a, b = (tuple(map(tuple, case[key])) for key in ("cards_a", "cards_b"))
        menu = tuple(case["packages"])
        public = tuple(case["public"])
        assert all(len(card) == 3 for card in (*a, *b, public))
        assert all(x in range(4) for card in (*a, *b, public) for x in card)
        assert len(set(a)) == len(a) and len(set(b)) == len(b)
        fixtures[name] = menu, a, b, public
    return fixtures


def source_menu(name, packages):
    if name == "climate":
        path = HERE.parents[1] / "families.json"
        titles = json.loads(path.read_text())[name]["options"]
        options = dict(zip(packages, titles, strict=True))
    else:
        path = HERE.parent / name / "case.json"
        data = json.loads(path.read_text())
        options = {row["id"]: row for row in data["options"] if row["id"] in packages}
    assert set(options) == set(packages)
    return options, sha256(path.read_bytes()).hexdigest()


def run():
    torch.set_num_threads(1)
    old = torch.as_tensor(json.loads(BASELINE.read_text())["shared_weights"], dtype=torch.float64)
    training = transfer.Experiment(transfer.Grid("space"), True)
    # Target data is used only below this completed fit.
    params, history = fit(training)
    cases = fixture_cases()
    with patch.dict(transfer.FIXTURES, cases):
        calibrated = evaluate(transfer.Grid("space"), params, old, True)
        assert abs(calibrated["anchored_learned"]["net"] - history[-1]["expected_net"]) < 1e-9
        output = {}
        for name in (*transfer.NEW_GRIDS, *cases):
            grid = transfer.Grid(name)
            measured = evaluate(grid, params, old)
            alias_checks = []
            for order in permutations(range(3)):
                held = evaluate(transfer.Grid(name, order), params, old)
                changes = {policy: abs(values["net"] - held[policy]["net"])
                           for policy, values in measured.items()}
                assert max(changes.values()) < 1e-9
                alias_checks.append({"order": order, "max_net_delta": max(changes.values())})
            options, digest = source_menu(name, grid.packages)
            output[name] = {
                "type": "new_held_out_grid" if name in cases else "previously_evaluated_grid",
                "packages": options, "source_sha256": digest,
                "world_counts": {"all": len(grid.worlds),
                                 "impasse": sum("impasse" in grid.winners(w) for w in grid.worlds),
                                 "ties": sum(len(grid.winners(w)) > 1 for w in grid.worlds)},
                "scores": measured, "package_order_checks": alias_checks,
            }
    return {
        "scope": "One exact residual fit on the original space workshop; two new fictional target grids "
                 "are evaluated after training alongside the exposed Mali and Myanmar grids. "
                 "The fixed public-information policies receive the same evidence and costs.",
        "training": history, "training_scores": calibrated,
        "historical_case_registry_sha256": sha256(REGISTRATION.read_bytes()).hexdigest(),
        "interpolation_share": RESIDUAL_SHARE, "exploration_prior": EXPLORATION,
        "logit_bound": LOGIT_LIMIT, "weights": params.tolist(), "targets": output,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
