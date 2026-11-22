"""Fit recipient action values from ordinary verified historical receipts."""
from collections import defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from statistics import mean
from unittest.mock import patch

import numpy as np
import torch

import crossplay as c
import render

HERE, s = Path(__file__).resolve().parent, c.s
HORIZONS = (0,4,16,32,128)
HISTORIES = 1024
SEED = 78119


def received(col, grid):
    return min(col, key=lambda x: grid.packages[x])


def alternative(grid, variant, shared):
    result = []
    for row in grid.cards[0]:
        paid = shared and max(row) == 3
        if paid and variant != "broadcast-median":
            col = received((i for i, g in enumerate(row) if g == max(row)), grid)
        elif variant in ("median", "broadcast-median"):
            col = sorted(range(3), key=lambda i:(row[i], grid.packages[i]))[1]
        elif variant == "veto-conditioned":
            grade = min(row) if 0 in row else max(row)
            col = received((i for i,g in enumerate(row) if g == grade),grid)
        elif variant == "public-priority":
            col = received((i for i,g in enumerate(grid.public) if g == max(grid.public)), grid)
        else:
            raise ValueError(variant)
        result.append((col, paid or variant == "broadcast-median"))
    return result


def mixed(first, second, fraction=.5):
    branches = {k: (fraction*first[0].get(k,np.zeros(3))+(1-fraction)*second[0].get(k,np.zeros(3)))
                for k in set(first[0])|set(second[0])}
    observations = {mode:{k:(fraction*first[1][mode].get(k,0.)+(1-fraction)*second[1][mode].get(k,0.))
                          for k in set(first[1][mode])|set(second[1][mode])} for mode in ("local","public")}
    return branches, observations, fraction*first[2]+(1-fraction)*second[2], first[3]+second[3]


def verified_credit(grid, family, state, first):
    _, local, _ = state
    own_card = grid.cards[1][local]
    values = []
    for col, grade in enumerate(own_card):
        expected = 0.
        for got in (True,False):
            view = (first,(col,grade) if got else None)
            allowed = c.r.ledger(grid,view)
            text = render.render(grid,family,allowed)
            checked = render.verify(grid,family,allowed,text)
            expected += (s.base.DELIVER if got else 1-s.base.DELIVER)*checked["settled_points"]/70
        values.append(expected)
    return values


def posterior(counts, likelihood):
    # Count unsupported symbols explicitly so a zero count times log(0) cannot enter the calculation.
    exists = likelihood > 0
    log_likelihood = np.zeros_like(likelihood)
    np.log(likelihood, out=log_likelihood, where=exists)
    log = counts @ log_likelihood.T
    compatible = (counts @ (~exists).astype(int).T) == 0
    rejected = ~compatible.any(axis=1)
    result = np.full((len(counts),len(likelihood)),1/len(likelihood))
    log[~compatible] = -np.inf
    active = ~rejected
    weights = np.exp(log[active]-log[active].max(-1,keepdims=True))
    result[active] = weights/weights.sum(-1,keepdims=True)
    return result, rejected


