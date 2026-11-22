"""Fit a separate listener residual from a terminal shared documentary score."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import sampled_team as original

receipt, old, reform = original.receipt, original.old, original.reform
FRESH_SEED = 7724301
FRESH_COUNT = 96
FIXED = np.array([1., 0., 1.])


def plan():
    pins = (Path(__file__), HERE / "protocol.md", HERE.parent / "plan.json",
            HERE.parent / "results.json", Path(original.__file__), Path(reform.__file__),
            reform.HERE / "docket.json")
    return {"fresh_seed": FRESH_SEED, "fresh_count": FRESH_COUNT,
            "training_seed": original.SEED, "updates": old.UPDATES,
            "sha256": {str(p.relative_to(original.RUNS)): old.DIGEST(p) for p in pins}}


def fit(cases, residual_rate):
    rng = np.random.default_rng(original.SEED)
    _, earlier, third = (np.stack(features) for features in zip(*(x["open"] for x in cases), strict=True))
    later = np.stack([x["adaptive"] for x in cases])
    observation = np.stack([x["observe"] for x in cases])
    masks = np.stack([x["mask_probabilities"].cumsum()[:-1] for x in cases])
    reward_table = np.stack([x["returns"] for x in cases])
    indices = np.arange(len(cases))
    base = np.zeros(len(old.FEATURES))
    residual = np.zeros_like(base)
    trace, digest, baseline = {}, sha256(), 0.
    for step in range(old.UPDATES + 1):
        if step in original.CHECKPOINTS:
            trace[str(step)] = {"weights": base.tolist(), "listener_residual": residual.tolist(),
                                "running_baseline": baseline}
        if step == old.UPDATES:
            break
        noise = rng.random((4, len(cases)))
        mask = (noise[0, :, None] >= masks).sum(axis=1)
        b, grad_b = original.draw(earlier, base, noise[1])
        c, grad_c = original.draw(third, base, noise[2])
        view = observation[indices, b, mask]
        a, grad_a = original.draw(later[indices, view], base + residual, noise[3])
        scores = reward_table[indices, b, c, mask, a]
        advantage = (scores - baseline)[:, None]
        base += old.RATE * np.mean(advantage * (grad_a + grad_b + grad_c), axis=0)
        residual += residual_rate * np.mean(advantage * grad_a, axis=0)
        baseline = .9 * baseline + .1 * float(scores.mean())
        digest.update(np.column_stack((mask, b, c, view, a, scores)).astype("<i4").tobytes())
    return (base, base + residual), {"checkpoints": trace, "trajectory_sha256": digest.hexdigest(),
                                     "reward_returns": len(cases) * old.UPDATES}


def arms(shared, fit_weights):
    team, listener = fit_weights
    return {"shared": (shared, shared, "adaptive"), "listener_residual": (team, listener, "adaptive"),
            "without_content": (team, listener, "open"), "fixed": (FIXED, FIXED, "adaptive"),
            "swap_listener": (shared, listener, "adaptive"), "swap_other_desks": (team, shared, "adaptive")}


def dispatch(scene, configurations):
    output = {}
    for arm, (team, listener, mode) in configurations.items():
        b, c, _ = receipt.run_policy(scene, team, mode)
        _, _, a = receipt.run_policy(scene, listener, mode)
        output[arm] = receipt.outcome(scene, (b, c, a))
    output.update(content_ceiling=receipt.oracle(scene, True)[0], static_ceiling=receipt.oracle(scene, False)[0])
    assert max(output.values()) <= output["content_ceiling"] + 1e-9
    assert output["without_content"] <= output["static_ceiling"] + 1e-9
    return output


def archive(configurations, previous):
    rows = []
    replayed = {(r["order"], r["delivery"], r["private_prior"]): r["policies"] for r in previous}
    for order, role_indices in reform.ORDERS.items():
        _, local, edges, _, records = reform.setup(role_indices)
        for rate, share in product(reform.RATES, reform.SHARES):
            scene = receipt.features(reform.COUNTS, reform.CAPS, local, edges, (rate,) * 3, records)
            reference = replayed[order, rate, share]
            output, actions = {}, {}
            for arm, (team, listener, mode) in configurations.items():
                channel = "content" if mode == "adaptive" else "none"
                late = reform.test_private(scene, local, edges, share, rate, listener, records)[channel]["learned"]["by_view"]
                third = reform.test_private(scene, local, edges, share, rate, team, records)[channel]["learned"]["third"]
                output[arm] = sum((share if card == 0 else 1-share) *
                                  rate ** mask.bit_count() * (1-rate) ** (3-mask.bit_count()) *
                                  records[late[card + 1 if mask & 2 and mode == "adaptive" else 0], card, third][mask]
                                  for card, mask in product(range(2), range(8)))
                actions[arm] = {"later": late, "third": third}
            for key, ref in (("shared", "sampled_content"), ("fixed", "fixed_content")):
                assert abs(output[key] - reference[ref]["released"]) <= 1e-9
            output["content_ceiling"] = reference["content_ceiling"]["released"]
            assert max(output.values()) <= output["content_ceiling"] + 1e-9
            rows.append({"order": order, "delivery": rate, "private_prior": share, "scores": output, "actions": actions})
    return rows


def summary(rows):
    result = {}
    for arm in rows[0]:
        differences = [row[arm]-row["shared"] for row in rows]
        result[arm] = {"mean": mean(row[arm] for row in rows),
                       "wins_vs_shared": sum(d > 1e-9 for d in differences),
                       "losses_vs_shared": sum(d < -1e-9 for d in differences)}
    return result


def run():
    frozen = HERE / "plan.json"
    assert json.loads(frozen.read_text()) == plan()
    previous = json.loads((HERE.parent / "results.json").read_text())
    training = receipt.cases(old.TRAIN_SEED, old.TRAIN_N)
    (shared, _), trace = fit(training, 0.)
    trace_ref = previous["training"]["content"]
    assert trace["trajectory_sha256"] == trace_ref["trajectory_sha256"]
    assert trace["reward_returns"] == trace_ref["reward_returns"]
    for step, row in trace["checkpoints"].items():
        assert all(row[k] == v for k, v in trace_ref["checkpoints"][step].items())
    specialized, new_trace = fit(training, old.RATE)
    configurations = arms(shared, specialized)
    assert FRESH_SEED not in (old.TRAIN_SEED, old.EVAL_SEED)
    panels = {
        "fresh": [dispatch(case, configurations) for case in receipt.cases(FRESH_SEED, FRESH_COUNT)],
        "development": [dispatch(case, configurations) for case in receipt.cases(old.EVAL_SEED, old.EVAL_N)],
    }
    for row, ref in zip(panels["development"], previous["held_rows"], strict=True):
        assert row["shared"] == ref["sampled_content"]
    transfer = archive(configurations, previous["transfer_rows"])
    return {"plan_sha256": old.DIGEST(frozen), "control_trace": trace, "fit_trace": new_trace,
            "synthetic": {name: {"summary": summary(rows), "rows": rows} for name, rows in panels.items()},
            "documentary": {name: summary([r["scores"] for r in transfer if r["order"] == name])
                            for name in reform.ORDERS}, "transfer_rows": transfer}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
