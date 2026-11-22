"""Fit two-desk request policies on archived guarded records and transfer to UNAMA."""
import argparse
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path

import numpy as np

import facilitator_unama_authority_score as unama
import source_request_policy as route

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parents[1] / "benchmark-kit/evidence"
HELD = HERE / "facilitator-unama-authority-evidence/results.json"
LOSS = route.TRAIN_LOSS
ORDERS = tuple(permutations(range(3)))


def load(path):
    return json.loads(path.read_text())


def training_banks():
    cases = {}
    for family, location in (
        ("outer_space", "space-protected-receipt-bank/score.json"),
        ("unifil", "unifil-final-transfer/verified-transport.json"),
        ("mali", "mali-protected-writer/score-trusted-citations.json"),
        ("myanmar", "myanmar-protected-transfer/score.json"),
        ("climate", "climate2021-language-channel/scores.json"),
    ):
        path = ARCHIVE / location
        source = load(path)
        if "bank" in source:
            rows = [source["bank"][f"team-{mask}"] for mask in range(8)]
            material_key = "raw_points" if "raw_points" in rows[0] else "points"
            material = [row[material_key] for row in rows]
            guarded = [row["release_points"] for row in rows]
        elif family == "mali":
            rows = source["records"]
            assert [row["mask"] for row in rows] == list(range(8))
            material = [row["raw_points"] for row in rows]
            guarded = [row["release_points"] for row in rows]
        elif family == "myanmar":
            rows = source["records"]
            assert [row["mask"] for row in rows] == list(range(8))
            material = guarded = [row["points"] for row in rows]
        else:
            material = source["arms"]["visible"]["raw"]
            guarded = source["arms"]["visible"]["release"]
        assert len(material) == len(guarded) == 8 and all(0 <= g <= p <= 70 for p, g in zip(material, guarded))
        cases[family] = {"path": str(path.relative_to(ARCHIVE)), "sha256": sha256(path.read_bytes()).hexdigest(),
                         "material": material, "guarded": guarded}
    assert sum(case["guarded"] != case["material"] for case in cases.values()) >= 2
    return cases


def calibrated_orders(guarded):
    weights = [guarded[1 << i] for i in range(3)]
    return [p for p in ORDERS if list(weights[i] for i in p) == sorted(weights, reverse=True)]


def training_values(cases, measure):
    # A tied calibration contributes the same total family weight across permutations.
    rows, weights = [], []
    for case in cases.values():
        orders = calibrated_orders(case["guarded"])
        for order in orders:
            points = unama.reordered(case[measure], order)
            rows.append(points - points[0])
            weights.append(1 / (len(cases) * len(orders)))
    return rows, np.asarray(weights)


