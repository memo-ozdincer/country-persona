"""Fit small shared sender and receiver actors and test held-docket transfer."""
import argparse
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
ORIGINAL = RUNS / "documentary-team-policy"
spec = spec_from_file_location("documentary_team", ORIGINAL / "train_team.py")
base = module_from_spec(spec)
spec.loader.exec_module(base)
ADAPT = 32


def plan():
    assert base.plan() == base.read(ORIGINAL / "plan.json")
    files = (Path(__file__), HERE / "protocol.md", ORIGINAL / "train_team.py",
             ORIGINAL / "plan.json", ORIGINAL / "results.json")
    return {"source_updates": base.UPDATES, "target_updates": ADAPT,
            "batch": base.BATCH, "seed": base.SEED, "target_seed_offset": 31,
            "test_delivery": list(base.TEST_DELIVERY), "test_prices": list(base.TEST_PRICES),
            "test_priors": [list(v) for v in base.TEST_PRIORS],
            "sha256": {str(p.relative_to(RUNS)): sha256(p.read_bytes()).hexdigest() for p in files}}


def features(q_sender, q_reply, price, own_points, support):
    return np.stack(np.broadcast_arrays(np.ones_like(q_sender), q_sender, q_reply, price / 10,
                                         q_sender * own_points / 10, q_sender * q_reply,
                                         support, support * q_sender * q_reply), axis=-1)


def zero():
    return np.zeros(8), np.zeros(3)


def train(table, family, initial, updates, seed):
    public, first_only, last_only, both, observed = table
    rng = np.random.default_rng(seed)
    sender, receiver = [v.copy() for v in initial]
    send_mean, send_var = np.zeros_like(sender), np.zeros_like(sender)
    reply_mean, reply_var = np.zeros_like(receiver), np.zeros_like(receiver)
    running_mean = public[family]
    trace = []
    for step in range(1, updates + 1):
        view = rng.integers(3, size=base.BATCH)
        q0 = rng.choice(base.TRAIN_DELIVERY, size=base.BATCH)
        q1 = rng.choice(base.TRAIN_DELIVERY, size=base.BATCH)
        price = rng.choice(base.TRAIN_PRICES, size=base.BATCH)
        own = first_only[family, view] - public[family]
        supports = observed[family, view] == 2
        x = features(q0, q1, price, own, supports)
        prob_send = base.sigmoid(x @ sender)
        sent = rng.random(base.BATCH) < prob_send
        arrived = sent & (rng.random(base.BATCH) < q0)
        obs = np.where(arrived, observed[family, view], 0)
        prob_reply = base.sigmoid(receiver[obs])
        reply = (rng.random(base.BATCH) < prob_reply).astype(int)
        reply_arrived = rng.random(base.BATCH) < q1
        release = np.where(
            arrived, np.where(reply_arrived, both[family, view, reply], first_only[family, view]),
            np.where(reply_arrived, last_only[family, reply], public[family])
        )
        utility = release - price * sent
        advantage = (utility - running_mean) / 10
        grad_s = x.T @ (advantage * (sent - prob_send)) / base.BATCH
        grad_r = np.zeros_like(receiver)
        np.add.at(grad_r, obs, advantage * (reply - prob_reply) / base.BATCH)
        sender, send_mean, send_var = base.adam(sender, grad_s, send_mean, send_var, step)
        receiver, reply_mean, reply_var = base.adam(receiver, grad_r, reply_mean, reply_var, step)
        running_mean = 0.95 * running_mean + 0.05 * float(np.mean(utility))
        if step in {1, 8, 16, 32, 128, 256, updates}:
            trace.append({"update": step, "mean_batch_utility": round(float(np.mean(utility)), 8),
                          "sender": sender.round(10).tolist(), "receiver": receiver.round(10).tolist(),
                          "sender_grad_norm": round(float(np.linalg.norm(grad_s)), 8),
                          "receiver_grad_norm": round(float(np.linalg.norm(grad_r)), 8)})
    return (sender, receiver), trace


