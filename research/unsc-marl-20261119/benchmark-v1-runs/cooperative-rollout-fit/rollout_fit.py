"""Fit chair and reply residual values from counterfactual episode returns."""
import argparse
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
TRIB = HERE.parent / "tribunals-v14-transfer"
sys.path.insert(0, str(TRIB))
from routing_transfer import NUMBERED, POLICY, a, digest, f, interval, o, wire

D = interval.D
FIXED = np.array([np.where(D.CHAIR_LEGAL[:, i], i, 0) for i in range(4)])
BITS = np.array((0, 1, 2, 4))
LEGAL = np.broadcast_to(D.FINAL_LEGAL, (8, 4, 4, 4))
TRAIN = 48
DRAWS = 192
ROUNDS = 3
RIDGE = .01
SEED = 20261122
SMOOTHING = .10
SHIFT = POLICY.parent
SPARSE = interval.a.m.HERE.parent / "sparse-results.json"
TRANSFER = TRIB / "constrained/transfer"
INITIAL = o.replan.study.OLD


def centered(bank):
    return tuple(np.asarray(bank) - bank[0])


def plan():
    all_banks = wire.n.read(SPARSE)["training"]
    assert len(set(map(tuple, all_banks))) == len(all_banks)
    train = all_banks[:TRAIN]
    held = wire.n.read(TRANSFER / "plan.json")["banks"]
    assert not {centered(bank) for bank in train} & {centered(bank) for bank in held.values()}
    assert len(train) == TRAIN and len(held) == 5
    pins = (Path(__file__).resolve(), HERE / "protocol.md", SPARSE, INITIAL, TRANSFER / "plan.json",
            Path(o.__file__), Path(interval.__file__), Path(f.__file__), Path(a.__file__))
    return {"seed": SEED, "rounds": ROUNDS, "samples_per_context": DRAWS, "ridge": RIDGE,
            "smoothing": SMOOTHING, "training_banks": train, "test_banks": held,
            "base_laws": list(o.R.TEST_PRIORS), "offsets": [-7, 0, 7],
            "sha256": {str(p.relative_to(TRIB.parents[1])): digest(p) for p in pins}}


def context(points, observed, announced, init):
    opening = o.replan.study.opening(f.views(points)["4"], announced, init)
    mass = o.opening(*opening, announced)
    grades = {key: points[key] for key in (0, 1, 2, 4, 5, 6)}
    forecast = interval.forecasts(grades, observed)
    return opening, mass, forecast


def observation(queries, explore):
    policy = D.one_hot(queries)
    if explore:
        uniform = D.CHAIR_LEGAL / D.CHAIR_LEGAL.sum(-1, keepdims=True)
        policy = (1 - SMOOTHING) * policy + SMOOTHING * uniform
    return o.fit.heard(policy)


def act(features, forecast, weights, legal):
    residual = features @ weights
    priorities = np.where(legal, forecast + residual, -np.inf)
    return priorities.argmax(-1)


def responder_features(points, mass, queries):
    heard = observation(queries, True)
    value = o.payoff(points)[:, 0, :]
    delta = value - value[:, :1]
    visits = np.einsum("rbm,mt->rbt", mass, heard)
    weighted = np.einsum("rbm,mt,mc->rbtc", mass, heard, delta)
    expected = weighted / visits[..., None].clip(min=1e-12)
    missing = ((np.arange(8)[:, None] & BITS) == 0) & (BITS != 0)
    receipt = np.einsum("rbm,mt,mc->rbtc", mass, heard, missing) / visits[..., None].clip(min=1e-12)
    _, own, signal, action = np.ix_(np.arange(8), np.arange(4), np.arange(4), np.arange(4))
    templates = [(action != 0), ((signal == action) & (signal != 0)), ((own == action) & (action != 0)),
                 (signal != 0), D.SEND_COST.reshape(1, 1, 1, 4)]
    flags = [np.broadcast_to(v, expected.shape) for v in templates]
    feature = np.stack((expected / 10, receipt, *flags), axis=-1)
    feature[..., 0, :] = 0
    return feature, expected


