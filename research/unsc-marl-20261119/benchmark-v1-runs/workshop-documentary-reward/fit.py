"""Fit both disclosures with either a decision or a documentary shared reward."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import build

HERE=Path(__file__).resolve().parent
RATES=(.75,.95)
PRICES=(4,10,16)
UPDATES=256
LR=.15


def plan():
    paths=(Path(__file__),HERE/"build.py",HERE/"bank.json",HERE/"protocol.md",build.RELEASE/"release.json")
    return {"rates":list(RATES),"prices":list(PRICES),"updates":UPDATES,"lr":LR,
            "pins":{str(p.relative_to(HERE.parents[1])):sha256(p.read_bytes()).hexdigest() for p in paths}}


def prepare(worlds,order,rate,price):
    components=[]
    for world in worlds.values():
        a,b=[world["local_keys"][side] for side in (order,1-order)]
        for sent,heard,answered,receipt in product(range(2),repeat=4):
            if heard>sent or receipt>answered:
                continue
            observations=f"{heard}{receipt}" if order==0 else f"{receipt}{heard}"
            outcome=world["views"][observations]["score"]
            amount=outcome["released_70"]
            certified=int(outcome["mechanical"]["accepted"])
            fee=price*(sent+answered)
            obs=a+1 if heard else 0
            mass=(rate if heard else 1-rate if sent else 1)*(rate if receipt else 1-rate if answered else 1)
            components.append((a,sent,b*3+obs,answered,mass/4,amount,certified,fee))
    data=np.asarray(components)
    return data[:,:4].astype(int).T,data[:,4],data[:,5],data[:,6],data[:,7]


def evaluate(table,p,q):
    (a,s,b,r),mass,points,correct,cost=table
    sent=np.where(s,p[a],1-p[a])
    reply=np.where(r,q[b],1-q[b])
    weights=sent*reply*mass
    assert abs(np.sum(weights)-1)<1e-8
    return {"documentary":float(weights@(points-cost)), "decision":float(weights@(70*correct-cost)),
            "released":float(weights@points),"certified":float(weights@correct),"send_cost":float(weights@cost),
            "attempts":float(weights@(s+r))}


def fit(table,kind):
    (a,s,b,r),mass,points,correct,cost=table
    reward=points-cost if kind=="documentary" else 70*correct-cost
    x=np.zeros(8)
    first=np.zeros_like(x)
    second=np.zeros_like(x)
    trace=[]
    for step in range(1,UPDATES+1):
        y=1/(1+np.exp(-x))
        p,q=y[:2],y[2:]
        weighted=np.where(s,p[a],1-p[a])*np.where(r,q[b],1-q[b])*mass
        g=np.bincount(a,weighted*reward*(s-p[a]),minlength=2)
        h=np.bincount(b,weighted*reward*(r-q[b]),minlength=6)
        gradient=np.concatenate((g,h))/70
        first=.9*first+.1*gradient
        second=.999*second+.001*gradient**2
        x+=LR*(first/(1-.9**step))/(np.sqrt(second/(1-.999**step))+1e-8)
        if step in (1,32,128,UPDATES):
            trace.append({"step":step,"expected":float(weighted@reward),"norm":float(np.linalg.norm(gradient))})
    choices=(x>0).astype(int)
    return {"actions":choices.tolist(),"logits":x.tolist(),"gradients":trace,
            "score":evaluate(table,choices[:2],choices[2:])}


def benchmarks(table, stop):
    mixed=[]
    for actions in product(range(2),repeat=8):
        act=np.asarray(actions)
        mixed.append({"actions":list(actions),"score":evaluate(table,act[:2],act[2:])})
    return {"disclose":evaluate(table,np.ones(2),np.ones(6)),
            "certificate_stop":evaluate(table,np.ones(2),stop),
            **{f"exact_{mode}":max(mixed,key=lambda row:row["score"][mode])
               for mode in ("decision","documentary")}}


def report():
    data=build.e.read(HERE/"bank.json")
    results=[]
    for family,order,rate,price in product(data,(0,1),RATES,PRICES):
        worlds=data[family]["cases"]
        table=prepare(worlds,order,rate,price)
        stop=np.ones((2,3))
        for value in (0,1):
            compatible=[w for w in worlds.values() if w["local_keys"][order]==value]
            visible="10" if order==0 else "01"
            labels={tuple(w["views"][visible]["options"]) for w in compatible}
            assert len(labels)==1
            stop[:,value+1]=int(not next(iter(labels)))
        controls=benchmarks(table,stop.reshape(-1))
        fitted={kind:fit(table,kind) for kind in ("decision","documentary")}
        for kind in fitted:
            assert fitted[kind]["score"][kind] <= controls["exact_"+kind]["score"][kind]+1e-8
        results.append({"family":family,"order":order,"rate":rate,"price":price,
                        "fitted":fitted,"controls":controls})
    return results


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",action="store_true")
    a=parser.parse_args()
    spec=plan()
    if not a.plan:
        assert spec==build.e.read(HERE/"plan.json")
    print(json.dumps(spec if a.plan else report(),indent=2))
