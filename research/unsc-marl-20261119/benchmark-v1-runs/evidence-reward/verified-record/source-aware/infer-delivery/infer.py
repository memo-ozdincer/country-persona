"""Infer persistent delivery rates from dialogues with learned optional replies."""
from functools import cache
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import chooser as ch
import source_aware as fit

s, g = fit.score, fit.game
GRID = np.array(list(product((.23, .51, .78, .95), repeat=3)))
WORLDS = np.array(g.WORLDS)
SEED, REPEATS, STEPS = 951, 512, 24
CASES = (*ch.SHIFTS, ((.9, .9, .9), (.9, .9, .9)))
MODES = ("nominal", "prior_only", "naive", "reply_aware", "paid_pings")
MISS = -1


def prior(nominal):
    distances = np.sum(np.square((GRID - nominal) / .28), axis=1)
    mass = np.exp(-distances / 2)
    return mass / mass.sum()


def normalize(mass):
    total = mass.sum(axis=-1, keepdims=True)
    assert np.all(total > 0)
    return mass / total


def update_rule(weights, choice, state, cap, role, observed, teams, naive=False):
    # Kept unnormalized inside one workshop, where weights have a world axis.
    send = np.array([teams[choice][1](state, cap, role, bit) for bit in (0, 1)])
    if naive:
        send = np.ones(2, dtype=bool)
    sending_world = send[WORLDS[:, role]]
    rates = GRID[:, role, None]
    if observed == MISS:
        return weights * (1. - rates * sending_world)
    match = WORLDS[:, role] == observed
    return weights * (rates * sending_world * match)


def structures(teams, cap):
    @cache
    def likelihood(index, events, naive):
        choice = teams[index]
        state, left = g.EMPTY, cap
        weights = np.ones((len(GRID), len(WORLDS))) / len(WORLDS)
        for observation in events:
            role = choice[0](state, left)
            assert role is not None
            weights = update_rule(weights, index, state, left, role, observation, teams, naive)
            if observation >= 0:
                state = g.write_bit(state, role, observation)
            left -= 1
        assert not left or choice[0](state, left) is None
        result = weights.sum(axis=1)
        assert len(result) == len(GRID) and np.all((result >= 0) & (result <= 1 + 1e-12))
        return result

    def traces():
        def enumerate_team(index, state, left, history):
            role = teams[index][0](state, left) if left else None
            if role is None:
                yield history
                return
            yield from enumerate_team(index, state, left - 1, (*history, MISS))
            for bit in (0, 1):
                if teams[index][1](state, left, role, bit):
                    after = g.write_bit(state, role, bit)
                    yield from enumerate_team(index, after, left - 1, (*history, bit))
        checks = 0
        for index in range(len(teams)):
            events = list(enumerate_team(index, g.EMPTY, cap, ()))
            assert np.allclose(sum(likelihood(index, history, False) for history in events), 1.)
            checks += len(events)
        return checks

    return likelihood, traces


def play(teams, selected, menu, evaluate, physical, cap, world_id, draw):
    world = g.WORLDS[world_id]
    target = g.terminal(menu, world)[0]
    ask, send = teams[selected]
    state, attempted, history = g.EMPTY, 0, []
    for index in range(cap):
        left = cap - index
        role = ask(state, left)
        if role is None:
            break
        bit = world[role]
        want = send(state, left, role, bit)
        attempted += int(want)
        observed = bit if want and draw[index, role] < physical[role] else MISS
        history.append(observed)
        if observed >= 0:
            state = g.write_bit(state, role, bit)
    doc, correct, strict = evaluate(state, target)
    net = doc - fit.core.QUERY_COST * len(history) - fit.core.SEND_COST * attempted
    return np.array([net, doc * 70, correct, strict, len(history), attempted]), tuple(history)


def policy_setup(menu, evaluate, values, heads, nominal, cap):
    former = s.arms_for(menu, nominal)
    teams = (former["learned"], fit.deploy(menu, nominal, values, heads), former["silent"])
    lookup = np.array([[ch.measure(menu, evaluate, tuple(rates), cap, pair)["net"] for pair in teams]
                      for rates in GRID])
    static = np.array([ch.measure(menu, evaluate, nominal, cap, pair)["net"] for pair in teams])
    likelihood, checks = structures(teams, cap)
    return teams, lookup, static, likelihood, checks()


def choice(values):
    # Lowest contact when both values and silence are equally good.
    maximum = values.max()
    return 2 if values[2] >= maximum - 1e-12 else int(values.argmax())


