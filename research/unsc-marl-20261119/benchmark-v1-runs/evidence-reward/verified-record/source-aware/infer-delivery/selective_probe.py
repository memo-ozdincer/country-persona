"""Buy information selectively and keep inference separate from caution."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import infer as task

HERE = Path(__file__).resolve().parent
CUTOFF = .80
FEE = task.fit.core.QUERY_COST + task.fit.core.SEND_COST


def settle(mass, values):
    net = mass @ values
    safe = mass @ (values > 0.) >= CUTOFF
    allowed = np.where(safe, net, 0.)
    allowed[2] = 0.
    selected = task.choice(allowed)
    return selected, allowed[selected]


def test_probe(mass, values, available, remaining):
    baseline = settle(mass, values)[1]
    best = 0.
    selected = None
    for desk in sorted(available):
        arrive = task.GRID[:, desk]
        success = mass @ arrive
        after_success = task.normalize(mass * arrive)
        after_miss = task.normalize(mass * (1. - arrive))
        expected = success * settle(after_success, values)[1] + (1. - success) * settle(after_miss, values)[1]
        gain = remaining * (expected - baseline) - FEE
        if gain > best + 1e-12:
            best, selected = gain, desk
    return selected


def replay(environment, physical, nominal, cap, worlds, draws, probes, menu, evaluate, buy):
    teams, lookup, _, likelihood, _ = environment
    counts = Counter()
    prior = task.prior(nominal)
    outcomes = []
    for i, workshop_worlds in enumerate(worlds):
        spent, total, tried, decisions = 0., 0., 0, 0
        available = set(range(3))
        mass = prior.copy()
        for time, world in enumerate(workshop_worlds):
            if buy and available:
                desk = test_probe(mass, lookup, available, len(workshop_worlds) - time)
                if desk is not None:
                    available.remove(desk)
                    landed = probes[i, desk] < physical[desk]
                    probability = task.GRID[:, desk]
                    mass = task.normalize(mass * (probability if landed else 1. - probability))
                    spent += FEE
                    tried += 1
                    counts[f"probe_role_{desk}"] += 1
            selected, _ = settle(mass, lookup)
            reward, history = task.play(teams, selected, menu, evaluate, physical, cap, world, draws[i, time])
            decisions += int(reward[2])
            total += reward[0]
            counts[f"team_{selected}"] += 1
            if history:
                mass = task.normalize(mass * likelihood(selected, history, False))
        outcomes.append((total - spent, decisions, tried))
    return np.array(outcomes), counts


def summarize(rows, counts, base):
    gains = rows[:, 0] - base
    return {"mean_campaign_net": float(rows[:, 0].mean()),
            "improvement_vs_reply_aware": float(gains.mean()),
            "paired_standard_error": float(gains.std(ddof=1) / np.sqrt(len(rows))),
            "decisions_per_campaign": float(rows[:, 1].mean()),
            "probes_per_campaign": float(rows[:, 2].mean()),
            "negative_campaign_fraction": float(np.mean(rows[:, 0] < 0.)),
            "action_counts": counts}


def run():
    rng = np.random.default_rng(task.SEED)
    worlds = rng.integers(len(task.WORLDS), size=(task.REPEATS, task.STEPS))
    draws = rng.random((task.REPEATS, task.STEPS, 3, 3))
    probes = rng.random((task.REPEATS, 3))
    e, s = task.s.e, task.s
    fit = e.read(HERE.parent / "results.json")
    earlier = e.read(HERE / "results.json")
    heads = {int(h): tuple(tuple(np.array(x) for x in a) for a in pair) for h, pair in fit["heads"].items()}
    native = {row["arm"]: s.r.parse(row["reply"]) for row in s.review.rows("calls.jsonl")}
    out = {}
    for arm in s.r.ARMS:
        context = s.r.load(arm)
        menu = context[1]
        evaluate = s.documentary(arm, native[arm], context)
        values = tuple(fit["evaluation"][arm]["packet_values"])
        cache = {}
        rows = {}
        for (nominal, physical), cap in product(task.CASES, (2, 3)):
            key = nominal, cap
            if key not in cache:
                cache[key] = task.policy_setup(menu, evaluate, values, heads, nominal, cap)
            env = cache[key]
            condition = f"{nominal}->{physical}/{cap}"
            base, baseline = task.campaign(env, physical, nominal, cap, "reply_aware", worlds, draws,
                                           probes, menu, evaluate)
            assert base["mean_campaign_net"] == earlier["results"][arm][condition]["strategies"]["reply_aware"]["mean_campaign_net"]
            row = {"reply_aware_net": base["mean_campaign_net"]}
            for label, buy in (("cautious", False), ("selective_probe", True)):
                results, counts = replay(env, physical, nominal, cap, worlds, draws, probes, menu, evaluate, buy)
                row[label] = summarize(results, counts, baseline)
            rows[condition] = row
        out[arm] = rows
    pins = (Path(__file__), HERE / "selective-probe-protocol.md", HERE / "infer.py", HERE / "results.json",
            HERE.parent / "results.json")
    return {"positive_net_probability": CUTOFF, "probe_cost": FEE, "results": out,
            "sha256": {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
