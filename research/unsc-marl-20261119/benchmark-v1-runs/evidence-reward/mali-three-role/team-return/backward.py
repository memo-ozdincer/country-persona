"""Train a decentralized team with sampled finite-horizon returns."""
from functools import cache
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

import numpy as np

import train as core

HERE = Path(__file__).resolve().parent
SEED = 83
ROWS = 12_288
WIDTH = 144


def basis(x, projection, bias):
    return np.concatenate((x, np.ones((*x.shape[:-1], 1)), np.tanh(x @ projection + bias)), axis=-1)


def fit(x, y, rng):
    projection = rng.normal(0, 1.7, (x.shape[1], WIDTH))
    bias = rng.normal(0, .8, WIDTH)
    features = basis(x, projection, bias)
    ridge = .1 * np.eye(features.shape[-1])
    weights = np.linalg.solve(features.T @ features + ridge, features.T @ y)
    return projection, bias, weights


def predict(x, model):
    projection, bias, weights = model
    return basis(x, projection, bias) @ weights


def ask_batch(menu, state, rates, left, chair):
    obs = core.features(menu, state, rates, np.full(len(state), left))
    scores = np.where(state < 0, predict(obs, chair), -np.inf)
    selected = scores.argmax(axis=1)
    active = scores[np.arange(len(state)), selected] > 0.
    return selected, active


def reply_batch(menu, state, rates, left, truth, roles, delegate):
    obs = core.features(menu, state, rates, np.full(len(state), left), truth)
    return predict(obs[np.arange(len(state)), roles], delegate) > 0.


def proceed(state, truth, roles, received):
    after = state.copy()
    selected = np.flatnonzero(received)
    after[selected, roles[selected]] = truth[selected, roles[selected]]
    return after


def continuation(menu, state, rates, truth, left, heads, draws):
    spent = np.zeros(len(state))
    active = np.ones(len(state), dtype=bool)
    for horizon in range(left, 0, -1):
        chair, delegate = heads[horizon]
        roles, ask = ask_batch(menu, state, rates, horizon, chair)
        active &= ask
        send = active & reply_batch(menu, state, rates, horizon, truth, roles, delegate)
        received = send & (draws[horizon - 1] < rates[np.arange(len(state)), roles])
        spent += core.QUERY_COST * active + core.SEND_COST * send
        state = proceed(state, truth, roles, received)
    return core.credit(menu, state)[2] - spent


def context(menus, rng, left):
    menu = menus[rng.integers(len(menus), size=ROWS)]
    truth = rng.integers(2, size=(ROWS, 3))
    rates = rng.choice(core.TRAIN_RATES, size=(ROWS, 3))
    roles = rng.integers(3, size=ROWS)
    reveal = rng.random((ROWS, 3)) < (0. if left == 3 else .42)
    reveal[np.arange(ROWS), roles] = False
    state = np.where(reveal, truth, -1)
    draws = rng.random((left, ROWS))
    delivered = draws[-1] < rates[np.arange(ROWS), roles]
    return menu, state, rates, truth, roles, draws, delivered


def learn(menus):
    rng = np.random.default_rng(SEED)
    heads = {}
    trace = {}
    for left in (1, 2, 3):
        menu, state, rates, truth, roles, draws, delivered = context(menus, rng, left)
        rows = np.arange(ROWS)
        hit = proceed(state, truth, roles, delivered)
        yes = continuation(menu, hit, rates, truth, left - 1, heads, draws)
        no = continuation(menu, state, rates, truth, left - 1, heads, draws)
        local = core.features(menu, state, rates, np.full(ROWS, left), truth)[rows, roles]
        delegate = fit(local, yes - no - core.SEND_COST, rng)

        menu, state, rates, truth, roles, draws, delivered = context(menus, rng, left)
        send = reply_batch(menu, state, rates, left, truth, roles, delegate)
        after = proceed(state, truth, roles, send & delivered)
        future = continuation(menu, after, rates, truth, left - 1, heads, draws)
        goal = future - core.credit(menu, state)[2] - core.QUERY_COST - core.SEND_COST * send
        obs = core.features(menu, state, rates, np.full(ROWS, left))[rows, roles]
        chair = fit(obs, goal, rng)
        heads[left] = chair, delegate
        trace[left] = {"prefix_length_counts": np.bincount((state >= 0).sum(axis=1), minlength=3).tolist(),
                       "mean_asked_return_relative_to_stop": float(goal.mean()),
                       "mean_router_squared_residual": float(np.mean((predict(obs, chair) - goal) ** 2))}
    return heads, trace


def deployed(menu, rates, heads):
    packet, channel = np.array([menu]), np.array([rates])

    @cache
    def ask(state, left):
        chair, _ = heads[left]
        role, good = ask_batch(packet, np.array([state]), channel, left, chair)
        return int(role[0]) if good[0] else None

    @cache
    def send(state, left, role, bit):
        _, delegate = heads[left]
        local = np.full((1, 3), -7)
        local[0, role] = bit
        return bool(reply_batch(packet, np.array([state]), channel, left, local, np.array([role]), delegate)[0])

    return ask, send


def measure(menu, initial_run, team):
    result = {}
    for rates in core.game.HELD:
        joint_ask, joint_send = deployed(menu, rates, team)
        for cap in (2, 3):
            input_rows = initial_run["held_results"][f"{rates}/{cap}"]
            scenarios = {}
            for label, send in (("backward_joint", joint_send), ("backward_always_send", lambda *_: True)):
                values = [core.evaluate_world(menu, rates, cap, joint_ask, send, world) for world in core.game.WORLDS]
                scenarios[label] = core.summarize(np.mean(values, axis=0))
                assert scenarios[label]["net"] <= input_rows["optional_exact"]["net"] + 1e-10
            result[f"{rates}/{cap}"] = scenarios | {"opening_desk": joint_ask(core.game.EMPTY, cap),
                "fixed_always_send": input_rows["fixed_always_send"], "optional_exact": input_rows["optional_exact"]}
    return result


def run():
    case, previous = HERE.parent / "case.json", HERE / "results.json"
    held = tuple(tuple(x) for x in core.game.read(case)["packages"].values())
    shape = core.game.shape(held)
    menus = np.array([m for m in combinations(core.game.WORLDS, 4) if core.game.shape(m) != shape])
    heads, trace = learn(menus)
    return {"seed": SEED, "rows_per_actor_per_horizon": ROWS, "training_menus": len(menus),
            "trace": trace, "held_results": measure(held, core.game.read(previous), heads),
            "heads": {left: [[x.tolist() for x in actor] for actor in pairs] for left, pairs in heads.items()},
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest()
                       for p in (case, previous, Path(__file__), HERE / "train.py", HERE / "backward-protocol.md")}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))