def evaluate(table, target, policies, oracle_rows):
    public, first_only, last_only, both, observed = table
    coverage = first_only[target] - public[target]
    supports = observed[target] == 2
    family = list(base.PRIVATE)[target]
    held = []
    oracle_rows = [r for r in oracle_rows if r["family"] == family]
    controls = product(base.TEST_DELIVERY, base.TEST_DELIVERY, base.TEST_PRICES, base.TEST_PRIORS)
    for (q0, q1, price, prior), anchor in zip(controls, oracle_rows, strict=True):
        x = features(q0, q1, price, coverage, supports)
        mass = np.array(prior)

        def branches(reply):
            reply = np.asarray(reply)
            absent = (1 - q1) * public[target] + q1 * last_only[target, reply[0]]
            present = (1 - q1) * first_only[target] + q1 * both[target, np.arange(3), reply[observed[target]]]
            return absent, q0 * (present - absent)

        def pay(send, reply):
            absent, gain = branches(reply)
            fact = absent + mass @ (gain * send)
            cost = price * (mass @ send)
            return {"release": round(float(fact), 8), "cost": round(float(cost), 8),
                    "utility": round(float(fact - cost), 8), "send": np.asarray(send, dtype=int).tolist(),
                    "reply": np.asarray(reply, dtype=int).tolist()}

        fitted = {key: pay(x @ sender > 0, (receiver > 0).astype(int))
                  for key, (sender, receiver) in policies.items()}
        frozen_s = x @ policies["frozen"][0] > 0
        frozen_r = (policies["frozen"][1] > 0).astype(int)
        simple = np.array([0, 0, 1])
        empty = np.zeros(3, dtype=bool)
        fitted["frozen_sender_best_receiver"] = max(
            (pay(frozen_s, mapping) for mapping in base.MAPPINGS), key=lambda row: row["utility"])
        fitted["best_sender_frozen_receiver"] = pay(branches(frozen_r)[1] > price, frozen_r)
        fitted["no_send"] = pay(empty, simple)
        fitted["always_send"] = pay(~empty, simple)
        fitted["oracle"] = max((pay(branches(mapping)[1] > price, mapping) for mapping in base.MAPPINGS),
                               key=lambda row: row["utility"])
        assert (anchor["q_first"], anchor["q_reply"], anchor["cost"], anchor["private_prior"]) == (
            q0, q1, price, list(prior))
        assert fitted["oracle"]["utility"] == anchor["policies"]["oracle"]["utility"]
        assert all(row["utility"] <= fitted["oracle"]["utility"] + 1e-8 for row in fitted.values())
        held.append({"q_first": q0, "q_reply": q1, "price": price, "private_prior": prior, "policies": fitted})
    return held


def run():
    assert plan() == base.read(HERE / "plan.json")
    table = base.tables()
    original = base.read(ORIGINAL / "results.json")["test"]
    report = {}
    for source, target in ((0, 1), (1, 0)):
        trained, source_history = train(table, source, zero(), base.UPDATES, base.SEED + source)
        target_seed = base.SEED + 31 + target
        warm, warm_history = train(table, target, trained, ADAPT, target_seed)
        cold, cold_history = train(table, target, zero(), ADAPT, target_seed)
        policies = {"frozen": trained, "warm_32": warm, "cold_32": cold}
        held = evaluate(table, target, policies, original)
        metrics = {
            key: {
                **{field: round(float(np.mean([r["policies"][key][field] for r in held])), 8)
                   for field in ("release", "cost", "utility")},
                "oracle_matches": sum(r["policies"][key]["utility"] == r["policies"]["oracle"]["utility"]
                                      for r in held),
                "n": len(held),
            } for key in held[0]["policies"]
        }
        labels = list(base.PRIVATE)
        report[f"{labels[source]}_to_{labels[target]}"] = {
            "summary": metrics, "held": held, "source_history": source_history,
            "warm_history": warm_history, "cold_history": cold_history,
            "receiver_choices": {key: (value[1] > 0).astype(int).tolist() for key, value in policies.items()},
        }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan() if args.plan else run(), indent=2))
