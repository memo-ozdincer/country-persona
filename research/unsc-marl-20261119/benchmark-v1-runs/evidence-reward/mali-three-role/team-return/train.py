"""Joint policy gradients for asking and signing, from sampled documentary reward."""
from functools import cache
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import experiment as game

QUERY_COST = game.FEE
SEND_COST = .03
SEED = 83
UPDATES = 600
BATCH = 512
TRAIN_RATES = (.30, .55, .75, .95)
WIDTH = 24


def credit(menu, states):
    fits = ((states[:, None, :] < 0) | (menu == states[:, None, :])).all(axis=2)
    missing = (states < 0).sum(axis=1)
    points = np.where(missing == 0, 1., np.where(fits.any(axis=1), 0., .8))
    return fits, missing, points


def features(menu, state, delivery, turns, truth=None):
    fits, missing, points = credit(menu, state)
    active = state < 0
    numbers = fits.sum(axis=1)
    cols = []
    for role in range(3):
        other = [i for i in range(3) if i != role]
        rate = delivery[:, role]
        spare = np.sort(delivery[:, other] * active[:, other], axis=1)
        group = fits & (menu[:, :, role] == 1)
        high = group.sum(axis=1)
        low = numbers - high
        parts = np.sort(np.stack((low, high), axis=1), axis=1)
        inspect_pair = []
        for peer in other:
            cells = np.stack([
                (fits & (menu[:, :, role] == left) & (menu[:, :, peer] == right)).sum(axis=1)
                for left, right in ((0, 0), (0, 1), (1, 0), (1, 1))
            ], axis=1)
            inspect_pair.append((cells == 0).mean(axis=1) * delivery[:, peer] * active[:, peer])
        pair = np.sort(np.stack(inspect_pair, axis=1), axis=1)
        data = [turns / 3, missing / 3, points, numbers / 4, rate,
                spare[:, 0], spare[:, 1], parts[:, 0] / 4, parts[:, 1] / 4, pair[:, 0], pair[:, 1]]
        if truth is not None:
            filtered = np.where(truth[:, role] == 1, high, low)
            fully_known = missing == 1
            disclosed_credit = np.where(fully_known, 1., np.where(filtered == 0, .8, 0.))
            data.extend((filtered / 4, disclosed_credit - points))
        cols.append(np.stack(data, axis=1))
    return np.stack(cols, axis=1)


class Actor:
    def __init__(self, rng, inputs, params=None):
        self.params = params if params is not None else [
            rng.normal(0, .35, (inputs, WIDTH)), np.zeros(WIDTH),
            rng.normal(0, .03, WIDTH), np.zeros(1),
        ]
        self.first = [np.zeros_like(x) for x in self.params]
        self.second = [np.zeros_like(x) for x in self.params]

    def forward(self, observation):
        matrix, offset, head, bias = self.params
        hidden = np.tanh(observation @ matrix + offset)
        return hidden @ head + bias, hidden

    def step(self, samples, iteration):
        matrix, _, head, _ = self.params
        gradients = [np.zeros_like(x) for x in self.params]
        for observation, hidden, dlogit in samples:
            x = observation.reshape(-1, observation.shape[-1])
            h = hidden.reshape(-1, hidden.shape[-1])
            d = dlogit.reshape(-1)
            dh = (d[:, None] * head) * (1 - h * h)
            for total, delta in zip(gradients, (x.T @ dh, dh.sum(axis=0), d @ h, d.sum()), strict=True):
                total += delta / BATCH
        for parameter, first, second, gradient in zip(self.params, self.first, self.second, gradients, strict=True):
            first *= .9
            first += .1 * gradient
            second *= .999
            second += .001 * gradient ** 2
            parameter += .006 * (first / (1 - .9 ** iteration)) / (np.sqrt(second / (1 - .999 ** iteration)) + 1e-8)

    def export(self):
        return [parameter.tolist() for parameter in self.params]


def softmax(logits, valid):
    logits = np.where(valid, logits, -np.inf)
    exponent = np.exp(logits - logits.max(axis=1, keepdims=True))
    return exponent / exponent.sum(axis=1, keepdims=True)


def advantage(rewards, groups):
    counts = np.bincount(groups)
    sums = np.bincount(groups, weights=rewards)
    baseline = (sums[groups] - rewards) / np.maximum(counts[groups] - 1, 1)
    return rewards - baseline


