"""Learn decentralized routes from one observed terminal score per rollout."""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
DONOR = RUNS / "native-reward-routing-fit"
sys.path.insert(0, str(DONOR))
import learn as prior

team = prior.team
BATCH = 32
OBSERVATIONS = (64, 256, 1024, 8192)
CONTENT = {"independent": False, "peer": True}


def plan():
    source = prior.plan()
    paths = (Path(__file__), HERE / "protocol.md", DONOR / "plan.json",
             DONOR / "results.json", RUNS.parent / "benchmark-v1.7/release.json")
    return {
        "previous_input_pins": source["sha256"],
        "pins": {str(path.relative_to(RUNS.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in paths},
        "seed": source["train"]["seed"],
        "batch": BATCH,
        "observations": list(OBSERVATIONS),
        "train": {k: source["train"][k] for k in ("prices", "delivery")},
        "held": source["held"],
        "initial_receipt_value": 35,
        "exploration": 0.2,
    }


def receipt_bank(data, joined):
    return np.concatenate(([data["public"]], data["first"], data["last"], joined.ravel()))


def view_observations(data, peer):
    return data["observed"] if peer else np.ones(3, dtype=int)


def outcome_table(receipts):
    return receipts[0], receipts[1:4], receipts[4:6], receipts[6:].reshape(3, 2)


def pay(receipts, observed, setting, sender, reply):
    q0, q1, price, mass = setting
    public, first, last, joined = outcome_table(receipts)
    absent = (1 - q1) * public + q1 * last[reply[0]]
    pairs = joined[np.arange(3), reply[observed]]
    present = (1 - q1) * first + q1 * pairs
    released = mass @ (absent + q0 * sender * (present - absent))
    cost = price * (mass @ sender)
    relation = (mass * sender * q0 * q1) @ (pairs == 70)
    blocked = (mass * sender * q0 * q1) @ (pairs == 0)
    return np.array([released - cost, released, cost, relation, blocked])


def best_route(receipts, observed, setting):
    q0, q1, price, mass = setting
    public, first, last, joined = outcome_table(receipts)
    states = int(observed.max()) + 1
    replies = np.array(list(product(range(2), repeat=states)))
    absent = (1 - q1) * public + q1 * last[replies[:, 0]]
    present = (1 - q1) * first + q1 * joined[np.arange(3), replies[:, observed]]
    advantage = q0 * (present - absent[:, None]) - price
    sender = advantage > 1e-9
    index = int(np.argmax(absent + (advantage * sender) @ mass))
    return sender[index], replies[index]


def rollout(receipts, view, q0, q1, draws, sender, reply):
    front = sender & (draws[0] < q0)
    back = draws[1] < q1
    idx = np.where(front, np.where(back, 6 + 2 * view + reply, 1 + view),
                   np.where(back, 4 + reply, 0))
    return receipts[idx], idx


def train(receipts, observed, spec, receipt_fit):
    rng = np.random.default_rng(spec["seed"])
    n = spec["batch"]
    sender = np.zeros((3, 5))
    reply = np.zeros(int(observed.max()) + 1)
    sm, sv = np.zeros_like(sender), np.zeros_like(sender)
    rm, rv = np.zeros_like(reply), np.zeros_like(reply)
    count = np.zeros(len(receipts), dtype=int)
    total = np.zeros(len(receipts))
    baseline = spec["initial_receipt_value"]
    estimates = np.full(len(receipts), baseline, dtype=float)
    snapshots = {}
    log = []
    for step in range(1, max(spec["observations"]) // n + 1):
        view = rng.integers(3, size=n)
        q0, q1 = rng.choice(spec["train"]["delivery"], size=(2, n))
        price = rng.choice(spec["train"]["prices"], size=n)
        send_draw, reply_draw, front_draw, back_draw = rng.random((4, n))
        if receipt_fit:
            plans = {setting: best_route(estimates, observed, (*setting, np.full(3, 1 / 3)))
                     for setting in sorted(set(zip(q0, q1, price)))}
            intended = [plans[setting] for setting in zip(q0, q1, price)]
            half = spec["exploration"] / 2
            ps = np.array([s[v] for (s, _), v in zip(intended, view)]) * (1 - 2 * half) + half
        else:
            x = team.features(q0, q1, price)
            ps = team.sigmoid(np.sum(sender[view] * x, axis=1))
        send = send_draw < ps
        state = np.where(send & (front_draw < q0), observed[view], 0)
        if receipt_fit:
            pr = np.array([r[o] for (_, r), o in zip(intended, state)]) * (1 - 2 * half) + half
        else:
            pr = team.sigmoid(reply[state])
        action = (reply_draw < pr).astype(int)
        score, keys = rollout(receipts, view, q0, q1, (front_draw, back_draw), send, action)
        net = score - price * send
        np.add.at(count, keys, 1)
        if receipt_fit:
            np.add.at(total, keys, score)
            np.divide(total, count, out=estimates, where=count > 0)
        else:
            advantage = (net - baseline) / 10
            gs, gr = np.zeros_like(sender), np.zeros_like(reply)
            np.add.at(gs, view, x * (advantage * (send - ps))[:, None] / n)
            np.add.at(gr, state, advantage * (action - pr) / n)
            sender, sm, sv = team.adam(sender, gs, sm, sv, step)
            reply, rm, rv = team.adam(reply, gr, rm, rv, step)
            baseline = 0.95 * baseline + 0.05 * net.mean()
        log.append({"indices": keys.tolist(), "scores": score.tolist(),
                    "mean_utility": round(float(net.mean()), 8)})
        if step * n in spec["observations"]:
            snapshots[step * n] = {
                "counts": count.tolist(), "estimate": estimates.tolist() if receipt_fit else None,
                "sender": sender.tolist() if not receipt_fit else None,
                "reply": reply.tolist() if not receipt_fit else None,
            }
    assert count.sum() == max(spec["observations"])
    return snapshots, log


def frozen_route(checkpoint, observed, setting):
    if checkpoint["estimate"] is not None:
        return best_route(np.array(checkpoint["estimate"]), observed, setting)
    return ((np.array(checkpoint["sender"]) @ team.features(*setting[:3])) > 0,
            (np.array(checkpoint["reply"]) > 0).astype(int))


def run(spec):
    data, joined = prior.environment()
    banks = {name: receipt_bank(data, scores) for name, scores in joined.items()}
    compact = banks["compact_ungated"]
    fits = {}
    for algorithm, (arm, peer) in product(("receipt_value", "reinforce"), CONTENT.items()):
        fits[f"{algorithm}/{arm}"] = train(compact, view_observations(data, peer), spec,
                                           algorithm == "receipt_value")
    typed = banks["typed"]
    held = spec["held"]
    names = ("utility", "released", "send_cost", "supported_comparison", "zero_release_pair")
    report = {}
    for count in spec["observations"]:
        report[count] = {}
        for bank in sorted(banks.keys() - {"typed"}):
            receipts = banks[bank]
            records = []
            for q0, q1, cost, mass in product(held["delivery"], held["delivery"], held["prices"], held["priors"]):
                setting = (q0, q1, cost, np.array(mass))
                measured = {}
                for arm, peer in CONTENT.items():
                    observed = view_observations(data, peer)
                    measured[f"oracle/{arm}"] = pay(receipts, observed, setting,
                                                   *best_route(receipts, observed, setting))
                    measured[f"typed_rule/{arm}"] = pay(receipts, observed, setting,
                                                       *best_route(typed, observed, setting))
                    for algorithm in ("receipt_value", "reinforce"):
                        key = f"{algorithm}/{arm}"
                        measured[key] = pay(receipts, observed, setting,
                                            *frozen_route(fits[key][0][count], observed, setting))
                    assert all(row[0] <= measured[f"oracle/{arm}"][0] + 1e-7
                               for key, row in measured.items() if key.endswith(f"/{arm}"))
                records.append({"setting": [q0, q1, cost, mass],
                                "arms": {arm: value.round(8).tolist() for arm, value in measured.items()}})
            metrics = {key: dict(zip(names, np.mean([row["arms"][key] for row in records],
                                                   axis=0).round(8).tolist(), strict=True))
                       for key in records[0]["arms"]}
            report[count][bank] = {"summary": metrics, "rows": records}
    return {"receipts": list(range(12)), "reward_tables": {k: v.tolist() for k, v in banks.items()},
            "fits": {key: {"checkpoints": fit[0], "training": fit[1]} for key, fit in fits.items()},
            "evaluation": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    spec = plan()
    if not args.plan:
        assert spec == json.loads((HERE / "plan.json").read_text())
    print(json.dumps(spec if args.plan else run(spec), indent=2))


if __name__ == "__main__":
    main()
