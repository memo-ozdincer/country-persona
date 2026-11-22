"""Fit receipt-aware policies using one forecast of partner responses."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations, product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RUNS = HERE.parents[3]
REFORM = RUNS / "reform-2553-transfer"
sys.path.insert(0, str(PARENT))
import receipt_choice as receiver
import private_receipt as replay

old, loss = receiver.old, receiver.loss
FIXED_LEGACY = np.array([1., 0., 1.])
FIXED_UPDATED = np.array([1., 0., 1.])
MIXTURE_SHIFT = 0.30
ARCHIVED = PARENT / "results.json"


def plan():
    pins = (Path(__file__), HERE / "protocol.md", Path(receiver.__file__), Path(replay.__file__),
            ARCHIVED, PARENT / "private-results.json", REFORM / "transfer.py", REFORM / "results.json")
    return {"seed": old.TRAIN_SEED, "holdout_seed": old.EVAL_SEED, "train_n": old.TRAIN_N, "held_n": old.EVAL_N,
            "updates": old.UPDATES, "rate": old.RATE, "forecast_prior_shift": MIXTURE_SHIFT,
            "sha256": {str(p.relative_to(RUNS)): old.DIGEST(p) for p in pins}}


def design(scene, local, edges, rates, advertised):
    options_a, options_b, options_c = scene["choices"]
    membership = [np.asarray([[card in action for card in range(len(weights))] for action in options])
                  for options, weights in zip(scene["choices"], local, strict=True)]
    a = scene["adaptive"]
    c = scene["open"][2].copy()
    early = old.softmax(scene["open"][1][:, 0] * 7 / 3)
    for i, u, j, v, weight in edges:
        if (i, j) == (1, 2):
            distribution = membership[1][:, u]
            old_prob = np.array([distribution.mean(), early @ distribution])
            c[membership[2][:, v], 1:] += rates[1] * weight * (advertised @ distribution - old_prob) / 7
    a_plan = np.argmax(a @ FIXED_LEGACY, axis=1)
    c_plan = int(np.argmax(c @ FIXED_LEGACY))
    # Marginal predicted content of A as seen by the independent desk before A's receipt is drawn.
    a_distribution = ((1 - rates[1]) * membership[0][a_plan[0]].astype(float) +
                      rates[1] * (advertised @ membership[0][a_plan[1:]]))
    a_update = np.zeros(a.shape[:2])
    c_update = np.zeros(c.shape[0])
    for i, u, j, v, w in edges:
        if (i, j) == (0, 1):
            a_update[1:, :] += w * np.outer(membership[1][:, v], membership[0][:, u])
        elif (i, j) == (0, 2):
            a_update[:, membership[0][:, u]] += w * rates[2] * membership[2][c_plan, v]
            c_update[membership[2][:, v]] += w * rates[0] * a_distribution[u]
        else:
            assert (i, j) == (1, 2)
            c_update[membership[2][:, v]] += w * rates[1] * (advertised @ membership[1][:, u])
    updated_a = np.stack((a[..., 0], a[..., 2], a_update / 7), axis=-1)
    updated_c = np.column_stack((c[:, 0], c[:, 2], c_update / 7))
    return (a, c), (updated_a, updated_c), (a_plan.tolist(), c_plan)


def case(counts, caps, local, edges, rates, truth, advertised, records=None):
    scene = receiver.features(counts, caps, local, edges, rates, records)
    legacy, updated, announcement = design(scene, local, edges, rates, advertised)
    probability = truth[:, None] * scene["mask_probabilities"][None, :]
    assert abs(probability.sum() - 1) <= 1e-10
    return scene, legacy, updated, probability, announcement


def synthetic(seed, size, shift=False):
    rng = np.random.default_rng(seed)
    inventory = np.random.default_rng(seed + 9901)
    rows = []
    for _ in range(size):
        local = [rng.integers(0, 8, n) for n in old.COUNTS]
        edges = [(i, int(rng.integers(old.COUNTS[i])), j, int(rng.integers(old.COUNTS[j])), int(rng.integers(0, 15)))
                 for i, j in combinations(range(3), 2)]
        rates = inventory.choice(loss.RATES, 3)
        truth = inventory.dirichlet([2.] * 3)
        advertised = (1 - MIXTURE_SHIFT) * truth + MIXTURE_SHIFT * np.roll(truth, 1) if shift else truth
        rows.append(case(old.COUNTS, old.CAPS, local, edges, rates, truth, advertised))
    return rows


def objective(sample, weights):
    scene, _, (a, c), p, _ = sample
    prob_a = np.asarray([old.softmax(x @ weights) for x in a])
    prob_c = old.softmax(c @ weights)
    obs = scene["observe"]
    mass = p[:, None, :, None] * prob_c[None, :, None, None] * prob_a[obs][:, None, :, :]
    assert abs(mass.sum() - 1) < 1e-10
    value = float(np.sum(mass * scene["returns"]))
    residual = mass * (scene["returns"] - value)
    a_local = (a - np.einsum("oa,oaf->of", prob_a, a)[:, None, :])[obs]
    gradient = np.einsum("bcma,bmaf->f", residual, a_local)
    gradient += np.einsum("bcma,cf->f", residual, c - prob_c @ c)
    return value, gradient


def fit(samples):
    weights = np.zeros(3)
    trace = []
    for step in range(old.UPDATES + 1):
        evaluated = [objective(sample, weights) for sample in samples]
        mean_reward = mean(row[0] for row in evaluated)
        grad = np.mean([row[1] for row in evaluated], axis=0)
        if step == 0:
            diff = np.array([(objective(samples[0], weights + axis * 1e-5)[0]
                              - objective(samples[0], weights - axis * 1e-5)[0]) / 2e-5 for axis in np.eye(3)])
            assert np.allclose(diff, evaluated[0][1], rtol=0, atol=1e-7)
        if step % 15 == 0:
            trace.append({"step": step, "mean_expected_reward": mean_reward, "weights": weights.tolist()})
        if step < old.UPDATES:
            weights += old.RATE * grad
    assert trace[0]["mean_expected_reward"] < trace[-1]["mean_expected_reward"]
    return weights, trace


def policies(sample, weights, previous):
    scene, legacy, updated, probability, _ = sample
    controls = {"older_fit": (legacy, previous), "legacy_fixed": (legacy, FIXED_LEGACY),
                "refreshed_fixed": (updated, FIXED_UPDATED), "refreshed_fit": (updated, weights),
                "fit_without_refreshed_signal": (updated, np.array([weights[0], weights[1], 0.]))}
    arms = {name: (np.argmax(a @ w, axis=1).tolist(), int(np.argmax(c @ w)))
            for name, ((a, c), w) in controls.items()}
    ceiling, action, third = replay.optimal(scene["returns"], probability, scene["observe"])
    arms["oracle"] = (action, third)
    scores = {name: replay.expected(scene["returns"], probability, scene["observe"], np.asarray(a), c)
              for name, (a, c) in arms.items()}
    assert all(score <= ceiling + 1e-9 for score in scores.values())
    return scores, arms


def summarize(rows):
    return {arm: {"mean": mean(row[arm] for row in rows),
                  "mean_delta_against_older_fit": mean(row[arm] - row["older_fit"] for row in rows),
                  "ties_with_oracle": sum(abs(row[arm] - row["oracle"]) <= 1e-9 for row in rows)}
            for arm in rows[0]}


def capture(sample, weights, previous, true):
    score, arms = policies(sample, weights, previous)
    public = true[(0, 0, 0)][0]
    scene, _, _, probability, launch = sample
    result = {}
    for name, (a, c) in arms.items():
        by_the_record = sum(probability[b, m] * true[(a[scene["observe"][b, m]], b, c)][m]
                            for b, m in product(range(len(probability)), range(8)))
        assert abs(score[name] + public - by_the_record) < 1e-9
        result[name] = float(by_the_record)
    return result, arms, launch


def archive(weights, previous):
    spec = spec_from_file_location("reform_2553_feature_source", REFORM / "transfer.py")
    asset = module_from_spec(spec)
    spec.loader.exec_module(asset)
    reform = json.loads((REFORM / "results.json").read_text())["orders"]
    tribunals = json.loads((PARENT / "private-results.json").read_text())
    output = {}
    for key, order in asset.ORDERS.items():
        _, local, edges, _, true = asset.setup(order)
        series = []
        for prior in reform[key]["forced_private_inventory"]:
            share, rate = prior["first_card_probability"], prior["receipt"]
            p = np.array([share, 1 - share])
            sample = case(asset.COUNTS, asset.CAPS, local, edges, (rate,) * 3, p, p, true)
            result, actions, forecast = capture(sample, weights, previous, true)
            ref = prior["outcomes"]["content"]
            assert abs(result["older_fit"] - ref["learned"]["released"]) < 1e-9
            assert abs(result["legacy_fixed"] - ref["fixed"]["released"]) < 1e-9
            assert abs(result["oracle"] - ref["oracle"]["released"]) < 1e-9
            series.append({"share": share, "rate": rate, "expected_release": result, "policies": actions,
                           "forecast_origin": forecast, "arrival_oracle": prior["outcomes"]["arrival"]["oracle"]["released"]})
        output[key] = series
    (_, counts, caps, values, edges, score), = [row for row in old.un_cases() if row[0] == "tribunals"]
    local = [np.asarray(row) for row in values]
    choices = old.options(counts, caps)
    true = {ids: [score([choices[i][a] for i, a in enumerate(ids)], mask) for mask in range(8)]
            for ids in product(*(range(len(group)) for group in choices))}
    output["tribunals"] = []
    for prior in tribunals["rows"]:
        share, rate = prior["staffing_probability"], prior["rate"]
        p = np.array([share, 1 - share])
        sample = case(counts, caps, local, edges, (rate,) * 3, p, p, true)
        result, actions, forecast = capture(sample, weights, previous, true)
        ref = prior["outcomes"]["content"]
        assert abs(result["older_fit"] - ref["learned"]["expected_release"]) < 1e-9
        assert abs(result["legacy_fixed"] - ref["fixed"]["expected_release"]) < 1e-9
        assert abs(result["oracle"] - ref["oracle"]["expected_release"]) < 1e-9
        output["tribunals"].append({"share": share, "rate": rate, "expected_release": result,
                                  "policies": actions, "forecast_origin": forecast,
                                  "arrival_oracle": prior["outcomes"]["arrival"]["oracle"]["expected_release"]})
    return output


def run():
    assert plan() == json.loads((HERE / "plan.json").read_text())
    samples = synthetic(old.TRAIN_SEED, old.TRAIN_N)
    weights, trace = fit(samples)
    previous = np.asarray(json.loads(ARCHIVED.read_text())["training"][-1]["weights"])
    tests = {}
    for label, shift in (("matched", False), ("misannounced", True)):
        rows = [policies(sample, weights, previous)[0] for sample in synthetic(old.EVAL_SEED, old.EVAL_N, shift)]
        tests[label] = {"summary": summarize(rows), "rows": rows}
    held = archive(weights, previous)
    archive_summary = {}
    for name, rows in held.items():
        releases = [row["expected_release"] for row in rows]
        result = summarize(releases)
        for arm in result:
            result[arm]["below_arrival"] = sum(row["expected_release"][arm] < row["arrival_oracle"] - 1e-9
                                              for row in rows)
        archive_summary[name] = result
    return {"training": trace, "synthetic": tests, "archived_summary": archive_summary, "archive": held,
            "archived_policy_replays": sum(len(values) * len(values[0]["expected_release"]) for values in held.values()),
            "plan_sha256": old.DIGEST(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), ensure_ascii=False, indent=2))
