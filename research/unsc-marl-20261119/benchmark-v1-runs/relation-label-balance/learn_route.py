"""Fit decentralized rechecks against the measured option-order channels."""
from itertools import product
from pathlib import Path
from statistics import mean
from collections import Counter
import json

import numpy as np

import score
import balance as study

HERE, team = study.HERE, study.team
STEPS, RATE, L2, COST = 160, .2, .02, .1
THRESHOLDS = (-1., .25, .5, 1., 2., 100.)


def payoff(label, gold):
    return 0. if label == 2 else 1. if label == gold else -2.


def encode(rows, key, family, expected):
    first, *rest = map(team.mapped, rows)
    cycles = rest[-2:]
    scores, local = first
    gap = scores[local] - max(scores[i] for i in range(3) if i != local)
    x = np.array([1., np.tanh(gap), float(local == 2), float(local == 1)])
    base = [2, local]
    second_rows, second_labels = [], []
    for values, label in cycles:
        own_gap = values[label] - max(values[i] for i in range(3) if i != label)
        peer_gap = values[local] - max(values[i] for i in range(3) if i != local)
        second_rows.append([1., np.tanh(own_gap), np.tanh(peer_gap), float(label == local),
                            float(label == 2), float(local == 2)])
        second_labels.append([2, local, label])
    z = np.asarray(second_rows)
    legal = np.asarray([[True, l != 2, s != 2 and s != l] for _, l, s in second_labels])
    truth = team.LABELS.index(expected)
    policy_payoff = np.array([[payoff(y, truth) for y in vals] for vals in second_labels])
    opening = [payoff(i, truth) for i in base]
    balanced, _ = score.decode(rows)
    return {"key":key, "family":family, "gold":truth, "x":x, "z":z, "first":local, "gap":float(gap),
            "opening":opening, "legal":legal, "labels":second_labels, "reply_rewards":policy_payoff,
            "balanced":balanced["balanced_unanimous"]}


def load():
    from collections import defaultdict
    combined = defaultdict(dict)
    for row in study.old_rows() + [json.loads(s) for s in (study.OUT / "calls.jsonl").read_text().splitlines()]:
        group, key, position = row["observation"]
        combined[group, key][position] = row
    gold = study.e.read(HERE / "results.json")["decisions"]
    assert len(combined) == len(gold) == 27
    return [encode([combined["routed" if r["cohort"] == "archive" else "held", r["case"]][i]
                    for i in range(4)], r["case"], r["case"].split("/")[0] if r["cohort"] == "archive"
                    else "myanmar", r["truth"]) for r in gold]


def softmax(z, legal):
    z = np.where(legal, z, -np.inf)
    exp = np.exp(z - z.max(axis=-1, keepdims=True))
    return exp / exp.sum(axis=-1, keepdims=True)


def strategies(row, weights):
    proposer, receiver = weights
    return softmax(row["x"] @ proposer, [True, row["first"] != 2, True, True]), softmax(
        row["z"] @ receiver, row["legal"])


def fit(rows):
    weights = (np.zeros((4,4)), np.zeros((6,3)))
    counts = Counter(r["family"] for r in rows)
    def objective(weights):
        a, b = (np.zeros_like(w) for w in weights)
        reward = 0.
        for row in rows:
            p, q = strategies(row, weights)
            selected = np.sum(q * row["reply_rewards"], axis=1)
            branch = np.r_[row["opening"], selected - COST]
            norm = len(counts) * counts[row["family"]]
            value = float(p @ branch)
            reward += value / norm
            a += np.outer(row["x"], p * (branch - value)) / norm
            dw = p[2:,None] * q * (row["reply_rewards"] - selected[:,None])
            b += row["z"].T @ dw / norm
        return reward, (a - L2 * weights[0], b - L2 * weights[1])
    before, (a, b) = objective(weights)
    for w, g in enumerate((a, b)):
        for cell in np.ndindex(g.shape):
            trial = [v.copy() for v in weights]
            trial[w][cell] += 1e-5
            up = objective(trial)[0]
            trial[w][cell] -= 2e-5
            down = objective(trial)[0]
            assert abs((up-down)/2e-5-g[cell]) < 1e-8
    for _ in range(STEPS):
        _, gradient = objective(weights)
        weights = tuple(w+RATE*g for w,g in zip(weights,gradient,strict=True))
    after, _ = objective(weights)
    assert after >= before
    return weights, [before, after]


