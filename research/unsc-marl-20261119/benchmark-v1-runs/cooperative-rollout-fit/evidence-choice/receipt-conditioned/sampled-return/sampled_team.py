"""Optimize UN documentary message selection using sampled team reward."""
import argparse
from hashlib import sha256
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from statistics import mean

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[3]
reform_path = RUNS / "reform-2553-transfer" / "transfer.py"
spec = spec_from_file_location("sampled_team_reform", reform_path)
reform = module_from_spec(spec)
spec.loader.exec_module(reform)

receipt = reform.learned
old = receipt.old
SEED = 77242
CHECKPOINTS = (0, 15, 60, 150)


def plan():
    files = [
        Path(__file__), HERE / "protocol.md", Path(receipt.__file__),
        receipt.HERE / "plan.json", receipt.HERE / "results.json",
        Path(old.__file__), Path(receipt.loss.__file__),
        receipt.PARENT / "delivery-aware/results.json",
        Path(reform.__file__), reform.HERE / "plan.json",
        reform.HERE / "results.json", reform.HERE / "docket.json",
    ]
    return {
        "seed": SEED, "checkpoints": CHECKPOINTS,
        "sha256": {str(p.relative_to(RUNS)): old.DIGEST(p) for p in files},
    }


def draw(features, weights, uniform):
    logits = features @ weights
    mass = np.exp(logits - logits.max(axis=1, keepdims=True))
    prob = mass / mass.sum(axis=1, keepdims=True)
    action = (uniform[:, None] >= prob.cumsum(axis=1)[:, :-1]).sum(axis=1)
    gradient = features[np.arange(len(features)), action] - np.einsum("na,naf->nf", prob, features)
    return action, gradient


def train(cases, sees_content):
    rng = np.random.default_rng(SEED)
    _, earlier, third = (np.stack(values) for values in zip(*(x["open"] for x in cases), strict=True))
    views = np.stack([x["adaptive"] if sees_content else
                      np.broadcast_to(x["open"][0], x["adaptive"].shape) for x in cases])
    observation = np.stack([x["observe"] for x in cases])
    masks = np.stack([x["mask_probabilities"].cumsum()[:-1] for x in cases])
    rewards = np.stack([x["returns"] for x in cases])
    indices = np.arange(len(cases))
    weights = np.zeros(len(old.FEATURES))
    trace, digest, baseline = {}, sha256(), 0.
    for step in range(old.UPDATES + 1):
        if step in CHECKPOINTS:
            trace[step] = {"weights": weights.tolist(), "running_baseline": baseline}
        if step == old.UPDATES:
            break
        noise = rng.random((4, len(cases)))
        mask = (noise[0, :, None] >= masks).sum(axis=1)
        b, grad_b = draw(earlier, weights, noise[1])
        c, grad_c = draw(third, weights, noise[2])
        view = observation[indices, b, mask]
        a, grad_a = draw(views[indices, view], weights, noise[3])
        reward = rewards[indices, b, c, mask, a]
        gradient = np.mean((reward - baseline)[:, None] * (grad_a + grad_b + grad_c), axis=0)
        weights += old.RATE * gradient
        baseline = .9 * baseline + .1 * float(reward.mean())
        digest.update(np.column_stack((mask, b, c, view, a, reward)).astype("<i4").tobytes())
    return weights, {"checkpoints": trace, "trajectory_sha256": digest.hexdigest(),
                     "reward_returns": len(cases) * old.UPDATES}


def policies(scene, weights):
    p = {name: receipt.run_policy(scene, w, mode)
         for name, (w, mode) in weights.items()}
    b, c, a = p["sampled_content"]
    fb, fc, fa = p["fixed_content"]
    p["later_fit_only"] = fb, fc, a
    p["earlier_and_third_fit_only"] = b, c, fa
    p["static_ceiling"] = receipt.oracle(scene, False)[1]
    p["content_ceiling"] = receipt.oracle(scene, True)[1]
    return p


def held_row(scene, weights):
    result = {name: receipt.outcome(scene, policy) for name, policy in policies(scene, weights).items()}
    assert max(result.values()) <= result["content_ceiling"] + 1e-9
    for name in ("sampled_open", "sampled_content_without_visibility", "fixed_open", "exact_open"):
        assert result[name] <= result["static_ceiling"] + 1e-9
    return result


def documentary(weights):
    fixed_fit = weights["sampled_content"][0]
    fixed_replay = reform.READ(reform.HERE / "results.json")["orders"]
    rows = []
    for name, order in reform.ORDERS.items():
        _, local, edges, _, true = reform.setup(order)
        for rate, share in reform.product(reform.RATES, reform.SHARES):
            scene = receipt.features(reform.COUNTS, reform.CAPS, local, edges, (rate,) * 3, true)
            original = next(row["outcomes"] for row in fixed_replay[name]["forced_private_inventory"]
                            if row["receipt"] == rate and row["first_card_probability"] == share)
            exact = weights["exact_content"][0]
            arms = {"sampled_content": fixed_fit, "sampled_open": weights["sampled_open"][0], "exact_content": exact}
            comparisons = {arm: reform.test_private(scene, local, edges, share, rate, w, true)
                           for arm, w in arms.items()}
            base = comparisons["sampled_content"]
            for mode in base:
                for ctrl in ("fixed", "oracle"):
                    assert base[mode][ctrl] == original[mode][ctrl]
            trained = {arm: result["none" if arm == "sampled_open" else "content"]["learned"]
                       for arm, result in comparisons.items()}
            trained["sampled_content_without_visibility"] = base["none"]["learned"]
            trained.update({label: base[mode][arm] for label, mode, arm in (
                ("fixed_content", "content", "fixed"), ("fixed_open", "none", "fixed"),
                ("arrival_ceiling", "arrival", "oracle"), ("content_ceiling", "content", "oracle"))})
            rows.append({"order": name, "delivery": rate, "private_prior": share, "policies": trained})
    return rows


def run():
    lock = HERE / "plan.json"
    assert json.loads(lock.read_text()) == json.loads(json.dumps(plan()))
    training = receipt.cases(old.TRAIN_SEED, old.TRAIN_N)
    held = receipt.cases(old.EVAL_SEED, old.EVAL_N)
    content, content_trace = train(training, True)
    opened, open_trace = train(training, False)
    exact, exact_trace = receipt.train(training)
    previous = np.array(json.loads((receipt.PARENT / "delivery-aware/results.json").read_text())["trace"][-1]["weights"])
    fixed = np.array([1., 0., 1.])
    weights = {
        "sampled_content": (content, "adaptive"), "sampled_open": (opened, "open"),
        "sampled_content_without_visibility": (content, "open"),
        "exact_content": (exact, "adaptive"), "exact_open": (previous, "open"),
        "fixed_content": (fixed, "adaptive"), "fixed_open": (fixed, "open"),
    }
    scores = [held_row(x, weights) for x in held]
    transfer = documentary(weights)
    return {
        "plan_sha256": old.DIGEST(lock),
        "training": {"content": content_trace, "open": open_trace, "exact_content": exact_trace},
        "held_mean": {k: mean(x[k] for x in scores) for k in scores[0]}, "held_rows": scores,
        "transfer_mean": {k: mean(row["policies"][k]["released"] for row in transfer)
                          for k in transfer[0]["policies"]}, "transfer_rows": transfer,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
