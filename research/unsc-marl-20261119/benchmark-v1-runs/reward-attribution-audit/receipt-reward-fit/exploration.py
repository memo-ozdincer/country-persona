"""Compare active receipt designs to random exploratory dispatch."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import fit_reward as study

HERE=Path(__file__).resolve().parent
SEED=772512


def physical_maps():
    rows=[]
    for plan in study.POLICIES:
        grid=[]
        for b,mask in product(range(2),study.MASKS):
            a,c=plan[b+1 if mask & 2 else 0],plan[-1]
            state=tuple(v if mask & (1<<i) else -1 for i,v in enumerate((a,b,c)))
            grid.append(study.STATES.index(state))
        rows.append(grid)
    return np.asarray(rows)


def collect(case):
    rng=np.random.default_rng(SEED)
    h,n=study.HISTORY_COUNT,max(study.HORIZONS)
    rate,prior=study.COLLECTION
    observed=(rng.random((h,n))>=prior).astype(int)
    delivery=(rng.random((h,n,3))<rate)@np.array([1,2,4])
    index=observed*8+delivery
    paths=physical_maps()
    mass,_=study.value_matrix(case,rate,prior)
    # Independent mass check against the distribution over hidden cards and delivery.
    probability=np.asarray([(prior if b==0 else 1-prior)*rate**mask.bit_count()*(1-rate)**(3-mask.bit_count())
                            for b,mask in product(range(2),study.MASKS)])
    alternative=np.eye(len(study.STATES))[paths]
    assert np.allclose(mass,np.einsum("pks,k->ps",alternative,probability))
    random=paths[rng.integers(len(paths),size=(h,n)),index]
    cov=np.repeat((np.eye(len(study.EDGES))/study.RIDGE)[None],h,axis=0)
    output=np.zeros((h,n),dtype=int)
    singleton=mass@case["base"]
    basis=case["pair"]
    for t in range(n):
        variances=np.einsum("sj,hjk,sk->hs",basis,cov,basis)
        values=np.log1p(variances)@mass.T
        best=np.isclose(values,values.max(axis=1,keepdims=True),rtol=0,atol=1e-12)
        policy=np.argmax(np.where(best,singleton,-np.inf),axis=1)
        output[:,t]=paths[policy,index[:,t]]
        used=basis[output[:,t]]
        update=np.einsum("hjk,hk->hj",cov,used)
        cov-=np.einsum("hj,hk->hjk",update,update)/(1+np.einsum("hj,hj->h",used,update))[:,None,None]
    return {"uniform":random,"receipt_design":output}


def run():
    historical=study.HERE/"results.json"
    assert study.old.READ(study.HERE/"plan.json")==study.plan()
    report={}
    for case in study.data():
        exposed=collect(case)
        snapshots={}
        for t in study.HORIZONS:
            s={}
            for name,history in exposed.items():
                seen=history[:,:t]
                estimates=study.predict(case,seen)["pair"]
                outcome=study.score(case,{"pair":estimates})
                s[name]={"deployment_mean":outcome["mean"]["pair"],
                         "rollout_mean":float(case["real"][seen].mean()),
                         "ceiling_fraction":outcome["mean_ceiling_fraction"]["pair"],
                         "mean_absolute_reward_error":float(np.abs(estimates-case["real"]).mean())}
            snapshots[str(t)]=s
        report[case["name"]]={"horizons":snapshots,"receipt_trace_sha256":{
            key:sha256(value.astype("<i8").tobytes()).hexdigest() for key,value in exposed.items()}}
    return {"seed":SEED,"pins":{p.name:study.old.prior.digest(p) for p in (
        Path(__file__),HERE/"exploration-protocol.md",historical)},"cases":report}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