def routed(row, cycle, threshold, mode):
    local = row["first"]
    if row["gap"] > threshold:
        return local, 0
    _, first, second = row["labels"][cycle]
    assert first == local
    picked = second if mode == "second" else first if first == second else 2
    return picked, 1


def stats(row, action, q):
    label = (2, row["first"])[action] if action < 2 else row["labels"][action-2][q]
    return float(payoff(label,row["gold"]) - COST*(action>=2)), int(action>=2), label


def select_fixed(train):
    count = Counter(row["family"] for row in train)
    def objective(rule):
        result = 0.
        for row in train:
            label, paid = routed(row, *rule)
            result += (payoff(label,row["gold"])-COST*paid) / (len(count)*count[row["family"]])
        return result
    menu = product(range(2), THRESHOLDS, ("agreement","second"))
    return max(menu, key=objective)


def compare(row, weights, fixed):
    p, q = strategies(row, weights)
    action = int(p.argmax())
    reply = int(q[action-2].argmax()) if action >= 2 else 0
    value, count, label = stats(row, action, reply)
    policies = {"learned": (value,count,label)}
    sampled = 0.
    for a in range(4):
        if a < 2:
            sampled += p[a]*stats(row,a,0)[0]
        else:
            sampled += p[a]*sum(pr*stats(row,a,r)[0] for r,pr in enumerate(q[a-2]))
    references = {"first_only": (row["first"],0), "fixed_train":routed(row,*fixed),
                  "cycles_unanimous_three": (row["balanced"],2)}
    for cycle in range(2):
        for mode in ("second","agreement"):
            references[f"always_{cycle}_{mode}"] = routed(row, cycle, 100., mode)
    for name,(choice,paid) in references.items():
        policies[name] = (payoff(choice,row["gold"])-COST*paid,paid,choice)
    oracle = max(stats(row,a,r)[0] for a in range(4) for r in range(3))
    assert all(row_[0] <= oracle+1e-9 for row_ in policies.values())
    return {"case":row["key"],"truth":team.LABELS[row["gold"]],
            "policy":{name:{"net":v,"checks":n,"relation":team.LABELS[label]}
                      for name,(v,n,label) in policies.items()},
            "sampled_net": float(sampled), "sampled_checks":float(p[2:].sum()), "oracle":oracle}


def trial(train,test):
    w, trace = fit(train)
    fixed = select_fixed(train)
    rows = [compare(r,w,fixed) for r in test]
    metrics = {name:{k:mean(r["policy"][name][k] for r in rows) for k in ("net","checks")}
               for name in rows[0]["policy"]}
    return {"fit_families": sorted({r["family"] for r in train}), "weights":[x.tolist() for x in w],
            "fit_objective":trace,"fixed_rule":fixed, "results":rows, "means":metrics,
            "sampled_net":mean(r["sampled_net"] for r in rows),"oracle":mean(r["oracle"] for r in rows)}


def run():
    sources = (Path(__file__), HERE/"routing-protocol.md",HERE/"verified.json",HERE/"results.json")
    records = load()
    kept = [r for r in records if r["family"] != "myanmar"]
    families = sorted({r["family"] for r in kept})
    folds = {name: trial([r for r in kept if r["family"]!=name], [r for r in kept if r["family"]==name])
             for name in families}
    macro = {arm:{metric: mean(fold["means"][arm][metric] for fold in folds.values()) for metric in ("net","checks")}
             for arm in folds[families[0]]["means"]}
    return {"folds":folds,"archive_macro":macro,
            "myanmar":trial(kept,[r for r in records if r["family"]=="myanmar"]),
            "sha256":{p.name:team.pin(p) for p in sources}}


if __name__ == "__main__":
    study.e.emit(run())