def train(menus):
    rng = np.random.default_rng(SEED)
    chair, reply = Actor(rng, 11), Actor(rng, 13)
    initial = [chair.export(), reply.export()]
    curve = []
    for update in range(1, UPDATES + 1):
        menu = menus[rng.integers(len(menus), size=BATCH)]
        truth = rng.integers(2, size=(BATCH, 3))
        rates = rng.choice(TRAIN_RATES, size=(BATCH, 3))
        turns = rng.integers(2, 4, size=BATCH)
        state = np.full_like(truth, -1)
        live = np.ones(BATCH, dtype=bool)
        spent = np.zeros(BATCH)
        queries = np.zeros(BATCH)
        sends = np.zeros(BATCH)
        chair_trace, reply_trace = [], []
        temperature = 1. - .35 * update / UPDATES
        for _ in range(3):
            rows = np.flatnonzero(live & (turns > 0))
            if not rows.size:
                break
            obs = features(menu[rows], state[rows], rates[rows], turns[rows])
            logits, hidden = chair.forward(obs)
            scores = np.column_stack((logits, np.zeros(rows.size))) / temperature
            valid = np.column_stack((state[rows] < 0, np.ones(rows.size, dtype=bool)))
            probabilities = softmax(scores, valid)
            chosen = (rng.random(rows.size)[:, None] > np.cumsum(probabilities, axis=1)[:, :3]).sum(axis=1)
            group = turns[rows] * 8 + (state[rows] < 0).sum(axis=1) * 2 + (obs[:, 0, 2] > 0)
            chair_trace.append((rows, obs, hidden, np.eye(4)[chosen, :3] - probabilities[:, :3], group, spent[rows].copy()))
            live[rows[chosen == 3]] = False
            asked = chosen < 3
            rows, roles = rows[asked], chosen[asked]
            if not rows.size:
                continue
            spent[rows] += QUERY_COST
            queries[rows] += 1
            local = features(menu[rows], state[rows], rates[rows], turns[rows], truth[rows])
            local = local[np.arange(rows.size), roles]
            logits, hidden = reply.forward(local)
            probability = 1 / (1 + np.exp(-logits / temperature))
            send = rng.random(rows.size) < probability
            reply_trace.append((rows, local, hidden, send - probability, group[asked], spent[rows].copy()))
            spent[rows[send]] += SEND_COST
            sends[rows[send]] += 1
            delivered = send & (rng.random(rows.size) < rates[rows, roles])
            state[rows[delivered], roles[delivered]] = truth[rows[delivered], roles[delivered]]
            turns[rows] -= 1
        reward = credit(menu, state)[2] - spent

        def updates(trace):
            for rows, obs, hidden, gradient, group, previous_cost in trace:
                signal = advantage(reward[rows] + previous_cost, group) / temperature
                yield obs, hidden, gradient * signal.reshape((-1,) + (1,) * (gradient.ndim - 1))

        chair.step(updates(chair_trace), update)
        reply.step(updates(reply_trace), update)
        if update in (1, 100, 200, 300, 400, 500, UPDATES):
            curve.append({"update": update, "batch_mean_net": float(reward.mean()),
                          "batch_queries": float(queries.mean()), "batch_sends": float(sends.mean())})
    return initial, [chair.export(), reply.export()], curve


def loads(weights):
    return [Actor(None, None, [np.array(x) for x in actor]) for actor in weights]


def decisions(menu, rates, weights):
    chair, desk = loads(weights)
    menus = np.array([menu])
    delivery = np.array([rates])

    @cache
    def ask(state, turns):
        logits, _ = chair.forward(features(menus, np.array([state]), delivery, np.array([turns])))
        candidates = [(logits[0, i], i) for i in range(3) if state[i] < 0]
        value, action = max(candidates + [(0., None)], key=lambda x: x[0])
        return action if value > 0 else None

    @cache
    def send(state, turns, role, bit):
        own = np.full((1, 3), -7, dtype=int)
        own[0, role] = bit
        obs = features(menus, np.array([state]), delivery, np.array([turns]), own)
        logits, _ = desk.forward(obs[:, role, :])
        return bool(logits[0] > 0)

    return ask, send


def metrics(menu, state, truth):
    answer, points = game.terminal(menu, state)
    target = game.terminal(menu, truth)[0]
    assert answer in (target, "UNRESOLVED")
    correct = answer == target
    return np.array([points, correct and target != "IMPASSE", correct and target == "IMPASSE", 0., 0.])


