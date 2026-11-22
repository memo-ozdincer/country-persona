"""Train two decentralized selectors from shared released-record reward."""
import argparse
import json
from itertools import product
from pathlib import Path

import numpy as np

import render
from headroom import optimize, slates

HERE=Path(__file__).resolve().parent
TRAIN_KEEP=.65
HELD=(.45,.85)
UPDATES=256
LEARNING_RATE=.15


def plan():
    paths=(Path(__file__),HERE/"protocol.md",HERE/"render.py",HERE/"bank.json",
           render.PRIOR/"headroom.py",render.PRIOR/"results.json",
           render.bank.PRIOR/"coverage.json",render.bank.previous.RELEASE/"release.json")
    return {"updates":UPDATES,"learning_rate":LEARNING_RATE,"train":TRAIN_KEEP,"held":list(HELD),
            "pins":{str(p.relative_to(HERE.parents[1])):render.bank.suite.pin(p) for p in paths}}


def prepare():
    case=render.e.cases()["tribunals"]
    own=[[row["id"] for row in deck] for deck in case["owned"]]
    observed=render.e.read(HERE/"bank.json")
    reward=np.array([[[observed[f"{order}/{a}/{b}"]["score"]["released_70"]
                       for b in own[1]] for a in own[0]] for order in (0,1)],dtype=float)
    return own,reward


def evaluate(reward, weights, keep, peers, greedy, with_gradients=False):
    values=[]
    gradients=np.zeros_like(weights)
    mass=[slates(tuple(range(n)),keep) for n in (2,4)]

    def prob(logits, legal):
        if greedy:
            output=np.zeros(len(legal))
            output[int(np.argmax(logits[legal]))]=1.
            return output
        legal_logits=logits[legal]
        p=np.exp(legal_logits-np.max(legal_logits))
        return p/p.sum()

    for order in (0,1):
        matrix=reward[order] if order==0 else reward[order].T
        total=0.
        for (a,pa),(b,pb) in product(mass[order],mass[1-order]):
            a,b=list(a),list(b)
            p=prob(weights[order,0],a)
            values_for_first=[]
            for i,x in enumerate(a):
                state=x+1 if peers else 0
                q=prob(weights[order,state+5],b)
                outcomes=matrix[x,b]
                target=float(q @ outcomes)
                values_for_first.append(target)
                if with_gradients:
                    gradients[order,state+5,b]+=.5*pa*pb*p[i]*q*(outcomes-target)
            target=float(p @ values_for_first)
            total+=pa*pb*target
            if with_gradients:
                gradients[order,0,a]+=.5*pa*pb*p*(np.array(values_for_first)-target)
        values.append(total)
    return values,gradients


def fit(reward,peers,spec):
    weights=np.zeros((2,10,4))
    first=np.zeros_like(weights)
    second=np.zeros_like(weights)
    log=[]
    for step in range(1,spec["updates"]+1):
        expected,grad=evaluate(reward,weights,spec["train"],peers,False,True)
        grad/=10.
        first=.9*first+.1*grad
        second=.999*second+.001*grad**2
        step_size=spec["learning_rate"]/(1-.9**step)
        weights+=step_size*first/(np.sqrt(second/(1-.999**step))+1e-8)
        if step in (1,8,32,128,spec["updates"]):
            log.append({"step":step,"expected":expected,"gradient_norm":float(np.linalg.norm(grad)),
                        "greedy_after_update":evaluate(reward,weights,spec["train"],peers,True)[0]})
    return weights,log


def score(spec):
    own,reward=prepare()
    coverage=render.e.read(render.bank.PRIOR/"coverage.json")[render.CASE]["cases"]
    baseline={tuple(x["source_ids"]):x["potential_points"] for x in coverage}
    assert all(reward[o,i,j]==baseline[own[0][i],own[1][j]] for o,i,j in product(range(2),range(2),range(4)))
    fitted={name:fit(reward,peers,spec) for name,peers in (("independent",False),("peer",True))}
    rows=[]
    for keep in (*spec["held"],spec["train"]):
        outcomes={
            mode: evaluate(reward,weights,keep,mode=="peer",True)[0]
            for mode,(weights,_) in fitted.items()
        }
        outputs=[]
        for order in (0,1):
            exact=optimize(baseline,slates(own[0],keep),slates(own[1],keep),order)
            values={name:round(scores[order],8) for name,scores in outcomes.items()}
            assert all(values[mode]<=exact[mode]+1e-7 for mode in values)
            outputs.append({"order":order,"learned":values,"rubric_rule_and_oracle":exact})
        rows.append({"retention":keep,"results":outputs})
    return {"training":{name:{"logits":weights.tolist(),"trace":trace} for name,(weights,trace) in fitted.items()},
            "reward":reward.tolist(),"evaluation":rows}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan",action="store_true")
    a=p.parse_args()
    spec=plan()
    if not a.plan:
        assert spec==render.e.read(HERE/"plan.json")
    print(json.dumps(spec if a.plan else score(spec),indent=2))