def chair_features(points, mass, replies):
    value = o.payoff(points)[:, 0, :]
    terminal = np.einsum("rbm,rbtc,mc->mt", mass, D.one_hot(replies), value)
    visits = mass.sum((0, 1))
    change = (1 - D.LOSS) * (terminal - terminal[:, :1]) / visits[:, None].clip(min=1e-12)
    expected = change - D.QUERY_COST
    probabilities = np.einsum("rbm,rt->mt", mass, D.FINAL_LEGAL[:, 0, 0])
    rate = probabilities / visits[:, None].clip(min=1e-12)
    available = rate * (np.arange(4) != 0)
    costs = np.broadcast_to(D.QUERY_COST, expected.shape)
    signal = np.broadcast_to(np.arange(4) != 0, expected.shape)
    number = np.array([i.bit_count() for i in range(8)])[:, None]
    feature = np.stack((expected / 10, available, costs, signal,
                        signal * number / 3, expected * available / 10), axis=-1)
    return feature, expected


def start(forecast, mass):
    scripted = D.scripts()[3]
    features, payoff = chair_features(forecast, mass, scripted)
    return act(features, payoff, np.zeros(features.shape[-1]), D.CHAIR_LEGAL)


def deploy(forecast, mass, history):
    q = start(forecast, mass)
    for reply_weights, chair_weights in history:
        features, values = responder_features(forecast, mass, q)
        r = act(features, values, reply_weights, LEGAL)
        features, values = chair_features(forecast, mass, r)
        q = act(features, values, chair_weights, D.CHAIR_LEGAL)
    # Replies condition on the actual deployed chair. This incurs no simulator calls.
    features, values = responder_features(forecast, mass, q)
    r = act(features, values, history[-1][0], LEGAL)
    return q, r


def rolls(law, opening, rng):
    worlds = rng.choice(64, DRAWS, p=law.ravel())
    left, right = worlds // 8, worlds % 8
    own = opening[1][right]
    ok = rng.random((DRAWS, 4)) >= D.LOSS
    receipt = BITS[opening[0][left]] * ok[:, 0] | BITS[own] * ok[:, 1]
    return right, own, receipt, ok


def fit_ridge(features, targets):
    x = np.concatenate(features, axis=0)
    y = np.concatenate(targets)
    lhs = x.T @ x / len(x) + RIDGE * np.eye(x.shape[-1])
    w = np.linalg.solve(lhs, x.T @ y / len(y))
    before = float(np.mean(y ** 2))
    after = float(np.mean((y - x @ w) ** 2))
    assert after <= before + 1e-12 and np.isfinite(w).all()
    return w, {"action_samples": len(x), "residual_mse_before": before, "residual_mse_after": after}


def train(locked, init):
    contexts = []
    for bank, law, shift in product(locked["training_banks"], o.R.TEST_PRIORS.values(), locked["offsets"]):
        points = np.array(bank, dtype=float)
        opening, mass, forecast = context(points, np.clip(points[3] + shift, 0, 70), law, init)
        contexts.append((points, law, opening, mass, forecast))
    rng = np.random.default_rng(locked["seed"])
    history, trace = [], []
    for step in range(ROUNDS):
        reply_x, reply_y, state = [], [], []
        for points, law, opening, mass, forecast in contexts:
            query = deploy(forecast, mass, history)[0] if history else start(forecast, mass)
            right, own, receipt, ok = rolls(law, opening, rng)
            # Draw heard signals from the same randomized request model used in the posterior.
            request_prob = (1 - SMOOTHING) * D.one_hot(query) + SMOOTHING * (
                D.CHAIR_LEGAL / D.CHAIR_LEGAL.sum(-1, keepdims=True))
            draws = rng.random(DRAWS)
            telegraph = (draws[:, None] >= np.cumsum(request_prob[receipt], axis=-1)).sum(-1).clip(max=3)
            heard = telegraph * ok[:, 2]
            feat, estimate = responder_features(forecast, mass, query)
            reward = points[receipt[:, None] | BITS * ok[:, 3, None]] - points[receipt, None] - D.SEND_COST
            legal = LEGAL[right, own, heard]
            reply_x.append(feat[right, own, heard][legal])
            reply_y.append((reward - estimate[right, own, heard])[legal])
            state.append(query)
        answer, reply_trace = fit_ridge(reply_x, reply_y)
        chair_x, chair_y = [], []
        for (points, law, opening, mass, forecast), query in zip(contexts, state, strict=True):
            rf, estimate = responder_features(forecast, mass, query)
            replies = act(rf, estimate, answer, LEGAL)
            cf, estimate = chair_features(forecast, mass, replies)
            right, own, receipt, ok = rolls(law, opening, rng)
            heard = np.arange(4) * ok[:, 2, None]
            sent = replies[right[:, None], own[:, None], heard]
            completed = receipt[:, None] | BITS[sent] * ok[:, 3, None]
            values = points[completed] - D.SEND_COST[sent] - D.QUERY_COST
            gain = values - values[:, :1]
            legal = D.CHAIR_LEGAL[receipt]
            chair_x.append(cf[receipt][legal])
            chair_y.append((gain - estimate[receipt])[legal])
        chair, chair_trace = fit_ridge(chair_x, chair_y)
        history.append((answer, chair))
        trace.append({"round": step + 1, "reply": reply_trace, "chair": chair_trace})
    return history, trace, len(contexts)


