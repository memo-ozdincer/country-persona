"""Learn question and reply choices with public documentary values."""
from functools import cache
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import scoring_replay as score

old, core, game = score.r.w.fitted, score.core, score.g
PARTIAL = (.22, .48, .72, .92)
BONUS = (0., .11, .23)


def value(menu, state, floor):
    _, known, base = core.credit(menu, state)
    return np.where(known == 0, floor[:, 1], np.where(base > 0, floor[:, 0], 0.))


def features(menu, state, rates, left, floor, truth=None):
    base = core.features(menu, state, rates, np.full(len(state), left), truth)
    present = value(menu, state, floor)
    base[:, :, 2] = present[:, None]
    if truth is not None:
        fully_known_after = (state < 0).sum(axis=1) == 1
        outcome = np.where(fully_known_after[:, None], floor[:, 1, None],
                           np.where(base[:, :, -2] == 0, floor[:, 0, None], 0.))
        base[:, :, -1] = outcome - present[:, None]
    metadata = np.repeat(floor[:, None, :], 3, axis=1)
    return np.concatenate((base, metadata), axis=2)


def ask_batch(menu, state, rates, left, floor, chair):
    scores = np.where(state < 0, old.predict(features(menu, state, rates, left, floor), chair), -np.inf)
    chosen = scores.argmax(axis=1)
    return chosen, scores[np.arange(len(state)), chosen] > 0.


def send_batch(menu, state, rates, left, floor, truth, roles, reply):
    inputs = features(menu, state, rates, left, floor, truth)[np.arange(len(state)), roles]
    return old.predict(inputs, reply) > 0.


def continue_team(menu, state, rates, truth, floor, left, heads, draws):
    spent = np.zeros(len(state))
    active = np.ones(len(state), dtype=bool)
    for h in range(left, 0, -1):
        chair, reply = heads[h]
        roles, ask = ask_batch(menu, state, rates, h, floor, chair)
        active &= ask
        send = active & send_batch(menu, state, rates, h, floor, truth, roles, reply)
        delivered = send & (draws[h - 1] < rates[np.arange(len(state)), roles])
        state = old.proceed(state, truth, roles, delivered)
        spent += core.QUERY_COST * active + core.SEND_COST * send
    return value(menu, state, floor) - spent


def draw(menus, rng, left):
    event = old.context(menus, rng, left)
    partial = rng.choice(PARTIAL, size=old.ROWS)
    full = np.minimum(1., partial + rng.choice(BONUS, size=old.ROWS))
    return *event, np.column_stack((partial, full))


def train(menus):
    rng = np.random.default_rng(old.SEED)
    heads, trace = {}, {}
    rows = np.arange(old.ROWS)
    for h in (1, 2, 3):
        menu, state, rates, truth, roles, draws, delivered, floor = draw(menus, rng, h)
        received = old.proceed(state, truth, roles, delivered)
        hit = continue_team(menu, received, rates, truth, floor, h - 1, heads, draws)
        skip = continue_team(menu, state, rates, truth, floor, h - 1, heads, draws)
        local = features(menu, state, rates, h, floor, truth)[rows, roles]
        reply_target = hit - skip - core.SEND_COST
        reply = old.fit(local, reply_target, rng)

        menu, state, rates, truth, roles, draws, delivered, floor = draw(menus, rng, h)
        send = send_batch(menu, state, rates, h, floor, truth, roles, reply)
        received = old.proceed(state, truth, roles, send & delivered)
        future = continue_team(menu, received, rates, truth, floor, h - 1, heads, draws)
        target = future - value(menu, state, floor) - core.QUERY_COST - core.SEND_COST * send
        observe = features(menu, state, rates, h, floor)[rows, roles]
        chair = old.fit(observe, target, rng)
        heads[h] = chair, reply
        trace[h] = {"reply_mean_target": float(np.mean(reply_target)), "chair_mean_target": float(np.mean(target)),
                    "chair_train_mse": float(np.mean((old.predict(observe, chair) - target) ** 2))}
    return heads, trace


def deploy(menu, rates, packet_values, heads):
    menus, channels, available = np.array([menu]), np.array([rates]), np.array([packet_values])

    @cache
    def ask(state, left):
        selected, good = ask_batch(menus, np.array([state]), channels, left, available, heads[left][0])
        return int(selected[0]) if good[0] else None

    @cache
    def send(state, left, role, bit):
        private = np.full((1, 3), -7, dtype=int)
        private[0, role] = bit
        return bool(send_batch(menus, np.array([state]), channels, left, available, private, np.array([role]), heads[left][1])[0])

    return ask, send


