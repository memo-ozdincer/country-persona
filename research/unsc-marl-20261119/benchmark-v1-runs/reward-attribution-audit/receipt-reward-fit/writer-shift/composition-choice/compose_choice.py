"""Learn a choice between native composition and a verbatim source record."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
RUNS=HERE.parents[3]
AFG=RUNS/"afghanistan-2721-source-contrast"
REFORM=RUNS/"reform-2553-transfer/learned-send-writer"
SEED=772530
HISTORIES=256
BUDGETS=(16,64,256)
RATES=(.35,.55,.75,.95)
PRIORS=(.25,.5,.75)
COLLECT=(.55,.5)
FEE=.5


def read(path):
    return json.loads(path.read_text())


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def plan():
    files=(Path(__file__),HERE/"protocol.md",AFG/"native-comparison/scores.json",
           AFG/"native-comparison/plan.json",HERE.parent/"results.json",REFORM/"plan.json",
           REFORM/"public-record-anchor/scores.json")
    return {"seed":SEED,"histories":HISTORIES,"budgets":list(BUDGETS),"fee":FEE,
            "sha256":{str(p.relative_to(RUNS)):pin(p) for p in files}}


def afghanistan():
    archive=read(AFG/"native-comparison/scores.json")
    modes=archive["grades"]
    indices=tuple(modes["verbatim"])
    labels=read(AFG/"native-comparison/plan.json")["receipt_keys"]
    def grades(key):
        return np.array([modes[key][state]["released"] for state in indices],dtype=float)
    native,source,verbatim=(grades(key) for key in ("verbatim_plus_native","authored_comparison","verbatim"))

    for row in read(HERE.parent/"results.json")["dispatch"]["optional"]["256"]["conditions"]:
        chosen=row["policies"]
        assert chosen["authored"]["first_state_action_counts"]==[[0,HISTORIES,0],[0,HISTORIES,0],[0,0,HISTORIES]]
        assert chosen["native"]["first_state_action_counts"]==[[0,HISTORIES,0],[0,0,HISTORIES],[HISTORIES,0,0]]

    def layout(q,prior):
        result={}
        for name,policy in (("source_editor",(0,0,1)),("native_reward_editor",(0,1,None))):
            mass=np.zeros(len(indices))
            for card,before,later in product((0,1),repeat=3):
                early=card if before else None
                decision=policy[card+1 if before else 0] if later else None
                p=(prior if card==0 else 1-prior)*(q if before else 1-q)*(q if later else 1-q)
                mass[indices.index(f"{early}/{decision}")]+=p
            result[name]=mass
        return result

    alt={}
    for condition in archive["balanced_guard_sensitivity"]:
        alternative=native.copy()
        for i,state in enumerate(indices):
            if labels[state] in condition["cleared"]:
                alternative[i]=source[i]
        alt["+".join(condition["cleared"]) or "strict"]=alternative
    return {"ids":indices,"native":native,"source":source,"verbatim":verbatim,
            "pairs":source>verbatim,"layout":layout,"alternatives":alt}


def reform():
    archive=read(REFORM/"public-record-anchor/scores.json")
    keys=tuple(archive["grades"])
    source,verbatim=np.zeros(len(keys)),np.zeros(len(keys))
    for branch in archive["branches"]:
        for k,a,v in zip(branch["pair"],branch["typed_scores"],branch["verbatim_scores"],strict=True):
            i=keys.index(k)
            assert source[i] in (0.,a) and verbatim[i] in (0.,v)
            source[i],verbatim[i]=a,v
    native=np.array([archive["grades"][k]["released_70"] for k in keys],dtype=float)
    assert (verbatim>0).all()
    def layout(q,prior):
        result={name:np.zeros(len(keys)) for name in ("funding","inclusion")}
        for branch in archive["branches"]:
            b,mask=branch["early"],branch["mask"]
            weight=(prior if b==0 else 1-prior)*q**mask.bit_count()*(1-q)**(3-mask.bit_count())/q
            for name,k in zip(result,branch["pair"],strict=True):
                result[name][keys.index(k)]+=weight
        return result
    alternatives={}
    for row in archive["guard_sensitivity"]:
        updated=native.copy()
        for k in row["cleared"]:
            updated[keys.index(k)]=archive["grades"][k]["raw_70"][0]
        alternatives["+".join(row["cleared"]) or "strict"]=updated
    return {"ids":keys,"native":native,"source":source,"verbatim":verbatim,
            "pairs":source>verbatim,"layout":layout,"alternatives":alternatives}


def fit(case,rng):
    views=case["layout"](*COLLECT)
    mass=np.mean(list(views.values())[:1] if "source_editor" in views else list(views.values()),axis=0)
    assert abs(mass.sum()-1)<1e-9
    size=(HISTORIES,max(BUDGETS))
    observed=rng.choice(len(case["ids"]),p=mass,size=size)
    use_native=rng.random(size)<.5
    reward=np.where(use_native,case["native"][observed],case["verbatim"][observed])
    residual=(reward-case["verbatim"][observed])*use_native
    indicator=np.eye(len(mass))[observed]*use_native[...,None]
    plans={}
    for n in BUDGETS:
        seen=indicator[:,:n]
        values=np.einsum("hns,hn->hs",seen,residual[:,:n])/(seen.sum(1)+.5)
        plans[str(n)]=values>FEE
    return plans,sha256(observed.astype("<i8").tobytes()+use_native.tobytes()).hexdigest()


def evaluate(case,learned):
    rows=[]
    base,native,source=(case[k] for k in ("verbatim","native","source"))
    for q,prior in product(RATES,PRIORS):
        if (q,prior)==COLLECT:
            continue
        masses=case["layout"](q,prior)
        for editor,mass in masses.items():
            assert abs(mass.sum()-1)<1e-9
            arms={"verbatim":np.zeros_like(learned),"native":np.ones_like(learned),
                  "fit":learned,"writer_oracle":np.broadcast_to(native-base>FEE,learned.shape)}
            scores={}
            for name,choices in arms.items():
                points=np.where(choices,native,base) @ mass
                usage=choices @ mass
                net=points-FEE*usage
                scores[name]={"release":float(points.mean()),"native_use":float(usage.mean()),"net":float(net.mean()),
                    "below_verbatim":float((net<(mass@base)-1e-9).mean()),
                    "alternate_net":{label:float((np.where(choices,updated,base)@mass-FEE*usage).mean())
                                     for label,updated in case["alternatives"].items()}}
            assert scores["fit"]["net"]<=scores["writer_oracle"]["net"]+1e-9
            rows.append({"q":q,"prior":prior,"editor":editor,"source_pair_receipt":float(mass@case["pairs"]),
                         "authored_release":float(mass@source),"outcomes":scores})
    return rows


def run():
    assert read(HERE/"plan.json")==plan()
    rng=np.random.default_rng(SEED)
    dockets={}
    for name,case in (("2721",afghanistan()),("2553",reform())):
        policies,trace=fit(case,rng)
        dockets[name]={"training_trace":trace,"budgets":{
            n:{"admission_rates":dict(zip(case["ids"],choices.mean(0).tolist(),strict=True)),
               "evaluation":evaluate(case,choices)} for n,choices in policies.items()}}
    return {"plan_sha256":pin(HERE/"plan.json"),"dockets":dockets}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run"))
    print(json.dumps({"plan":plan,"run":run}[parser.parse_args().mode](),indent=2))