def metric(points, law, opening, policy):
    row = o.measure(points, o.opening(*opening, law), law, opening, policy)
    return {k: float(row[k]) for k in ("released", "cost", "net", "queries")}


def test(locked, history, init):
    rows = []
    neutral = [(np.zeros_like(r), np.zeros_like(q)) for r, q in history]
    for (case, bank), (label, (true, proxy)), prior_type, offset in product(
            locked["test_banks"].items(), a.laws().items(), ("exact", "dominant_only"), locked["offsets"]):
        points = np.array(bank, dtype=float)
        announced = true if prior_type == "exact" else proxy
        opening, mass, forecast = context(points, np.clip(points[3] + offset, 0, 70), announced, init)
        fixed = [(q, o.choose_response(q, mass, forecast)) for q in FIXED]
        match = max(fixed, key=lambda arm: metric(forecast, announced, opening, arm)["net"])
        policies = {"learned": deploy(forecast, mass, history), "no_fit": deploy(forecast, mass, neutral),
                    "fixed_forecast": match, "exact_forecast": o.exact_parts(mass, forecast)["exact_ask_reply"]}
        values = {name: metric(points, true, opening, arm) for name, arm in policies.items()}
        actual = o.controls(points, o.opening(*opening, true), true, opening)
        values["informed_fixed"] = {k: float(x) for k, x in max(
            (v for k, v in actual.items() if k != "exact_ask_reply"), key=lambda v: v["net"]).items()
            if k in ("released", "cost", "net", "queries")}
        values["informed_adaptive"] = {k: float(actual["exact_ask_reply"][k]) for k in ("released", "cost", "net", "queries")}
        assert all(r["net"] <= values["informed_adaptive"]["net"] + 1e-9 for r in values.values())
        rows.append({"case": case, "law": label, "information": prior_type, "review_offset": offset,
                     "silence_quality": actual["exact_no_request"]["released"], "outcomes": values,
                     "learned_policy": [v.tolist() for v in policies["learned"]],
                     "opening": [v.tolist() for v in opening]})
    return rows


def compare(values):
    return {"wins": sum(x > 1e-9 for x in values), "losses": sum(x < -1e-9 for x in values),
            "ties": sum(abs(x) <= 1e-9 for x in values), "mean": mean(values)}


def summarize(rows):
    result = {}
    for case in ["all", *sorted({r["case"] for r in rows})]:
        group = [r for r in rows if case == "all" or r["case"] == case]
        learned = [r["outcomes"]["learned"] for r in group]
        result[case] = {
            "conditions": len(group),
            "learned_below_silence": sum(out["released"] < r["silence_quality"] - 1e-9
                                         for out, r in zip(learned, group, strict=True)),
            "learned_mean_queries": mean(out["queries"] for out in learned),
            **{f"learned_vs_{ref}": compare([out["net"] - r["outcomes"][ref]["net"]
                                            for out, r in zip(learned, group, strict=True)])
               for ref in ("no_fit", "fixed_forecast", "exact_forecast", "informed_fixed", "informed_adaptive")},
        }
    return result


def run():
    locked = wire.n.read(HERE / "plan.json")
    assert locked == plan()
    init = wire.n.read(INITIAL)["training"]["budget_fit"]
    history, trace, contexts = train(locked, init)
    rows = test(locked, history, init)
    assert len(rows) == 90
    return {"numpy": np.__version__, "training_contexts": contexts, "trace": trace,
            "weights": [[v.tolist() for v in row] for row in history], "summary": summarize(rows),
            "rows": rows, "plan_sha256": digest(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