def calc(grid, family, data, fixed, library, actual, neutral, rng, extension=None):
    symbols = sorted(set(actual[1]["public"])|set(library[0][1]["public"])|set(library[1][1]["public"]),key=str)
    states = sorted({a for a,_ in symbols}, key=str)
    key_index = {key:i for i,key in enumerate(states)}
    initial = np.asarray([[m[0].get(key,np.zeros(3)) for key in states] for m in library])
    recorded = np.asarray([[m[1]["public"].get(key,0.) for key in symbols] for m in library])
    true_obs = np.asarray([actual[1]["public"].get(key,0.) for key in symbols])
    true_values = np.asarray([actual[0].get(key,np.zeros(3)) for key in states])
    fees = actual[2]
    assert np.isclose(true_obs.sum(),1.) and np.allclose(recorded.sum(1),1.)
    certificate = np.zeros((len(symbols),len(states),3))
    for ix,(state,first) in enumerate(symbols):
        certificate[ix,key_index[state]] = verified_credit(grid,family,state,first)
    for model_probs, model_values in ((true_obs,true_values), *zip(recorded,initial,strict=True)):
        assert np.allclose(np.einsum("k,ksa->sa", model_probs, certificate), model_values)
    base_guess = initial.mean(0)
    informed = ((recorded[0]+recorded[1])*0.5) @ np.eye(len(states))[[key_index[key] for key,_ in symbols]]
    prior = np.stack([neutral[k]["raw"] for k in states])
    np.divide(base_guess, informed[:,None], out=prior, where=informed[:,None] > 1e-12)
    neutral_choice = np.argmax(np.stack([neutral[k]["raw"] for k in states]),axis=1)

    def library_choice(weights):
        v = np.einsum("hk,ksa->hsa",weights,initial)
        signal_mass = np.einsum(
            "hk,ks->hs",weights,
            recorded @ np.eye(len(states))[[key_index[key] for key,_ in symbols]]
        )
        return np.where(signal_mass>1e-12,v.argmax(-1),neutral_choice[None,:])

    truth = true_values.max(-1).sum()-fees
    untouched = float(sum(fixed[data.states[k],:3] @ true_values[i] for i,k in enumerate(states))-fees)
    draws = rng.choice(len(symbols),size=(HISTORIES,max(HORIZONS)),p=true_obs)
    rows = np.arange(HISTORIES)
    frequencies = np.zeros((HISTORIES,len(symbols)),dtype=int)
    snapshots = {}

    def evaluate(choices):
        return true_values[np.arange(len(states)),choices].sum(-1)-fees

    for length in range(max(HORIZONS)+1):
        if length in HORIZONS:
            belief, excluded = posterior(frequencies,recorded)
            gains = np.einsum("hk,ksa->hsa",frequencies,certificate)
            values = (gains+2*prior[None,:,:]).argmax(-1)
            indicators = {
                "frozen":np.full(HISTORIES,untouched),
                "library-zero":evaluate(library_choice(np.full((HISTORIES,2),.5))),
                "library":evaluate(library_choice(belief)),
                "receipt-fit":evaluate(values),
                "oracle":np.full(HISTORIES,truth),
            }
            if extension is not None:
                decisions = extension(frequencies, recorded, initial, belief, excluded, values, library_choice)
                indicators.update({name: evaluate(choice) for name,choice in decisions.items()})
            assert all(np.all(row<=truth+1e-9) for row in indicators.values())
            if length == 0:
                assert np.allclose(indicators["library"],indicators["receipt-fit"])
            paired = indicators["receipt-fit"]-indicators["library"]
            snapshots[length] = dict(net={name:float(row.mean()) for name,row in indicators.items()},
                                     standard_error=float(paired.std(ddof=1)/np.sqrt(HISTORIES)),
                                     library_exclusion=float(excluded.mean()))
            if "support-selector" in indicators:
                gain = indicators["support-selector"]-indicators["library"]
                snapshots[length]["selector_standard_error"] = float(gain.std(ddof=1)/np.sqrt(HISTORIES))
        if length < max(HORIZONS):
            frequencies[rows,draws[:,length]] += 1
    return dict(horizons=snapshots,fee=fees,possible_history_symbols=len(symbols))


def run(extension=None):
    torch.set_num_threads(1)
    rng = np.random.default_rng(SEED)
    registry = s.read(s.original.REGISTRY)
    draws = {r["draw"]:r for r in registry["accepted"]}
    rank_file = s.read(HERE.parent/"ranking.json")
    old_w = torch.tensor(s.read(s.FIT)["weights"],dtype=torch.float64)
    op = np.asarray(s.read(HERE.parent/"joint-opener.json")["weights"])
    value = np.asarray(s.read(HERE.parent/"recipient.json")["weights"])

    def grid_for(draw):
        with patch.dict(s.shared.FIXTURES,{"unknown":s.original.fixture(draws[draw])}):
            return s.shared.Grid("unknown")

    regions = {f"space-{i}":("space",grid_for(i)) for i in registry["partition"]["reserved"]}
    regions.update({k:(k,s.shared.Grid(k)) for k in ("mali","myanmar")})
    results = {}
    for name,(family,grid) in regions.items():
        data = s.original.data_for(grid)
        original = data.probabilities(old_w).numpy()
        first = c.r.opener.choose(data,original,c.r.opener.basis(data,data.prior,original),op,s.base.FEE,"joint-fitted")
        fit = c.r.ranking.measure(data,first,c.r.recipient.aggregate(data,first),np.asarray(rank_file["coef"]),value)
        fixed = fit["fixed"][0]
        uniform = data.probabilities(torch.zeros_like(old_w)).numpy()
        neutral = c.r.recipient.aggregate(data,uniform)
        results[name] = {}
        for channel, shared in (("silent",False),("shared-peer",True)):
            library = [c.model(grid,family,data,c.script(grid,high,shared)) for high in (True,False)]
            targets = {kind:c.model(grid,family,data,alternative(grid,kind,shared))
                       for kind in ("median","veto-conditioned","public-priority")}
            targets["mixture"] = mixed(*library)
            if extension is not None:
                targets["mixture-low"] = mixed(*library, .2)
                targets["mixture-high"] = mixed(*library, .8)
            if shared:
                targets["broadcast-median"] = c.model(grid,family,data,alternative(grid,"broadcast-median",shared))
            results[name][channel] = {kind:calc(grid,family,data,fixed,library,target,neutral,rng,extension)
                                      for kind,target in targets.items()}
    macro = {}
    for channel in ("silent","shared-peer"):
        by_variant = {}
        for kind in results["space-198"][channel]:
            by_variant[kind] = {
                h:{name:mean(row[channel][kind]["horizons"][h]["net"][name] for row in results.values())
                   for name in results["space-198"][channel][kind]["horizons"][h]["net"]}
                for h in HORIZONS
            }
        macro[channel] = by_variant
    pins=(Path(__file__),HERE/"unknown-partner-protocol.md",HERE/"crossplay.py",HERE/"render.py",HERE.parent/"ranking.json")
    return dict(conditions=results,macro=macro,seed=SEED,histories_per_condition=HISTORIES,
                hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in pins})


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
