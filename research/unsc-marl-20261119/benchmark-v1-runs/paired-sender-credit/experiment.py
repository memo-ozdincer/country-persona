"""Test paired counterfactual sender credit on native-scored diplomatic outcomes."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
PREVIOUS = RUNS / "native-relation-team-fit"
sys.path.insert(0, str(PREVIOUS))
import fit

team = fit.team
CHECKPOINTS = (1, 32, 64, 128, 256, team.UPDATES)


def plan():
    paths = (Path(__file__), HERE / "protocol.md", PREVIOUS / "fit.py", PREVIOUS / "plan.json",
             PREVIOUS / "results.json", PREVIOUS / "sender-ceiling.json", Path(team.__file__))
    return {"base": team.plan(), "cpu": "numpy", "checkpoints": list(CHECKPOINTS),
            "terminal_scores_per_update": {"sampled": team.BATCH, "sampled_double": 2*team.BATCH,
                                           "paired": 2*team.BATCH},
            "sha256": {str(p.relative_to(RUNS)): sha256(p.read_bytes()).hexdigest() for p in paths}}


def pooled_pair(table):
    """Use the sampled receiver update and average out the sender's own action."""
    public, first_only, last_only, both, observed = table
    rng = np.random.default_rng(team.SEED)
    n = team.BATCH
    sender = np.zeros((2, 3, 5))
    receiver = np.zeros((2, 3))
    s1, s2 = np.zeros_like(sender), np.zeros_like(sender)
    r1, r2 = np.zeros_like(receiver), np.zeros_like(receiver)
    baseline = np.array([35., 45.])
    checkpoints = []
    for step in range(1, team.UPDATES+1):
        d = rng.integers(2, size=n)
        v = rng.integers(3, size=n)
        q0 = rng.choice(team.TRAIN_DELIVERY, size=n)
        q1 = rng.choice(team.TRAIN_DELIVERY, size=n)
        price = rng.choice(team.TRAIN_PRICES, size=n)
        x = team.features(q0, q1, price)
        p_send = team.sigmoid(np.sum(sender[d, v] * x, axis=1))
        sent = rng.random(n) < p_send
        delivery = rng.random(n) < q0
        u_reply = rng.random(n)
        back = rng.random(n) < q1
        obs_if_send = np.where(delivery, observed[d, v], 0)
        p_if_send = team.sigmoid(receiver[d, obs_if_send])
        p_if_silent = team.sigmoid(receiver[d, 0])
        a_if_send = (u_reply < p_if_send).astype(int)
        a_if_silent = (u_reply < p_if_silent).astype(int)
        r_if_silent = np.where(back, last_only[d, a_if_silent], public[d])
        r_if_send = np.where(delivery, np.where(back, both[d, v, a_if_send], first_only[d, v]),
                             r_if_silent) - price
        assert np.all(r_if_send[~delivery] == r_if_silent[~delivery] - price[~delivery])
        observed_reply = np.where(sent, obs_if_send, 0)
        a_reply = np.where(sent, a_if_send, a_if_silent)
        p_reply = np.where(sent, p_if_send, p_if_silent)
        reward = np.where(sent, r_if_send, r_if_silent)
        advantage = (reward - baseline[d]) / 10
        grad_s = np.zeros_like(sender)
        grad_r = np.zeros_like(receiver)
        score_s = (r_if_send-r_if_silent) * p_send * (1-p_send) / 10
        np.add.at(grad_s, (d, v), x * score_s[:, None] / n)
        np.add.at(grad_r, (d, observed_reply), advantage * (a_reply-p_reply) / n)
        sender, s1, s2 = team.adam(sender, grad_s, s1, s2, step)
        receiver, r1, r2 = team.adam(receiver, grad_r, r1, r2, step)
        for family in range(2):
            baseline[family] = .95*baseline[family] + .05*np.mean(reward[d == family])
        if step in CHECKPOINTS:
            checkpoints.append({
                "update": step, "mean_batch_utility": round(float(np.mean(reward)), 8),
                "sender_gradient_norm": round(float(np.linalg.norm(grad_s)), 8),
                "receiver_gradient_norm": round(float(np.linalg.norm(grad_r)), 8),
                "sender": sender.round(10).tolist(), "receiver": receiver.round(10).tolist(),
            })
    return sender, receiver, checkpoints


def send_audit(table, held):
    public, first, last, both, observed = table
    families = list(team.PRIVATE)
    counts = {name: Counter() for name in families}
    for row in held:
        family = row["family"]
        d = families.index(family)
        policy = row["native_fit"]
        mapping = np.array(policy["reply"])
        q0, q1, price = (row[key] for key in ("q_first", "q_reply", "cost"))
        alone = (1-q1)*public[d] + q1*last[d, mapping[0]]
        front = (1-q1)*first[d] + q1*both[d, np.arange(3), mapping[observed[d]]]
        gap = q0*(front-alone)-price
        for name, shown, gain in zip(team.PRIVATE[family], policy["send"], gap, strict=True):
            if abs(gain) > 1e-9 and bool(shown) != (gain > 0):
                counts[family][name] += 1
    return {key: dict(value) for key, value in counts.items()}


def run():
    spec = plan()
    assert spec == fit.read(HERE / "plan.json")
    old = fit.read(PREVIOUS / "results.json")
    tables, _ = fit.tables(old["grades"])
    trusted, audited = tables["trusted_native"], tables["audited_native"]
    sample = team.train(trusted)
    assert sample[2] == old["history"]
    with patch.object(team, "BATCH", 2*team.BATCH):
        double = team.train(trusted)
    paired = pooled_pair(trusted)
    assert paired[2][0]["mean_batch_utility"] == sample[2][0]["mean_batch_utility"]
    assert paired[2][0]["receiver"] == sample[2][0]["receiver"]
    assert paired[2][0]["sender"] != sample[2][0]["sender"]
    result = {}
    for key, (sender, receiver, history) in (("sampled", sample), ("sampled_double", double), ("paired", paired)):
        report = fit.compare(audited, (sender, receiver), sample[:2])
        result[key] = {"terminal_queries": spec["terminal_scores_per_update"][key]*team.UPDATES,
                       "history": history, "evaluation": report,
                       "sender_mismatches": send_audit(audited, report["held"])}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    print(json.dumps(plan() if parser.parse_args().plan else run(), ensure_ascii=False, indent=2))
