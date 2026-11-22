"""Fit two decentralized Bernoulli policies with shared terminal reward."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
ARCHIVE = {
    "reform": RUNS / "reform-2553-transfer/documentary-routing/results.json",
    "afghanistan": RUNS / "afghanistan-2721-source-contrast/documentary-routing/results.json",
}
WITNESS = RUNS / "indexed-witness-routing/results.json"
PRIVATE = {
    "reform": ("uk-explanation", "uk-inclusion", "belgium-explanation"),
    "afghanistan": ("russia-full", "ghana-full", "china-full"),
}
TRAIN_DELIVERY = (0.35, 0.65, 0.95)
TEST_DELIVERY = (0.45, 0.60, 0.80, 0.90)
TRAIN_PRICES = (6, 12, 18)
TEST_PRICES = (8, 11, 15)
TEST_PRIORS = ((0.6, 0.2, 0.2), (0.2, 0.2, 0.6))
SEED = 25532721
UPDATES = 512
BATCH = 256
LR = 0.06
ACTIONS = ("fund", "process")
MAPPINGS = tuple(product((0, 1), repeat=3))


def read(path):
    return json.loads(path.read_text())


def plan():
    return {
        "seed": SEED, "updates": UPDATES, "batch": BATCH, "learning_rate": LR,
        "train_delivery": list(TRAIN_DELIVERY), "test_delivery": list(TEST_DELIVERY),
        "train_prices": list(TRAIN_PRICES), "test_prices": list(TEST_PRICES),
        "test_priors": [list(p) for p in TEST_PRIORS], "private_views": {k: list(v) for k, v in PRIVATE.items()},
        "sha256": {str(p.relative_to(RUNS)): sha256(p.read_bytes()).hexdigest()
                   for p in [Path(__file__), HERE / "protocol.md", *ARCHIVE.values(), WITNESS]},
    }


def tables():
    witnesses = read(WITNESS)["cases"]
    # For each docket and private view, save the protected records for both
    # delivery outcomes and both possible reply actions.
    first_only = np.zeros((2, 3))
    both = np.zeros((2, 3, 2))
    public = np.zeros(2)
    last_only = np.zeros((2, 2))
    observed = np.zeros((2, 3), dtype=int)
    for docket, (name, keys) in enumerate(PRIVATE.items()):
        base = 20 if name == "reform" else 34
        public[docket] = base
        output = read(ARCHIVE[name])["cases"]

        def points(view, a):
            row = output[view]["records"][a]
            return row["released_70"] if name == "reform" else row["grade"]["released_70"]

        last_only[docket] = [points("no-message", a) for a in ACTIONS]
        for view, key in enumerate(keys):
            if name == "reform":
                rubric = {x["id"]: x["weight"] for x in output[key]["records"]["fund"]["packet"]["rubric"]}
                first_only[docket, view] = base + sum(rubric[x] for x in output[key]["grounded_card_ids"])
            else:
                first_only[docket, view] = base + (8 if output[key]["registered"] is not None else 0)
            both[docket, view] = [points(key, a) for a in ACTIONS]
            result = witnesses[f"{name}/{key}"]
            observed[docket, view] = 1 + int(result["choices"]["indexed_and_necessary_verifier"])
    assert both.shape == (2, 3, 2)
    return public, first_only, last_only, both, observed


def features(q0, q1, price):
    return np.stack(np.broadcast_arrays(np.ones_like(q0), q0, q1, q0 * q1, price / 10), axis=-1)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40, 40)))


def adam(x, gradient, first, second, step):
    first = 0.9 * first + 0.1 * gradient
    second = 0.999 * second + 0.001 * gradient**2
    change = (first / (1 - 0.9**step)) / (np.sqrt(second / (1 - 0.999**step)) + 1e-8)
    return np.clip(x + LR * change, -30, 30), first, second


def train(table):
    public, first_only, last_only, both, observed = table
    rng = np.random.default_rng(SEED)
    sender = np.zeros((2, 3, 5))
    receiver = np.zeros((2, 3))
    send_first = np.zeros_like(sender)
    send_second = np.zeros_like(sender)
    reply_first = np.zeros_like(receiver)
    reply_second = np.zeros_like(receiver)
    baseline = np.array([35.0, 45.0])
    history = []
    for step in range(1, UPDATES + 1):
        docket = rng.integers(2, size=BATCH)
        view = rng.integers(3, size=BATCH)
        q0 = rng.choice(TRAIN_DELIVERY, size=BATCH)
        q1 = rng.choice(TRAIN_DELIVERY, size=BATCH)
        price = rng.choice(TRAIN_PRICES, size=BATCH)
        x = features(q0, q1, price)
        p_send = sigmoid(np.sum(sender[docket, view] * x, axis=1))
        send = rng.random(BATCH) < p_send
        front = send & (rng.random(BATCH) < q0)
        obs = np.where(front, observed[docket, view], 0)
        p_reply = sigmoid(receiver[docket, obs])
        reply = rng.random(BATCH) < p_reply
        back = rng.random(BATCH) < q1
        score = np.where(front, np.where(back, both[docket, view, reply.astype(int)], first_only[docket, view]),
                         np.where(back, last_only[docket, reply.astype(int)], public[docket]))
        reward = score - price * send
        advantage = (reward - baseline[docket]) / 10
        grad_s = np.zeros_like(sender)
        grad_r = np.zeros_like(receiver)
        np.add.at(grad_s, (docket, view), x * (advantage * (send - p_send))[:, None] / BATCH)
        np.add.at(grad_r, (docket, obs), advantage * (reply - p_reply) / BATCH)
        sender, send_first, send_second = adam(sender, grad_s, send_first, send_second, step)
        receiver, reply_first, reply_second = adam(receiver, grad_r, reply_first, reply_second, step)
        for family in range(2):
            baseline[family] = 0.95 * baseline[family] + 0.05 * np.mean(reward[docket == family])
        if step in (1, 32, 64, 128, 256, UPDATES):
            history.append({"update": step, "mean_batch_utility": round(float(np.mean(reward)), 8),
                            "sender_gradient_norm": round(float(np.linalg.norm(grad_s)), 8),
                            "receiver_gradient_norm": round(float(np.linalg.norm(grad_r)), 8),
                            "sender": sender.round(10).tolist(), "receiver": receiver.round(10).tolist()})
    return sender, receiver, history


def evaluate(table, sender, receiver):
    public, first_only, last_only, both, observed = table
    results = []
    for docket, q0, q1, cost, prior in product(range(2), TEST_DELIVERY, TEST_DELIVERY, TEST_PRICES, TEST_PRIORS):
        mass = np.array(prior)
        chosen_send = (sender[docket] @ features(q0, q1, cost)) > 0
        chosen_reply = np.where(receiver[docket] > 0, 1, 0)

        def pay(send, reply):
            on = np.asarray(send, dtype=float)
            reply = np.asarray(reply)
            absent = (1 - q1) * public[docket] + q1 * last_only[docket, reply[0]]
            present = (1 - q1) * first_only[docket] + q1 * both[docket, np.arange(3), reply[observed[docket]]]
            scores = absent + (present - absent) * q0 * on
            sending_cost = cost * on
            return {"utility": round(float(mass @ (scores - sending_cost)), 8),
                    "release": round(float(mass @ scores), 8), "cost": round(float(mass @ sending_cost), 8),
                    "send": on.astype(int).tolist(), "reply": reply.tolist()}

        def best_sender(reply):
            value = []
            for view in range(3):
                single = np.eye(3, dtype=int)[view]
                value.append(pay(single, reply)["utility"] > pay((0, 0, 0), reply)["utility"])
            return value

        choices = {
            "learned": pay(chosen_send, chosen_reply),
            "initial_greedy": pay((0, 0, 0), (0, 0, 0)),
            "always_send_fixed_fund": pay((1, 1, 1), (0, 0, 0)),
            "optimal_sender_fixed_fund": pay(best_sender((0, 0, 0)), (0, 0, 0)),
            "always_send_learned_reply": pay((1, 1, 1), chosen_reply),
            "learned_sender_fixed_fund": pay(chosen_send, (0, 0, 0)),
        }
        choices["oracle"] = max((pay(best_sender(reply), reply) for reply in MAPPINGS), key=lambda row: row["utility"])
        assert choices["learned"]["utility"] <= choices["oracle"]["utility"] + 1e-8
        results.append({"family": list(PRIVATE)[docket], "q_first": q0, "q_reply": q1, "cost": cost,
                        "private_prior": prior, "policies": choices})
    return results


def run():
    assert plan() == read(HERE / "plan.json")
    table = tables()
    sender, receiver, history = train(table)
    held = evaluate(table, sender, receiver)
    metrics = {}
    for family in ("all", *PRIVATE):
        rows = [r for r in held if family == "all" or family == r["family"]]
        metrics[family] = {name: {
            **{key: round(float(np.mean([r["policies"][name][key] for r in rows])), 8)
               for key in ("utility", "release", "cost")},
            "oracle_matches": sum(r["policies"][name]["utility"] == r["policies"]["oracle"]["utility"] for r in rows),
            "n": len(rows),
        } for name in rows[0]["policies"]}
    return {"history": history, "summary": metrics, "test": held, "verified_observations": table[-1].tolist()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan() if args.plan else run(), indent=2))
