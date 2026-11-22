"""Learn a sender value model from paired outcomes while training its partner."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from experiment import CHECKPOINTS, HERE, PREVIOUS, fit, send_audit, team

TEMPERATURE = 2.


def plan():
    inputs = (Path(__file__), HERE / "value-protocol.md", HERE / "plan.json",
              HERE / "exact-gradient.json", PREVIOUS / "results.json")
    return {"temperature": TEMPERATURE, "old_training_grid": team.plan(),
            "sha256": {str(path.relative_to(HERE.parent)): sha256(path.read_bytes()).hexdigest()
                       for path in inputs}}


def sender_weights(count, total):
    values = np.divide(total, count, out=np.zeros_like(total), where=count > 0)
    gains_without_reply, gains_with_reply = np.moveaxis(values, -1, 0)
    # The feature order is intercept, q0, q1, q0*q1, price/10.
    zero = np.zeros_like(gains_without_reply)
    return np.stack((zero, gains_without_reply, zero, gains_with_reply-gains_without_reply,
                     zero-10), axis=-1) / TEMPERATURE


def train(table):
    public, first, last, both, observed = table
    rng = np.random.default_rng(team.SEED)
    reply = np.zeros((2, 3))
    r1, r2 = np.zeros_like(reply), np.zeros_like(reply)
    count = np.zeros((2, 3, 2), dtype=int)
    total = np.zeros_like(count, dtype=float)
    baseline = np.array([35., 45.])
    history = []
    n = team.BATCH
    for step in range(1, team.UPDATES+1):
        d = rng.integers(2, size=n)
        v = rng.integers(3, size=n)
        q0 = rng.choice(team.TRAIN_DELIVERY, size=n)
        q1 = rng.choice(team.TRAIN_DELIVERY, size=n)
        price = rng.choice(team.TRAIN_PRICES, size=n)
        features = team.features(q0, q1, price)
        actor = sender_weights(count, total)
        sender_prob = team.sigmoid(np.sum(actor[d, v] * features, axis=1))
        sent = rng.random(n) < sender_prob
        delivery = rng.random(n) < q0
        receiver_draw = rng.random(n)
        back = rng.random(n) < q1
        obs_if_send = np.where(delivery, observed[d, v], 0)
        p0 = team.sigmoid(reply[d, 0])
        p1 = team.sigmoid(reply[d, obs_if_send])
        a0, a1 = (receiver_draw < p0).astype(int), (receiver_draw < p1).astype(int)
        r0 = np.where(back, last[d, a0], public[d])
        r1_value = np.where(delivery, np.where(back, both[d, v, a1], first[d, v]), r0)
        advantage = r1_value - r0
        indices = (d[delivery], v[delivery], back[delivery].astype(int))
        np.add.at(count, indices, 1)
        np.add.at(total, indices, advantage[delivery])
        reward = np.where(sent, r1_value-price, r0)
        chosen_obs = np.where(sent, obs_if_send, 0)
        chosen_action = np.where(sent, a1, a0)
        chosen_prob = np.where(sent, p1, p0)
        gradient = np.zeros_like(reply)
        np.add.at(gradient, (d, chosen_obs),
                  (reward-baseline[d])*(chosen_action-chosen_prob)/(10*n))
        reply, r1, r2 = team.adam(reply, gradient, r1, r2, step)
        for family in range(2):
            baseline[family] = .95*baseline[family] + .05*np.mean(reward[d == family])
        if step in CHECKPOINTS:
            history.append({"update": step, "observations": count.tolist(), "totals": total.tolist(),
                            "sender": sender_weights(count, total).tolist(), "receiver": reply.tolist(),
                            "mean_training_utility": float(np.mean(reward))})
    assert np.all(count > 0)
    return sender_weights(count, total), reply, history


def run():
    spec = plan()
    assert spec == fit.read(HERE / "value-plan.json")
    old = fit.read(PREVIOUS / "results.json")
    banks, _ = fit.tables(old["grades"])
    baseline = tuple(np.array(old["history"][-1][key]) for key in ("sender", "receiver"))
    sender, reply, history = train(banks["trusted_native"])
    report = fit.compare(banks["audited_native"], (sender, reply), baseline)
    return {"training_terminal_queries": 2*team.BATCH*team.UPDATES, "history": history,
            "evaluation": report, "sender_mismatches": send_audit(banks["audited_native"], report["held"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    print(json.dumps(plan() if parser.parse_args().plan else run(), indent=2))
