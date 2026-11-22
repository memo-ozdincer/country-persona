"""Estimate how the chosen writer reward changes evidence selected by a team."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
RUNS=HERE.parents[2]
AFG=RUNS/"afghanistan-2721-source-contrast"
SEED=772521
HISTORIES=256
HORIZONS=(16,64,256)
RATES=(.35,.55,.75,.95)
PRIORS=(.25,.5,.75)
COLLECT=(.55,.5)
STATES=list(product((None,0,1),repeat=2))
RIDGE=.5


def read(p):
    return json.loads(p.read_text())


def pin(p):
    return sha256(p.read_bytes()).hexdigest()


def plan():
    sources=(Path(__file__),HERE/"protocol.md",AFG/"results.json",AFG/"native-comparison/scores.json",
             AFG/"native-comparison/plan.json",HERE.parent/"plan.json",HERE.parent/"results.json")
    return {"seed":SEED,"horizons":list(HORIZONS),"histories":HISTORIES,"ridge":RIDGE,
            "pins":{str(p.relative_to(RUNS)):pin(p) for p in sources}}


def banks():
    source=read(AFG/"native-comparison/scores.json")
    receipts=read(AFG/"native-comparison/plan.json")["receipt_keys"]
    by_mode=source["grades"]
    authored,native,base=(
        np.asarray([by_mode[mode][f"{a}/{b}"]["released"] for a,b in STATES],dtype=float)
        for mode in ("authored_comparison","verbatim_plus_native","verbatim"))
    both=np.asarray([int(a is not None and a==b) for a,b in STATES])
    blocks=np.asarray([int(bool(by_mode["verbatim_plus_native"][f"{a}/{b}"]["blockers"])) for a,b in STATES])
    assert np.all(authored==base+22*both)
    assert np.all(native==base*(1-blocks))
    for ix,(early,late) in enumerate(STATES):
        if early is None or late is None:
            assert authored[ix]==native[ix]==base[ix]
    alternatives={}
    for variant in source["balanced_guard_sensitivity"]:
        checked=native.copy()
        for key in variant["cleared"]:
            state,= [name for name,id_ in receipts.items() if id_==key]
            index=next(i for i,(a,b) in enumerate(STATES) if f"{a}/{b}"==state)
            checked[index]=authored[index]
        alternatives["+".join(variant["cleared"]) or "strict"]=checked
    return {"authored":authored,"native":native,"mixed":(authored+native)/2},base,both,blocks,alternatives


def sample(players,option):
    shape=(HISTORIES,max(HORIZONS))
    card,early,late,random_action,writer=players
    assert card.shape==shape
    actions=np.array(option,dtype=int)
    emitted=actions[(random_action*len(actions)).astype(int)]
    received=np.where(late,emitted,-1)
    slots=(np.where(early,card,-1)+1)*3+(received+1)
    return slots,writer


def fits(received,writer,tables,base):
    counts=np.eye(len(STATES))[received]
    result={}
    for key in tables:
        if key=="mixed":
            observed=np.where(writer,tables["native"][received],tables["authored"][received])
        else:
            observed=tables[key][received]
        correction=observed-base[received]
        estimates=base+np.einsum("hts,ht->hs",counts,correction)/(counts.sum(1)+RIDGE)
        result[key]=estimates
    return result


def branch_matrix(policies,q,prior):
    columns,sendrate= np.zeros((len(policies),len(STATES))),np.zeros(len(policies))
    for i,policy in enumerate(policies):
        for truth,first,receipt in product(range(2),repeat=3):
            early=truth if first else None
            action=policy[truth+1 if first else 0]
            late=action if action!=-1 and receipt else None
            p=(prior if truth==0 else 1-prior)*(q if first else 1-q)*(q if receipt else 1-q)
            columns[i,STATES.index((early,late))]+=p
            sendrate[i]+=p*(action!=-1)
    assert np.allclose(columns.sum(1),1.)
    return columns,sendrate


def evaluate(fitted,policies,tables,both,blocks,alternatives):
    rows=[]
    for q,prior in product(RATES,PRIORS):
        if (q,prior)==COLLECT:
            continue
        mass,sends=branch_matrix(policies,q,prior)
        candidates={name:np.argmax(values@mass.T,axis=-1) for name,values in fitted.items()}
        scripted=policies.index((0,0,1))
        candidates["informed_match"]=np.full(HISTORIES,scripted)
        scores={}
        for name,learned in candidates.items():
            vectors=mass[learned]
            rolled={key:float((vectors@values).mean()) for key,values in tables.items()}
            assert all(rolled[key]<=float((mass @ values).max())+1e-9 for key,values in tables.items())
            if name=="informed_match":
                assert abs(rolled["authored"]-(34+14*q+22*q*q))<1e-9
            scores[name]={"released":rolled,
                          "pair_coverage":float((vectors@both).mean()),
                          "native_guard_failure":float((vectors@blocks).mean()),
                          "sends":float(sends[learned].mean()),
                          "native_alternate_grades":{label:float((vectors@bank).mean())
                                                     for label,bank in alternatives.items()},
                          "first_state_action_counts":[np.bincount(
                              np.asarray([policies[i][view]+1 for i in learned]),minlength=3).tolist()
                              for view in range(3)]}
        rows.append({"q":q,"prior":prior,"policies":scores})
    scored={k:{"released":{j:float(np.mean([r["policies"][k]["released"][j] for r in rows])) for j in tables},
               **{metric:float(np.mean([r["policies"][k][metric] for r in rows]))
                  for metric in ("pair_coverage","native_guard_failure","sends")}}
            for k in rows[0]["policies"]}
    return {"mean":scored,"conditions":rows}


def run():
    assert read(HERE/"plan.json")==plan()
    tables,base,both,blocks,alternatives=banks()
    rng=np.random.default_rng(SEED)
    q,prior=COLLECT
    shape=(HISTORIES,max(HORIZONS))
    draws=((rng.random(shape)>=prior).astype(int),rng.random(shape)<q,rng.random(shape)<q,
           rng.random(shape),rng.random(shape)<.5)
    output={}
    for name,options in (("mandatory",(0,1)),("optional",(-1,0,1))):
        receipt,switch=sample(draws,options)
        policies=list(product(options,repeat=3))
        output[name]={str(n):evaluate(fits(receipt[:,:n],switch[:,:n],tables,base),
                                        policies,tables,both,blocks,alternatives)
                      for n in HORIZONS}
    return {"plan_sha256":pin(HERE/"plan.json"),"dispatch":output}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run"))
    print(json.dumps({"plan":plan,"run":run}[parser.parse_args().mode](),indent=2))