def campaign(env, physical, nominal, cap, mode, worlds, deliveries, pings,
             menu, evaluate):
    teams, lookup, static, likelihood, _ = env
    base = prior(nominal)
    sums = np.zeros((STEPS, 6))
    estimates = np.zeros((STEPS, 3))
    choices = np.zeros((STEPS, 3), dtype=int)
    totals = []
    for run in range(REPEATS):
        mass = base.copy()
        spent = 0.
        if mode == "paid_pings":
            observed = pings[run] < physical
            mass = normalize(mass * np.prod(np.where(observed, GRID, 1 - GRID), axis=1))
            spent = 3 * (fit.core.QUERY_COST + fit.core.SEND_COST)
        total = -spent
        for time, world in enumerate(worlds[run]):
            expected = static if mode == "nominal" else mass @ lookup
            option = choice(expected)
            reward, history = play(teams, option, menu, evaluate, physical, cap, world, deliveries[run, time])
            assert history or not reward[4]
            if mode in ("naive", "reply_aware", "paid_pings") and history:
                mass = normalize(mass * likelihood(option, history, mode == "naive"))
            sums[time] += reward
            estimates[time] += mass @ GRID
            choices[time, option] += 1
            total += reward[0]
        sums[0, 0] -= spent
        totals.append(total)
    totals = np.array(totals)
    mean_scores = sums / REPEATS
    return {"mean_campaign_net": float(totals.mean()),
            "negative_campaign_fraction": float((totals < 0.).mean()),
            "campaign_net_standard_error": float(totals.std(ddof=1) / np.sqrt(REPEATS)),
            "last_eight_mean_net": float(mean_scores[-8:, 0].mean()),
            "means_by_workshop": mean_scores.tolist(), "posterior_delivery_mean": (estimates / REPEATS).tolist(),
            "team_choices": choices.tolist()}, totals


def audit_missing():
    hold = lambda _, __, ___, bit: bool(bit)
    always = lambda *_: True
    silence = lambda *_: False
    teams = [(None, hold), (None, always), (None, silence)]
    uniform = np.ones((len(GRID), len(WORLDS))) / len(WORLDS)
    miss = update_rule(uniform, 0, g.EMPTY, 2, 0, MISS, teams).sum(axis=1)
    forced = update_rule(uniform, 1, g.EMPTY, 2, 0, MISS, teams).sum(axis=1)
    silent = update_rule(uniform, 2, g.EMPTY, 2, 0, MISS, teams).sum(axis=1)
    assert np.allclose(miss, 1. - GRID[:, 0] / 2)
    assert np.allclose(forced, 1. - GRID[:, 0])
    assert np.allclose(silent, 1.)
    return {"rate_cells": len(GRID), "miss_likelihood": ["1 − rate/2", "1 − rate", "1"]}


def run():
    rng = np.random.default_rng(SEED)
    worlds = rng.integers(len(WORLDS), size=(REPEATS, STEPS))
    deliveries = rng.random((REPEATS, STEPS, 3, 3))
    pings = rng.random((REPEATS, 3))
    fit_results = s.e.read(HERE.parent / "results.json")
    heads = {int(h): tuple(tuple(np.array(x) for x in actor) for actor in pair)
             for h, pair in fit_results["heads"].items()}
    native = {row["arm"]: s.r.parse(row["reply"]) for row in s.review.rows("calls.jsonl")}
    result, checks = {}, 0
    for arm in s.r.ARMS:
        context = s.r.load(arm)
        menu = context[1]
        evaluate = s.documentary(arm, native[arm], context)
        values = tuple(fit_results["evaluation"][arm]["packet_values"])
        outcomes = {}
        setups = {}
        for (nominal, physical), cap in product(CASES, (2, 3)):
            key = nominal, cap
            if key not in setups:
                setups[key] = policy_setup(menu, evaluate, values, heads, nominal, cap)
                checks += setups[key][-1]
            environment = setups[key]
            strategies, samples = {}, {}
            for mode in MODES:
                strategies[mode], samples[mode] = campaign(environment, physical, nominal, cap, mode, worlds,
                                                           deliveries, pings, menu, evaluate)
            for mode in MODES:
                differences = samples[mode] - samples["nominal"]
                strategies[mode]["paired_gain_vs_nominal"] = float(differences.mean())
                strategies[mode]["paired_gain_standard_error"] = float(differences.std(ddof=1) / np.sqrt(REPEATS))
            hindsight = [ch.measure(menu, evaluate, physical, cap, pair)["net"] for pair in environment[0]]
            outcomes[f"{nominal}->{physical}/{cap}"] = {"strategies": strategies,
                "hindsight_per_workshop": max(hindsight), "candidate_true_net": hindsight}
        result[arm] = outcomes
    pins = (Path(__file__), HERE / "protocol.md", Path(fit.__file__), HERE.parent / "results.json",
            Path(ch.__file__), s.HERE / "scoring_replay.py", s.HERE / "evidence" / "complete.json")
    return {"seed": SEED, "campaigns_per_condition": REPEATS, "workshops_per_campaign": STEPS,
            "miss_audit": audit_missing(), "normalized_public_traces": checks, "results": result,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