def fit(cases, measure, independent):
    import torch

    torch.set_num_threads(1)
    rng = torch.Generator().manual_seed(route.SEED)
    payoffs, weights = training_values(cases, measure)
    matrix = torch.as_tensor(np.stack([route.receipt_matrix(row, LOSS) for row in payoffs]))
    masses = torch.as_tensor(weights)
    prior = torch.as_tensor(route.TEST_PRIORS["uniform"])
    left = torch.nn.Parameter(torch.randn((8, 4, 4), generator=rng, dtype=torch.float64) * .04)
    right = torch.nn.Parameter(torch.randn((8, 4, 4), generator=rng, dtype=torch.float64) * .04)
    optim = torch.optim.Adam((left, right), lr=.13)
    joint = route.JOINT.copy()
    if independent:
        joint[:, 1:, :] = False
    legal_left = torch.as_tensor(joint.reshape(8, 16))
    legal_right = torch.as_tensor(route.SEND[:, None, :])
    fee = route.SIGNAL_COST * torch.arange(4).ne(0).to(torch.float64)
    trace = []
    for _ in range(route.UPDATES):
        a = left.flatten(1).masked_fill(~legal_left, -torch.inf).softmax(1).reshape(8, 4, 4)
        b = right.masked_fill(~legal_right, -torch.inf).softmax(2)
        observed = (1 - LOSS) * b + LOSS * b[:, :1, :]
        outcome = torch.einsum("lqa,rqb,pab,lr->p", a, observed, matrix, prior)
        cost = torch.einsum("lqa,q,l->", a, fee, prior.sum(dim=1))
        objective = masses @ outcome - cost
        optim.zero_grad()
        (-objective).backward()
        norms = [float(param.grad.norm()) for param in (left, right)]
        assert np.isfinite([float(objective.detach()), *norms]).all()
        optim.step()
        trace.append({"net_above_public_only": float(objective.detach()), "gradient_norms": norms})
    x = left.detach().flatten(1).masked_fill(~legal_left, -torch.inf).argmax(1).numpy()
    y = right.detach().masked_fill(~legal_right, -torch.inf).argmax(2).numpy()
    return (x // 4, x % 4, y), trace


def surrogate(guarded):
    # Use the empty and singleton receipts. A standalone failure adds no
    # contribution in this baseline, which has no pairwise evidence.
    return np.array([guarded[0] + sum(max(0, guarded[1 << i] - guarded[0])
                                      for i in range(3) if mask & (1 << i)) for mask in range(8)])


def evaluate_case(guarded, fitted, frozen, prior):
    matrix = route.receipt_matrix(guarded, LOSS)
    full_independent = route.best_silent(prior, matrix)
    full_adaptive, count = route.exact_optional(prior, matrix, LOSS)
    prior_matrix = route.receipt_matrix(surrogate(guarded), LOSS)
    partial_independent = route.best_silent(prior, prior_matrix)
    partial_adaptive, _ = route.exact_optional(prior, prior_matrix, LOSS)
    controls = {
        name: route.evaluate(policy, prior, guarded, LOSS)
        for name, policy in (("exact_independent", full_independent), ("exact_adaptive", full_adaptive),
                             ("singleton_independent", partial_independent), ("singleton_adaptive", partial_adaptive))
    }
    rows = {}
    # All priors used here are exchangeable, so receipt-value permutation
    # is equivalent to permuting the same policy into the source index order.
    for order in ORDERS:
        transformed = unama.reordered(guarded, order)
        permitted = order in calibrated_orders(guarded)
        arms = {
            name: route.evaluate(policy, prior, transformed, LOSS, force_missing=erased)
            for name, policy, erased in (("archived", frozen, False), ("fixed_request", route.scripted(), False),
                *((name, policy, False) for name, policy in fitted.items()),
                ("fit_guarded_erased", fitted["fit_guarded"], True))
        }
        assert max(row["net"] for row in arms.values()) <= controls["exact_adaptive"]["net"] + 1e-9
        rows["".join(str(i) for i in order)] = {"calibrated_order": permitted, "arms": arms}
    calibrated = [row["arms"] for row in rows.values() if row["calibrated_order"]]
    means = {name: sum(row[name]["net"] for row in calibrated) / len(calibrated) for name in calibrated[0]}
    selected = [x["arms"]["fit_guarded"]["net"] for x in rows.values()]
    return {"calibrated_means": means, "fit_guarded_all_orders_range": [min(selected), max(selected)],
            "controls": controls, "exact_requester_maps": count, "orders": rows,
            "singleton_only_surrogate": surrogate(guarded).tolist()}


def run():
    fitting = training_banks()
    configs = {
        "fit_material": ("material", False),
        "fit_guarded": ("guarded", False),
        "fit_guarded_independent": ("guarded", True),
    }
    frozen = tuple(np.asarray(load(unama.study.POLICY_ARCHIVE)["training"][name])
                   for name in ("request", "left_delivery", "reply"))
    trained, artifacts = {}, {}
    for name, (objective, independent) in configs.items():
        policy, trace = fit(fitting, objective, independent)
        trained[name] = policy
        artifacts[name] = {"objective": objective, "independent": independent, "trace": trace,
                           "policy": [values.tolist() for values in policy]}
    held = load(HELD)["records"]
    tests = {}
    for writer in ("normalized", "bound"):
        guarded = np.asarray([held[f"{writer}/{mask}"]["guarded_points"] for mask in range(8)])
        tests[writer] = {prior: evaluate_case(guarded, trained, frozen, route.TEST_PRIORS[prior])
                         for prior in ("uniform", "correlated_duplicates")}
    return {"scope": "Matched joint fits on five archived three-field record banks. Slot order uses the three "
                      "guarded singleton calibration scores and tests all ties. UNAMA pair and full scores stay "
                      "out of fitting and policy selection. Exact solvers with full observed scores are hindsight ceilings. "
                      "The held-out inference output is an archived same-assistant-reviewed receipt table.",
            "seed": route.SEED, "updates_per_fit": route.UPDATES, "training_cases": fitting,
            "training": artifacts, "tests": tests,
            "sha256": {path.name: sha256(path.read_bytes()).hexdigest()
                       for path in (Path(__file__), Path(route.__file__), HELD, unama.study.POLICY_ARCHIVE)}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2, ensure_ascii=False))
