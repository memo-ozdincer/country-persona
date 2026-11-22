"""Fit a joint post-proof question and disclosure policy on synthetic states."""
from collections import Counter
from hashlib import sha256
from math import exp, sqrt
from pathlib import Path

import environment as env

UPDATES = 120
ROLE = env.ROLES
ACTIONS = ("silence", *ROLE)
FEE = env.COSTS["mandate_target"]
LR = .22


def start_states(row, fitted):
    """Replay the frozen first stage, averaging synthetic compatible mandates."""
    initial = row["before"]
    delivery = row["delivery"]
    policy = env.exact(row, 0., env.ACTIONS[:2])
    if policy["action"] == "silence":
        return [(initial, 1., False, 0.)]
    branches = row["worlds"]["sign"]
    chosen = tuple(branches.values()) if fitted else (branches[row["truth"]["sign"]],)
    scenarios = []
    for after in chosen:
        weight = 1 / len(chosen)
        gain = delivery * (env.utility(env.outcome(after), 0) - env.utility(env.outcome(initial), 0))
        if gain > env.COSTS["sign"]:
            scenarios.extend([(after, weight * delivery, True, env.ASK + env.COSTS["sign"]),
                              (initial, weight * (1-delivery), True, env.ASK + env.COSTS["sign"])])
        else:
            scenarios.append((initial, weight, False, env.ASK))
    assert abs(sum(s[1] for s in scenarios) - 1.) < 1e-10
    return scenarios


def features(state, role, delivery):
    other = ROLE[1 - ROLE.index(role)]
    missing = len(state["candidates"][role]) > 1
    other_known = len(state["candidates"][other]) == 1
    return (1., float(missing), float(other_known), float(missing and other_known), delivery)


def components(state, delivery, heads):
    xs = [features(state, role, delivery) for role in ROLE]
    chair, reply = heads
    route = [0.] + [sum(w*x for w,x in zip(chair, ft, strict=True)) for ft in xs]
    offset = max(route)
    route = [exp(v-offset) for v in route]
    chair_policy = [v/sum(route) for v in route]
    response = [1/(1+exp(-sum(w*x for w,x in zip(reply, ft, strict=True)))) for ft in xs]
    can_finish = [bool(x[3]) for x in xs]
    return xs, chair_policy, response, can_finish


def reward(can_finish, probability, delivery):
    return probability * (env.BONUS * delivery * can_finish - FEE) - env.ASK


def fit(events):
    dim = 5
    weights = [[0.] * dim for _ in range(2)]
    accum = [[0.] * dim for _ in range(2)]
    trace = []
    count = sum(w for _, _, w in events)
    for step in range(UPDATES+1):
        grad = [[0.] * dim for _ in range(2)]
        objective = 0.
        for state, delivery, weight in events:
            xs, chair_policy, response, finish = components(state, delivery, weights)
            p = chair_policy[1:]
            values = [reward(g, r, delivery) for g,r in zip(finish, response, strict=True)]
            expected = sum(probability * v for probability,v in zip(p, values, strict=True))
            objective += expected * weight / count
            for x, route, send, gain, value in zip(xs, p, response, finish, values, strict=True):
                for i in range(dim):
                    grad[0][i] += weight / count * route * (value - expected) * x[i]
                    utility_delta = env.BONUS * delivery * gain - FEE
                    grad[1][i] += weight / count * route * send * (1-send) * utility_delta * x[i]
        trace.append({"updates": step, "expected_incremental_train_reward": objective})
        if step == UPDATES:
            break
        for w, g, a in zip(weights, grad, accum, strict=True):
            for i in range(dim):
                a[i] += g[i]**2
                w[i] += LR * g[i] / sqrt(a[i] + 1e-8)
    return weights, trace


def evaluate(row, mode, heads, followup_delivery=None):
    first = start_states(row, False)
    result = Counter(proof=0., ready=0., cost=0., extra_questions=0., extra_sends=0.)
    for state, weight, _, cost in first:
        delivery = row["delivery"] if followup_delivery is None else followup_delivery
        base = env.outcome(state, cost)
        for key, value in zip(("proof", "ready", "cost"), base, strict=True):
            result[key] += weight * value
        if not base[0] or mode == "no_followup":
            continue
        _, p, send, gains = components(state, delivery, heads)
        if mode == "learned_team":
            pick = max(range(3), key=p.__getitem__)
            respond = pick > 0 and send[pick-1] > .5
        elif mode == "always_first_recipient":
            # The original question names one role, even when its first policy stays silent.
            pick = ROLE.index(row["named"]) + 1
            respond = True
        else:
            choices = [i+1 for i, g in enumerate(gains) if g]
            pick = choices[0] if choices and (mode == "ask_ambiguous_role" or reward(True, 1., delivery) > 1e-12) else 0
            respond = pick > 0
        if pick:
            result["extra_questions"] += weight
            result["cost"] += weight * env.ASK
            if respond:
                result["extra_sends"] += weight
                result["cost"] += weight * FEE
                result["ready"] += weight * delivery * gains[pick-1]
    result["net"] = result["proof"] + env.BONUS * result["ready"] - result["cost"]
    return dict(result)


def run():
    rows = list(env.records())
    training = []
    held = []
    for split, row in rows:
        if split == "train":
            assert row["id"].startswith("synthetic-") and not row["truth"]
            training.extend((s, row["delivery"], w) for s,w,_,_ in start_states(row, True)
                            if s["decision"] != "U")
        else:
            held.append(row)
    assert training and len(held) == 44
    heads, trace = fit(training)
    assert trace[-1]["expected_incremental_train_reward"] > trace[0]["expected_incremental_train_reward"]
    arms = ("no_followup", "always_first_recipient", "ask_ambiguous_role", "exact_cost_aware", "learned_team")
    details = {row["id"]: {mode: evaluate(row, mode, heads) for mode in arms} for row in held}
    summary = {}
    for mode in arms:
        entries = [r[mode] for r in details.values()]
        totals = {field: sum(r[field] for r in entries) for field in entries[0]}
        totals["mean_net"] = totals["net"]/len(entries)
        summary[mode] = totals
    assert all(abs(v["proof"] - summary["no_followup"]["proof"]) < 1e-9 for v in summary.values())
    files = (Path(__file__), env.HERE / "environment.py", env.HERE / "followup-protocol.md", env.HERE / "exact.json")
    return {"fit": {"heads": heads, "trace": trace, "updates": UPDATES, "weighted_states": sum(w for _,_,w in training),
                    "terminal_training_paths": len(training)},
            "summary": summary, "held": details,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    env.E.emit(run())
