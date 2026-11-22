"""Fit one cooperative reply choice from archived, scored native records."""
from itertools import product
import json

import numpy as np

from concern_study import HERE, read

SEED = 255327
ACTIONS = ("process", "fund")
ORDERS = ("uk-first", "germany-first")
POLICIES = ("standalone", "two_delegation_gate", "exact_pair_gate")


def fit(reward, fallback, draws):
    inputs = []
    for uk, reply, order, action in draws:
        points = reward[uk, order, action] if reply else fallback[uk]
        inputs.append({"uk_card_arrived": bool(uk), "german_reply_arrived": bool(reply),
                       "order": ORDERS[order], "action": ACTIONS[action], "terminal_score": int(points)})
    estimates = np.empty_like(reward, dtype=float)
    for uk, order, action in product(range(2), repeat=3):
        values = [row["terminal_score"] for row in inputs if row["german_reply_arrived"]
                  and row["uk_card_arrived"] == bool(uk) and row["order"] == ORDERS[order]
                  and row["action"] == ACTIONS[action]]
        assert values
        estimates[uk, order, action] = np.mean(values)
    return inputs, estimates


def evaluate(reward, estimates, fallback):
    held = []
    for q_early, q_reply, uk_first in product((0.35, 0.65, 0.9), (0.45, 0.75, 0.95), (0.2, 0.8)):
        order = np.array([uk_first, 1 - uk_first])
        weight = np.array([1 - q_early, q_early])
        truth = np.einsum("o,uoa->ua", order, reward)
        predicted = np.einsum("o,uoa->ua", order, estimates)
        exact = np.argmax(truth, axis=1)
        learned = np.argmax(predicted, axis=1)
        controls = {"always_process": (0, 0), "always_fund": (1, 1),
                    "learned": tuple(learned), "exact": tuple(exact)}
        result = {}
        for key, actions in controls.items():
            points = q_reply * truth[np.arange(2), actions] + (1 - q_reply) * fallback
            result[key] = {"action_without_uk": ACTIONS[actions[0]], "action_with_uk": ACTIONS[actions[1]],
                           "release": round(float(weight @ points), 8)}
        held.append({"uk_delivery": q_early, "german_delivery": q_reply, "uk_first": uk_first, "outcomes": result})
    return held


def run():
    archive = read(HERE / "scores.json")
    values = archive["views"]
    partial = archive["fallback_partials"]
    fallback = np.array([partial["public"], values["uk-only"]["standalone"]])
    neither_uk = np.array([[partial["de-process"], partial["de-fund"]]] * 2)
    rng = np.random.default_rng(SEED)
    draws = (rng.random((64, 4)) < np.array([0.75, 0.85, 0.5, 0.5])).astype(int)
    out = {}
    for policy in POLICIES:
        both = [[values[f"{stem}-{order}"][policy] for stem in ("process", "cross")] for order in ORDERS]
        rewards = np.array([neither_uk, both])
        history, fitted = fit(rewards, fallback, draws)
        rows = evaluate(rewards, fitted, fallback)
        out[policy] = {
            "exploration": history, "learned_receipt_values": fitted.tolist(), "held": rows,
            "mean": {name: round(float(np.mean([row["outcomes"][name]["release"] for row in rows])), 8)
                     for name in rows[0]["outcomes"]},
        }
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