def exact(menu, rates, cap, packet_values):
    # The observed event "nothing arrived" has a public posterior depending on the
    # known policy. It never supplies a requirement to the proof.
    @cache
    def best(state, left, mass):
        total = sum(mass)
        if not total:
            return 0.
        decision, _ = game.terminal(menu, state)
        stop = 0. if decision == "UNRESOLVED" else packet_values[int(-1 not in state)]
        answer = total * stop
        if not left:
            return answer
        for role, known in enumerate(state):
            if known >= 0:
                continue
            for gate in ((True, True), (False, True), (True, False)):
                hits = [[0.] * len(mass), [0.] * len(mass)]
                lost = []
                cost = core.QUERY_COST * total
                for i, (w, role_mass) in enumerate(zip(game.WORLDS, mass, strict=True)):
                    bit = w[role]
                    attempted = role_mass if gate[bit] else 0.
                    receipt = attempted * rates[role]
                    hits[bit][i] = receipt
                    lost.append(role_mass - receipt)
                    cost += core.SEND_COST * attempted
                candidate = best(state, left - 1, tuple(lost)) - cost
                for bit, weights in enumerate(hits):
                    candidate += best(game.write_bit(state, role, bit), left - 1, tuple(weights))
                answer = max(answer, candidate)
        return answer

    return best(game.EMPTY, cap, (.125,) * 8)


def benchmark_values(evaluate, menu):
    partial = None
    for pair in game.WORLDS:
        for role in range(3):
            state = pair[:role] + (-1,) + pair[role + 1:]
            if game.terminal(menu, state)[0] == "IMPASSE":
                partial = state
                break
        if partial is not None:
            break
    assert partial is not None
    full = game.WORLDS[0]
    target = game.terminal(menu, full)[0]
    return evaluate(partial, "IMPASSE")[0], evaluate(full, target)[0]


def compare(heads):
    native = {x["arm"]: score.r.parse(x["reply"]) for x in score.review.rows("calls.jsonl")}
    reports = {}
    for arm in score.r.ARMS:
        context = score.r.load(arm)
        menu = context[1]
        evaluate = score.documentary(arm, native[arm], context)
        values = benchmark_values(evaluate, menu)
        assert not any(np.allclose(values,(p, min(1., p + b))) for p in PARTIAL for b in BONUS)
        profiles = {}
        for rates in game.HELD:
            previous = score.arms_for(menu, rates)
            former_ask, former_send = previous["learned"]
            improved_ask, improved_send = deploy(menu, rates, values, heads)
            controls = previous | {"aware": (improved_ask, improved_send),
                "chair_swap": (improved_ask, former_send), "reply_swap": (former_ask, improved_send),
                "aware_always_reply": (improved_ask, previous["always_reply"][1])}
            for cap in (2, 3):
                row = {}
                for label, (ask, send) in controls.items():
                    matrix = [score.expected(menu, evaluate, rates, world, cap, ask, send) for world in game.WORLDS]
                    points, correct, strict, questions, attempts = map(float, np.mean(matrix, axis=0))
                    row[label] = {"net": points - core.QUERY_COST * questions - core.SEND_COST * attempts,
                                  "points": points * 70, "accuracy": correct, "questions": questions,
                                  "attempts": attempts, "opening_desk": ask(game.EMPTY, cap)}
                bound = exact(menu, rates, cap, values)
                assert all(s["net"] <= bound + 1e-10 for s in row.values())
                profiles[str(rates) + f"/{cap}"] = {"arms": row, "exact_net": bound}
        reports[arm] = {"packet_values": values, "conditions": profiles}
    return reports


def run():
    held_menu = score.r.load("mali")[1]
    shape = game.shape(held_menu)
    menus = np.array([m for m in combinations(game.WORLDS, 4) if game.shape(m) != shape])
    heads, trace = train(menus)
    pins = (Path(__file__), HERE / "protocol.md", score.HERE / "scoring_replay.py", score.HERE / "scoring-replay.json",
            score.HERE / "evidence" / "complete.json", Path(old.__file__), Path(core.__file__))
    return {"menus": len(menus), "seed": old.SEED, "rows_per_head": old.ROWS, "trace": trace,
            "heads": {h: [[row.tolist() for row in actor] for actor in pair] for h, pair in heads.items()},
            "evaluation": compare(heads), "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
