"""Estimate partner conventions from local or archived public receipts."""
from collections import defaultdict
from fractions import Fraction
from hashlib import sha256
from itertools import product
from pathlib import Path
from statistics import mean
from unittest.mock import patch
import json

import numpy as np
import torch

import render
import replay as r

HERE, s = Path(__file__).resolve().parent, r.s
PARTNERS = ("high", "low")
HORIZONS = (0, 4, 16, 32)
FORECASTS = ("old-fixed", "old-rank", "prior-planner", "posterior-planner", "known-partner")


def script(grid, high, with_peer):
    choices = []
    for card in grid.cards[0]:
        paid = with_peer and max(card) == 3
        want = max(card) if high or paid else min(card)
        eligible = (i for i, grade in enumerate(card) if grade == want)
        column = min(eligible, key=lambda j: grid.packages[j])
        choices.append((column, paid))
    return choices


def model(grid, family, data, profile):
    """Integrate outcome and historical observation masses for a fixed opener."""
    branch = defaultdict(lambda: np.zeros(3))
    observations = {"local": defaultdict(float), "public": defaultdict(float)}
    cached = {}
    fee = 0.
    for world, mass in data.prior.items():
        col, paid = profile[world[0]]
        first = grid.claim(world, 0, col)
        fee += mass*paid*s.base.FEE
        for peer, chance in s.base.observations(first, paid):
            state = ("B", world[1], peer)
            observations["local"][state] += mass*chance
            for got_first in (False, True):
                first_at_chair = first if got_first else None
                p_first = s.base.DELIVER if got_first else 1-s.base.DELIVER
                reach = mass*chance*p_first
                observations["public"][(state, first_at_chair)] += reach
                for c in range(3):
                    second = grid.claim(world, 1, c)
                    for got_second in (False, True):
                        view = (first_at_chair, second if got_second else None)
                        if view not in cached:
                            trusted = r.ledger(grid, view)
                            text = render.render(grid, family, trusted)
                            verified = render.verify(grid, family, trusted, text)
                            assert (verified["settled_points"] > 0) == bool(grid.information(view)[1])
                            cached[view] = verified["settled_points"]/70
                        p_second = s.base.DELIVER if got_second else 1-s.base.DELIVER
                        branch[state][c] += reach*p_second*cached[view]
    assert all(abs(sum(distribution.values())-1.) < 1e-10 for distribution in observations.values())
    return branch, observations, fee, len(cached)


def rationalize(models, channel):
    dist = []
    for _, d, _, _ in models:
        probs = {k: Fraction(p).limit_denominator(100_000) for k,p in d[channel].items()}
        assert sum(probs.values()) == 1 and all(abs(float(p)-d[channel][k]) < 1e-12 for k,p in probs.items())
        dist.append(probs)
    support = sorted(set(dist[0]) | set(dist[1]), key=str)
    equal = tuple((dist[0].get(v,Fraction()),dist[1].get(v,Fraction())) for v in support)
    groups = defaultdict(lambda: np.zeros(2))
    for p,q in equal:
        if p and q:
            groups[p/q] += np.array([float(p),float(q)])
    return groups, float(sum(abs(a-b) for a,b in equal)/2), len(support)


def histories(groups):
    """Combine ambiguous prefixes with exactly the same joint likelihood ratio."""
    states = {Fraction(1): np.ones(2)}
    for n in range(max(HORIZONS)+1):
        if n in HORIZONS:
            ratios = sorted(states)
            masses = np.stack([states[k] for k in ratios]) if ratios else np.empty((0,2))
            # The missing mass has encountered an observation exclusive to its true opener.
            parsed = np.clip(1-masses.sum(0), 0, 1)
            options = np.concatenate((masses, [[parsed[0],0.],[0.,parsed[1]]]), axis=0)
            assert np.allclose(options.sum(0), 1.)
            assert np.allclose(masses[:,0], masses[:,1]*np.asarray([float(x) for x in ratios]))
            probability = np.asarray([float(r/(r+1)) for r in ratios] + [1.,0.])
            yield n, probability, options
        if n < max(HORIZONS):
            updated = defaultdict(lambda: np.zeros(2))
            for left, mass in states.items():
                for right, point in groups.items():
                    updated[left*right] += mass*point
            states = updated


