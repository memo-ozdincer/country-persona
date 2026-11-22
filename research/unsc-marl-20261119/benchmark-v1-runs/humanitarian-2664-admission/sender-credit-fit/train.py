"""Fit and evaluate cooperative sender policies on saved terminal records."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "source-preserving/scores.json"
SEED = 266412
EPISODES = 64
TRAIN_DELIVERY = 0.9
TRAIN_MIX = 0.5
TEST_DELIVERY = (0.65, 0.75, 0.85, 0.95)
TEST_MIX = (0.1, 0.5, 0.9)
ACTIONS = tuple(product((0, 1), repeat=2))
ACTION_NAMES = ("neither", "india", "safeguards", "both")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def plan():
    return {
        "seed": SEED, "episodes": EPISODES, "train_delivery": TRAIN_DELIVERY,
        "train_india_first": TRAIN_MIX, "test_delivery": list(TEST_DELIVERY),
        "test_india_first": list(TEST_MIX), "send_cost_premium": 2,
        "sha256": {p.name: digest(p) for p in (Path(__file__), HERE / "protocol.md", SOURCE)},
    }


def reward_data():
    records = json.loads(SOURCE.read_text())["cases"]
    standalone_key = {0: "none", 1: "india", 2: "safeguards"}
    values = np.array([
        [records[standalone_key[mask] if mask < 3 else name]["require_both"] for mask in range(4)]
        for name in ("safeguards-first", "india-first")
    ])
    standalone = values[0, [2, 1]] - values[0, 0]
    assert np.all(values[:, :3] == values[0, :3])
    assert all(records[k]["abstained"] for k in standalone_key.values())
    return values, standalone


def features(adopted, india, india_first, critic):
    pair = adopted * india
    if critic == "additive":
        return [1, adopted, india]
    if critic == "order_pooled":
        return [1, adopted, india, pair]
    return [1, adopted, india, pair * (1 - india_first), pair * india_first]


def exploration(rewards):
    rng = np.random.default_rng(SEED)
    sends = (rng.random((EPISODES, 2)) < 0.5).astype(int)
    arrivals = sends * (rng.random((EPISODES, 2)) < TRAIN_DELIVERY)
    order = (rng.random(EPISODES) < TRAIN_MIX).astype(int)
    return [
        {"sent": send.tolist(), "received": received.tolist(), "india_first": int(o),
         "reward": int(rewards[o, 2 * received[0] + received[1]])}
        for send, received, o in zip(sends, arrivals, order, strict=True)
    ]


def fit_team(log, critic):
    x = np.array([features(*r["received"], r["india_first"], critic) for r in log])
    target = np.array([r["reward"] for r in log])
    params, _, rank, _ = np.linalg.lstsq(x, target, rcond=None)
    coeff = params.round(10)
    assert rank == len(coeff)
    return coeff.tolist(), 0


def fit_deletion(log, rewards):
    standalone = [[], []]
    increments = [[], []]
    extra_lookups = 0
    for episode in log:
        a, b = episode["received"]
        order = episode["india_first"]
        actual = episode["reward"]
        if a and not b:
            standalone[0].append(actual - rewards[order, 0])
        if b and not a:
            standalone[1].append(actual - rewards[order, 0])
        if a and b:
            # The two single-source terminal values are additional observations.
            increments[order].append(actual - rewards[order, 2] - rewards[order, 1] + rewards[order, 0])
            extra_lookups += 2
    assert all(len(rows) > 0 for rows in (*standalone, *increments))
    assert rewards[0, 0] == rewards[1, 0]
    return [float(rewards[0, 0]), *(float(np.mean(x)) for x in (*standalone, *increments))], extra_lookups


def predict(coefficients, critic):
    weights = np.array(coefficients)
    return np.array([[features(a, b, order, critic) @ weights for a, b in ACTIONS] for order in (0, 1)])


def evaluate_actions(rewards, standalone, p, india_first):
    order_average = np.array([1 - india_first, india_first]) @ rewards
    values = []
    for action in ACTIONS:
        delivery = p * np.array(action)
        mass = np.array([np.prod(np.where(receipt, delivery, 1 - delivery)) for receipt in ACTIONS])
        assert np.isclose(mass.sum(), 1)
        release = float(mass @ order_average)
        cost = float((p * standalone + 2) @ np.array(action))
        values.append({"release": release, "cost": cost, "utility": release - cost})
    return values


def choose(values):
    # Break numeric ties by the fixed action order.
    return max(range(len(values)), key=lambda index: round(values[index]["utility"], 9))


def run():
    assert plan() == json.loads((HERE / "plan.json").read_text())
    rewards, standalone = reward_data()
    log = exploration(rewards)
    fits = {name: fit_team(log, name) for name in ("additive", "order_pooled", "order_aware")}
    fits["deletion_credit"] = fit_deletion(log, rewards)
    tables = {name: predict(coeff, name) for name, (coeff, _) in fits.items()}
    test = []
    for p, order_mix in product(TEST_DELIVERY, TEST_MIX):
        actual = evaluate_actions(rewards, standalone, p, order_mix)
        oracle = choose(actual)
        fitted = {name: choose(evaluate_actions(table, standalone, p, order_mix))
                  for name, table in tables.items()}
        analytic_joint_gain = p**2 * (rewards[1, 3] - rewards[1, 2] - rewards[1, 1] + rewards[1, 0]) * order_mix - 4
        assert np.isclose(actual[3]["utility"] - actual[0]["utility"], analytic_joint_gain)
        assert all(np.isclose(actual[i]["utility"], actual[0]["utility"] - 2) for i in (1, 2))
        test.append({"delivery": p, "india_first": order_mix, "oracle": ACTION_NAMES[oracle],
                     "fixed": {name: {k: round(v, 8) for k, v in value.items()}
                               for name, value in zip(ACTION_NAMES, actual, strict=True)},
                     "fitted": {name: {"action": ACTION_NAMES[choice],
                                       "regret": round(actual[oracle]["utility"] - actual[choice]["utility"], 8)}
                                for name, choice in fitted.items()}})
    return {
        "reward_table_in_receipt_mask_order": rewards.tolist(),
        "exploration": log,
        "fit": {name: {"coefficients": coeff, "extra_counterfactual_lookups": extra,
                       "predicted_table": tables[name].round(8).tolist()}
                for name, (coeff, extra) in fits.items()},
        "held": test,
        "mean_regret": {name: round(float(np.mean([row["fitted"][name]["regret"] for row in test])), 8)
                        for name in fits},
        "oracle_matches": {name: sum(row["fitted"][name]["action"] == row["oracle"] for row in test)
                           for name in fits},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan() if args.plan else run(), indent=2))
