"""Fit shared reward heads over raw or receipt-centered native margins."""
import argparse
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent
sys.path.insert(0,str(PRIOR))
import reward_head as head
import held_native as held

READ=head.READ
MODES=("raw_once","reader_raw","centered_once")
ORDERS=("ab","ba")
RUNS=head.RUNS
AFG=RUNS/"afghanistan-2721-source-contrast"


def plan():
    files=(Path(__file__),HERE/"protocol.md",Path(head.__file__),Path(held.__file__),PRIOR/"verified.json",
           PRIOR/"fit.json",PRIOR/"scores.json",PRIOR.parent/"verified.json",AFG/"results.json",
           AFG/"text-decoder/scores.json",AFG/"text-decoder/lexical-contrast/scores.json")
    return {"sha256":{str(path.relative_to(RUNS)):head.prior.digest(path) for path in files}}


def native(outputs, prefix, view, order):
    row=outputs[f"{prefix}/{view}/{order}"]["logits"]
    return (row["A"]-row["B"])*(1 if order=="ab" else -1)


def choice_vector(margin):
    return np.array([margin/2,-margin/2])


def transform(world,mode,outputs,key,order,intervention):
    centered=intervention=="centered_once"
    reference=native(outputs,key,"none",order) if centered else 0.
    later=np.stack([choice_vector(native(outputs,key,v,order)-reference) for v in head.VIEWS[mode]])
    third=choice_vector(native(outputs,key,"independent",order)) if intervention=="raw_once" else np.zeros(2)
    return world|{"language":(later,third)}


def fit(rows,outputs,intervention):
    problems=[transform(world,mode,outputs,key,order,intervention)
              for key,modes in rows.items() for mode,world in modes.items() for order in ORDERS]
    weights=np.zeros(3)
    trace=[]
    for step in range(head.STEPS+1):
        values=[head.objective(world,weights) for world in problems]
        gradient=np.mean([g for _,g in values],axis=0)-head.PENALTY*weights
        if step in (0,30,60,120):
            trace.append({"step":step,"mean_stochastic_reward":mean(row[0] for row in values),
                          "weights":weights.tolist()})
        if step<head.STEPS:
            weights+=head.RATE*gradient
    return weights,trace


def score(world,weights):
    model={"heads":{key:[{"weights":np.asarray(weights).tolist()}] for key in ("hybrid","typed_only")}}
    return head.score(world,model)["hybrid"]


def evaluate(weights,output):
    _,_,raw,edges,true=held.setup()
    local=[np.asarray(values) for values in raw]
    archived=READ(PRIOR/"scores.json")["held"]
    rows=[]
    for share,rate in product(held.SHARES,held.RATES):
        key=f"{share}/{rate}"
        reusable=head.sample(local,edges,rate,share,true,output,key)
        for mode,world in reusable.items():
            for order in ORDERS:
                selected={name:score(transform(world,mode,output,key,order,name),w)
                          for name,w in weights.items()}
                selected["fixed_centered"]=score(transform(world,mode,output,key,order,"centered_once"),[1.,0.,1.])
                selected.update({name:archived[key][mode][name] for name in
                                 ("raw_qwen","hybrid","typed_only","fixed_refreshed","oracle")})
                rows.append({"case":key,"observation":mode,"order":order,"outcomes":selected})
    means={}
    for mode in head.MODES:
        panel=[row["outcomes"] for row in rows if row["observation"]==mode]
        means[mode]={name:mean(row[name]["released"] for row in panel) for name in panel[0]}
    return {"means":means,"scenes":rows}


def afghanistan(weights):
    base=READ(AFG/"text-decoder/scores.json")
    stress=READ(AFG/"text-decoder/lexical-contrast/scores.json")
    archive=READ(AFG/"results.json")
    margins={mode:{int(k):{o:row[o]["margin_0_minus_1"] for o in ORDERS}
                   for k,row in item["decisions"].items()} for mode,item in base["modes"].items()}
    margins.update({mode:{int(k):{r["order"]:r["margin"] for r in item["orders"]}
                             for k,item in rows["observations"].items()} for mode,rows in stress.items()})
    raw_actions={
        mode:{int(k):{o:row[o]["raw_mapped"] for o in ORDERS} for k,row in value["decisions"].items()}
        for mode,value in base["modes"].items()
    }
    raw_actions.update({
        mode:{int(k):{r["order"]:r["raw"] for r in item["orders"]} for k,item in value["observations"].items()}
        for mode,value in stress.items()
    })
    neutral={o:base["absent"]["orders"][o]["margin_0_minus_1"] for o in ORDERS}
    result=[]
    for mode,raw in margins.items():
        for order in ORDERS:
            shifted={i:row[order]-neutral[order] for i,row in raw.items()}
            controls={"raw":{i:row[order] for i,row in raw_actions[mode].items()},
                      "centered":{i:int(v<0) for i,v in shifted.items()}}
            for name,w in weights.items():
                data=shifted if name=="centered_once" else {i:row[order] for i,row in raw.items()}
                bonus=22*(w[1]+w[2])/7
                controls[name+"_with_checklist"]={i:int(v+bonus*(1 if i==0 else -1)<0) for i,v in data.items()}
            scenes=[]
            for scenario in archive["conditions"]:
                q,p=scenario["receipt_probability"],scenario["first_card_0_probability"]
                for_decoder={name:34+14*q+22*q*q*(p*(a[0]==0)+(1-p)*(a[1]==1))
                             for name,a in controls.items()}
                assert all(v<=scenario["content_ceiling"]+1e-9 for v in for_decoder.values())
                scenes.append({"delivery":q,"prior":p,"released_70":for_decoder})
            result.append({"mode":mode,"first_order":order,"actions":controls,"scenes":scenes})
    return result


def run():
    lock=HERE/"plan.json"
    assert READ(lock)==plan()
    training=head.training_set()
    archived=READ(PRIOR.parent/"verified.json")["outputs"]
    weights,traces={},{}
    for method in MODES:
        weights[method],traces[method]=fit(training,archived,method)
    return {"plan_sha256":head.prior.digest(lock),"training":traces,
            "tribunals":evaluate(weights,READ(PRIOR/"verified.json")["outputs"]),
            "afghanistan":afghanistan(weights)}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run"))
    print(json.dumps({"plan":plan,"run":run}[parser.parse_args().mode](),indent=2))