def replay(grid, family, data, old, channel_paid):
    models = [model(grid, family, data, script(grid,i == 0,channel_paid)) for i in range(2)]
    states = sorted(set(models[0][0]) | set(models[1][0]), key=str)
    all_values = np.asarray([[m[0].get(key,np.zeros(3)) for key in states] for m in models])
    fees = np.array([m[2] for m in models])

    def replay_choices(choices):
        return all_values[:, np.arange(len(states)), choices].sum(-1).T-fees

    fixed = {
        name: (all_values*np.array([old[name][0][data.states[k],:3] for k in states])).sum(axis=(1,2))-fees
        for name in FORECASTS[:2]
    }
    exact = all_values.max(-1).sum(-1)-fees

    # Independently check the frozen and exact policies in the original evaluator.
    for i, m in enumerate(models):
        choices = script(grid,i == 0,channel_paid)
        opener = old["old-fixed"][0].copy()
        for private,(col,paid) in enumerate(choices):
            index = data.states["A",private]
            opener[index] = 0.
            opener[index,s.base.ACTIONS.index((col,paid))] = 1.
        for name in FORECASTS[:2]:
            policy = old[name][0].copy()
            for private in range(len(grid.cards[0])):
                idx = data.states["A",private]
                policy[idx] = opener[idx]
            compare = s.measure(data,policy,s.base.FEE)["net"]
            assert abs(compare-fixed[name][i]) < 1e-9
        for key, ranks in m[0].items():
            index = data.states[key]
            opener[index] = 0.
            opener[index,int(ranks.argmax())] = 1.
        outer = s.measure(data,opener,s.base.FEE)
        assert abs(outer["net"]-exact[i]) < 1e-9

    out = {}
    for channel in ("local","public"):
        observations,tv,count = rationalize(models,channel)
        section = {}
        for n, p, mass in histories(observations):
            estimate = p[:, None, None]*all_values[0] + (1-p)[:, None, None]*all_values[1]
            posterior = replay_choices(estimate.argmax(-1))
            anytime = replay_choices(all_values.mean(0).argmax(-1))
            modes = dict(fixed, **{"prior-planner":anytime,"posterior-planner":posterior,"known-partner":exact})
            values = {}
            for name, candidates in modes.items():
                net = (mass*candidates).sum(axis=0)
                result = {partner: {"settled_points":float((net[i]+fees[i])*70),"net":float(net[i])}
                          for i,partner in enumerate(PARTNERS)}
                result["mean_net"] = float(net.mean())
                assert np.all(net <= exact+1e-9)
                values[name] = result
            assert all(values["posterior-planner"]["mean_net"]+1e-9 >= values[arm]["mean_net"]
                       for arm in FORECASTS[:-2])
            section[n] = dict(accuracy=float(mass.max(1).sum()/2), policies=values)
        if channel == "local":
            assert tv == 0
            assert all(abs(row["accuracy"]-.5) < 1e-10 for row in section.values())
        out[channel] = dict(histories=section, total_variation=tv, observation_support=count)
    return dict(channels=out, verified_receipts=[m[3] for m in models], fees=fees.tolist())


def run():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    draws = {r["draw"]:r for r in registry["accepted"]}
    origin = torch.tensor(s.read(s.FIT)["weights"],dtype=torch.float64)
    opener_w = np.asarray(s.read(HERE.parent/"joint-opener.json")["weights"])
    rank_w = np.asarray(s.read(HERE.parent/"ranking.json")["coef"])
    value_w = np.asarray(s.read(HERE.parent/"recipient.json")["weights"])

    def make(draw):
        with patch.dict(s.shared.FIXTURES,{"crossplay":s.original.fixture(draws[draw])}):
            return s.shared.Grid("crossplay")

    case_grids = {f"space-{i}":("space",make(i)) for i in registry["partition"]["reserved"]}
    case_grids.update({k:(k,s.shared.Grid(k)) for k in ("mali","myanmar")})
    results = {}
    for key,(family,grid) in case_grids.items():
        d = s.original.data_for(grid)
        start = d.probabilities(origin).numpy()
        run = r.opener.choose(d,start,r.opener.basis(d,d.prior,start),opener_w,s.base.FEE,"joint-fitted")
        scored = r.ranking.measure(d,run,r.recipient.aggregate(d,run),rank_w,value_w)
        old = {"old-fixed":scored["fixed"],"old-rank":scored["rank-fit"]}
        results[key] = {label:replay(grid,family,d,old,paid) for label,paid in (("silent",False),("shared-peer",True))}
    macro={}
    for condition, channel in product(("silent","shared-peer"),("local","public")):
        macro[f"{condition}/{channel}"] = {
            n: {arm:mean(row[condition]["channels"][channel]["histories"][n]["policies"][arm]["mean_net"]
                        for row in results.values()) for arm in FORECASTS} for n in HORIZONS
        }
    paths=(Path(__file__),HERE/"crossplay-protocol.md",HERE/"render.py",s.original.REGISTRY,HERE.parent/"ranking.json")
    return dict(cases=results,macro=macro,hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in paths})


if __name__=="__main__":
    print(json.dumps(run(),indent=2,ensure_ascii=False))
