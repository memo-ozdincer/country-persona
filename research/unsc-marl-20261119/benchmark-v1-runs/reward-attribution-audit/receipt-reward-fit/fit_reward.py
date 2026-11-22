"""Fit joint documentary rewards from masked receipts and one terminal score."""
import argparse
from hashlib import sha256
from itertools import combinations,product
from pathlib import Path
import json
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
RUNS=HERE.parent.parent
ARCHIVE=RUNS/"reform-2553-transfer/native-decisions/reward-head"
sys.path.insert(0,str(ARCHIVE))
import held_native as tribunal
import reward_head as old

REFORM=old.reform
SEED=772511
HISTORY_COUNT=256
HORIZONS=(4,16,64,256)
COLLECTION=(.55,.25)
RIDGE=.5
ALL=list(product(range(2),repeat=3))
MASKS=range(8)
STATES=list(product((-1,0,1),repeat=3))
EDGES=[(i,j,a,b) for i,j in combinations(range(3),2) for a,b in product(range(2),repeat=2)]
POLICIES=np.asarray(list(product(range(2),repeat=4)))


def plan():
    paths=(Path(__file__),HERE/"protocol.md",Path(tribunal.__file__),Path(old.__file__),
           Path(REFORM.__file__),REFORM.HERE/"docket.json",REFORM.HERE/"results.json",
           Path(old.old.__file__),old.PARTNER.parent/"private-results.json")
    return {"seed":SEED,"history_count":HISTORY_COUNT,"horizons":list(HORIZONS),
            "collection":list(COLLECTION),"ridge":RIDGE,
            "sha256":{str(path.relative_to(RUNS)):old.prior.digest(path) for path in paths}}


def source(case, known, rewards):
    table={}
    for action,mask in product(ALL,MASKS):
        delivered=tuple(choice if mask & (1<<i) else -1 for i,choice in enumerate(action))
        value=rewards[action][mask]
        if delivered in table:
            assert table[delivered]==value
        table[delivered]=value
    real=np.asarray([table[state] for state in STATES],dtype=float)
    public=table[-1,-1,-1]
    baseline=np.asarray([public+sum(known[i][v] for i,v in enumerate(state) if v!=-1)
                         for state in STATES],dtype=float)
    pair=np.asarray([[int(state[i]==a and state[j]==b) for i,j,a,b in EDGES]
                    for state in STATES],dtype=float)
    assert all(table[state]==baseline[ix] for ix,state in enumerate(STATES) if state.count(-1)>=2)
    return {"name":case,"real":real,"base":baseline,"pair":pair,"reward_array":rewards}


def data():
    _,_,local,_,true=tribunal.setup()
    yield source("2422",local,true)
    for name,permutation in REFORM.ORDERS.items():
        _,local,_,_,true=REFORM.setup(permutation)
        yield source("2553-"+name,local,true)


def histories(rng):
    rate,prior=COLLECTION
    shape=(HISTORY_COUNT,max(HORIZONS))
    actions=[rng.integers(0,2,shape),(rng.random(shape)>=prior).astype(int),rng.integers(0,2,shape)]
    states=np.stack([np.where(rng.random(shape)<rate,choice,-1)+1 for choice in actions],axis=-1)
    return states @ np.array([9,3,1])


def predict(case,observed):
    truth,base,pair=(case[key] for key in ("real","base","pair"))
    # Simulate exactly one scalar observation per logged receipt tuple.
    residual=truth[observed]-base[observed]
    basis=np.eye(len(STATES))[observed]
    counts=basis.sum(axis=1)
    totals=np.einsum("hns,hn->hs",basis,residual)
    averages=np.divide(totals,counts,out=np.zeros_like(totals),where=counts>0)
    x=pair[observed]
    gram=np.einsum("hnj,hnk->hjk",x,x)+RIDGE*np.eye(len(EDGES))
    lhs=np.einsum("hnj,hn->hj",x,residual)
    coeff=np.linalg.solve(gram,lhs[...,None])[...,0]
    return {"pair":base+coeff@pair.T,"lookup":base+averages}


def value_matrix(case,rate,prior):
    mass=np.zeros((len(POLICIES),len(STATES)))
    direct=[]
    for ix,policy in enumerate(POLICIES):
        total=0.
        for b,mask in product(range(2),MASKS):
            a=policy[b+1 if mask & 2 else 0]
            c=policy[-1]
            receipt=tuple(v if mask & (1<<j) else -1 for j,v in enumerate((a,b,c)))
            weight=(prior if b==0 else 1-prior)*rate**mask.bit_count()*(1-rate)**(3-mask.bit_count())
            mass[ix,STATES.index(receipt)]+=weight
            total+=weight*case["reward_array"][a,b,c][mask]
        direct.append(total)
    assert np.allclose(mass.sum(axis=1),1.)
    assert np.allclose(mass@case["real"],direct)
    return mass,np.asarray(direct)


def score(case,predictions):
    rows=[]
    panels={m:[] for m in predictions}
    static=np.flatnonzero((POLICIES[:,0]==POLICIES[:,1])&(POLICIES[:,0]==POLICIES[:,2]))
    for rate,prior in product(REFORM.RATES,REFORM.SHARES):
        if (rate,prior)==COLLECTION:
            continue
        matrix,truth=value_matrix(case,rate,prior)
        ceiling=float(truth.max())
        chosen=int(np.argmax(matrix@case["base"]))
        baseline=float(truth[chosen])
        result={}
        for name, estimated in predictions.items():
            forecast=estimated@matrix.T
            effect=truth[np.argmax(forecast,axis=1)]
            no_text=truth[static[np.argmax(forecast[:,static],axis=1)]]
            panels[name].append(effect)
            result[name]={"mean":float(effect.mean()),"static_fit":float(no_text.mean()),
                          "ceiling_fraction":float(np.isclose(effect,ceiling,atol=1e-9,rtol=0).mean()),
                          "below_standalone_fraction":float((effect<baseline-1e-9).mean())}
        rows.append({"rate":rate,"prior":prior,"standalone":baseline,"oracle":ceiling,
                     "static_oracle":float(truth[static].max()),"policies":result})
    return {"contexts":rows,
            "mean":{name:float(np.mean(effect)) for name,effect in panels.items()},
            "mean_ceiling_fraction":{name:float(np.mean([v["policies"][name]["ceiling_fraction"] for v in rows]))
                                     for name in predictions},
            "comparison":{name:float(np.mean([v[name] for v in rows]))
                          for name in ("standalone","oracle","static_oracle")}}


def run():
    pinned=HERE/"plan.json"
    assert old.READ(pinned)==plan()
    rng=np.random.default_rng(SEED)
    result={}
    for case in data():
        received=histories(rng)
        panels={}
        for n in HORIZONS:
            models=predict(case,received[:,:n])
            outcomes=score(case,models)
            outcomes["mean_absolute_reward_error"]={
                name:float(np.mean(np.abs(est-case["real"]))) for name,est in models.items()}
            panels[str(n)]=outcomes
        result[case["name"]]={"panels":panels,
                              "history_ids_sha256":sha256(received.astype("<i8").tobytes()).hexdigest()}
    return {"plan_sha256":old.prior.digest(pinned),"dockets":result}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run"))
    print(json.dumps({"plan":plan,"run":run}[parser.parse_args().mode](),indent=2))