def evaluate_world(menu, rates, cap, ask, send, truth):
    @cache
    def rollout(state, left):
        role = ask(state, left) if left else None
        if role is None:
            return metrics(menu, state, truth)
        bit = truth[role]
        skip = rollout(state, left - 1)
        if send(state, left, role, bit):
            hit = rollout(game.write_bit(state, role, bit), left - 1)
            return rates[role] * hit + (1. - rates[role]) * skip + np.array([0., 0., 0., 1., 1.])
        return skip + np.array([0., 0., 0., 1., 0.])

    return rollout(game.EMPTY, cap)


def summarize(result):
    credit, agreement_correct, impasse_correct, asks, sends = map(float, result)
    return {"net": credit - QUERY_COST * asks - SEND_COST * sends, "credit": credit,
            "accuracy": agreement_correct + impasse_correct, "agreement_recall": 2 * agreement_correct,
            "impasse_recall": 2 * impasse_correct, "questions": asks, "attempts": sends}


def exact(menu, rates, cap, optional):
    per_probe = np.array([0., 0., 0., 1., 0.])
    per_send = np.array([0., 0., 0., 0., 1.])
    choices = ((True, True), (True, False), (False, True)) if optional else ((True, True),)

    def utility(values):
        return values[0] - QUERY_COST * values[3] - SEND_COST * values[4]

    @cache
    def solve(state, left, weights):
        mass = sum(weights)
        if not mass:
            return np.zeros(5)
        best = sum(w * metrics(menu, state, world) for w, world in zip(weights, game.WORLDS, strict=True) if w)
        if not left:
            return best
        for role, known in enumerate(state):
            if known >= 0:
                continue
            for gates in choices:
                lost = []
                delivered = [[0.] * len(weights), [0.] * len(weights)]
                attempts = 0.
                for i, (world, w) in enumerate(zip(game.WORLDS, weights, strict=True)):
                    bit = world[role]
                    attempted = w if gates[bit] else 0.
                    success = rates[role] * attempted
                    lost.append(w - success)
                    delivered[bit][i] = success
                    attempts += attempted
                value = solve(state, left - 1, tuple(lost)) + mass * per_probe + attempts * per_send
                for bit in (0, 1):
                    value += solve(game.write_bit(state, role, bit), left - 1, tuple(delivered[bit]))
                if utility(value) > utility(best) + 1e-10:
                    best = value
        return best

    return summarize(solve(game.EMPTY, cap, (.125,) * 8))


def evaluate(menu, baseline, fitted):
    output = {}
    for rates in game.HELD:
        old_ask, old_send = decisions(menu, rates, baseline)
        new_ask, new_send = decisions(menu, rates, fitted)

        def always(*args):
            return True

        def fixed(state, _):
            return next((i for i, bit in enumerate(state) if bit < 0), None)

        actors = {
            "initial": (old_ask, old_send), "chair_only": (new_ask, old_send),
            "reply_only": (old_ask, new_send), "joint": (new_ask, new_send),
            "fitted_chair_always_send": (new_ask, always), "fixed_always_send": (fixed, always),
        }
        for cap in (2, 3):
            arms = {}
            for name, (ask, send) in actors.items():
                results = [evaluate_world(menu, rates, cap, ask, send, truth) for truth in game.WORLDS]
                arms[name] = summarize(np.mean(results, axis=0)) | {"opening_desk": ask(game.EMPTY, cap)}
            arms["compulsory_exact"] = exact(menu, rates, cap, False)
            arms["optional_exact"] = exact(menu, rates, cap, True)
            assert all(arms["optional_exact"]["net"] + 1e-10 >= row["net"] for row in arms.values())
            output[f"{rates}/{cap}"] = arms
    return output


def run():
    case = HERE.parent / "case.json"
    held = tuple(tuple(row) for row in game.read(case)["packages"].values())
    held_shape = game.shape(held)
    menus = np.array([m for m in combinations(game.WORLDS, 4) if game.shape(m) != held_shape])
    initial, trained, curve = train(menus)
    sources = (Path(__file__), case, HERE.parent / "experiment.py", HERE / "protocol.md")
    return {"seed": SEED, "updates": UPDATES, "batch": BATCH, "training_menus": len(menus),
            "training_rates": TRAIN_RATES, "send_cost": SEND_COST, "query_cost": QUERY_COST,
            "training_curve": curve, "initial": initial, "trained": trained,
            "held_results": evaluate(held, initial, trained),
            "sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in sources}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))
