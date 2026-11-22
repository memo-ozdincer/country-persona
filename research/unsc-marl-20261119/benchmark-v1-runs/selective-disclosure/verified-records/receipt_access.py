"""Find worthwhile archival receipt reads without changing a live decision budget."""
from collections import defaultdict
from fractions import Fraction
from functools import cache
from hashlib import sha256
from itertools import product
import json
from statistics import mean
from unittest.mock import patch

import numpy as np
import torch

import crossplay as c

HERE, s = c.HERE, c.s
FEES = (.001,.003,.01)
LIMIT = 4
VIEWS = ("presence","package","grade","full")


def link_view(report, level):
    if level == "presence":
        return report is not None
    if report is None or level == "full":
        return report
    return report[0 if level == "package" else 1]


def categories(models, view):
    outcomes = defaultdict(lambda: [Fraction(0), Fraction(0)])
    for i, model in enumerate(models):
        for (state, report), p in model[1]["public"].items():
            key = state, link_view(report, view)
            mass = Fraction(p).limit_denominator(100_000)
            assert abs(float(mass)-p) < 1e-12
            outcomes[key][i] += mass
    assert all(sum(prob[i] for prob in outcomes.values()) == 1 for i in range(2))
    tv = float(sum(abs(a-b) for a,b in outcomes.values())/2)
    return tuple(tuple(val) for val in outcomes.values()), tv


def explore(values, fees, law, price):
    def select(belief):
        p = float(belief)
        scores = p*values[0] + (1-p)*values[1]
        choices = scores.argmax(-1)
        real = values[:,np.arange(len(choices)),choices].sum(-1)-fees
        return real

    @cache
    def predict(belief):
        events = []
        for skill in law:
            mass = belief*skill[0]+(1-belief)*skill[1]
            if mass:
                events.append((belief*skill[0]/mass,skill,mass))
        assert sum(event[2] for event in events) == 1
        return tuple(events)

    @cache
    def optimal(belief, left):
        p = float(belief)
        reward = select(belief)
        stop = p*reward[0] + (1-p)*reward[1]
        if not left:
            return stop, False
        children = predict(belief)
        value = sum(float(weight)*optimal(post,left-1)[0] for post,_,weight in children)-price
        return (value,True) if value > stop+1e-12 else (stop,False)

    @cache
    def dispatch(belief,left, adaptive):
        can_read = bool(left and (not adaptive or optimal(belief,left)[1]))
        if not can_read:
            return select(belief), np.zeros(2)
        accumulated = np.zeros(2)
        read_count = np.ones(2)
        for post, weight, _ in predict(belief):
            signal = np.asarray(weight,dtype=float)
            add, count = dispatch(post,left-1,adaptive)
            accumulated += signal * add
            read_count += signal * count
        return accumulated, read_count

    initial = Fraction(1,2)
    res = {}
    for name,left,adaptive in (("none",0,False),("first",1,False),("first-four",4,False),("adaptive",LIMIT,True)):
        gross, reads = dispatch(initial,left,adaptive)
        returns = gross-reads*price
        res[name] = dict(net=returns.tolist(), reads=reads.tolist(),
                         mean_net=float(returns.mean()), mean_reads=float(reads.mean()))
    exact = values.max(-1).sum(-1)-fees
    res["known"] = dict(net=exact.tolist(), reads=[0.,0.], mean_net=float(exact.mean()), mean_reads=0.)
    assert abs(res["adaptive"]["mean_net"]-optimal(initial,LIMIT)[0]) < 1e-9
    assert res["adaptive"]["mean_net"] <= res["known"]["mean_net"]+1e-9
    assert all(res["adaptive"]["mean_net"] >= r["mean_net"]-1e-9 for name,r in res.items() if name!="known")
    return res


def run():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    entries = {row["draw"]:row for row in registry["accepted"]}
    earlier = s.read(HERE/"crossplay.json")

    def make(draw):
        with patch.dict(s.shared.FIXTURES,{"receipt-access":s.original.fixture(entries[draw])}):
            return s.shared.Grid("receipt-access")

    cases = {f"space-{i}":("space",make(i)) for i in registry["partition"]["reserved"]}
    cases.update({family:(family,s.shared.Grid(family)) for family in ("mali","myanmar")})
    out = {}
    for label,(family,grid) in cases.items():
        data = s.original.data_for(grid)
        out[label] = {}
        for state, paid in (("silent",False),("shared-peer",True)):
            models = [c.model(grid,family,data,c.script(grid,high,paid)) for high in (True,False)]
            states = sorted(set(models[0][0])|set(models[1][0]), key=str)
            values = np.asarray([[m[0].get(k,np.zeros(3)) for k in states] for m in models])
            fees = np.asarray([m[2] for m in models])
            variations = {}
            for view in VIEWS:
                law,tv = categories(models,view)
                rates = {price:explore(values,fees,law,price) for price in FEES}
                ref = earlier["cases"][label][state]["channels"]["public"]["histories"]["4"]["policies"]
                if view == "full":
                    assert abs(rates[FEES[0]]["first-four"]["mean_net"]+4*FEES[0]
                               -ref["posterior-planner"]["mean_net"]) < 1e-9
                if view == "presence":
                    assert tv == 0
                    assert all(rate["adaptive"]["mean_reads"] == 0 for rate in rates.values())
                variations[view] = dict(total_variation=tv,prices=rates)
            out[label][state] = variations
    macro = {}
    for state,view in product(("silent","shared-peer"),VIEWS):
        macro[f"{state}/{view}"] = {
            fee: {arm: {k:mean(row[state][view]["prices"][fee][arm][k] for row in out.values())
                         for k in ("mean_net","mean_reads")} for arm in ("none","first","first-four","adaptive","known")}
            for fee in FEES
        }
    paths=(HERE/"receipt-access-protocol.md",HERE/"crossplay.json",HERE/"render.py")
    return dict(cases=out,macro=macro,pins={p.name:sha256(p.read_bytes()).hexdigest() for p in paths})


if __name__=="__main__":
    print(json.dumps(run(),indent=2,ensure_ascii=False))
