"""Replay frozen policies on one new UN-linked workshop with authored receipts."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
MALI=HERE.parent/"mali"
sys.path.insert(0,str(MALI))
import robust_retry_fit as fit

episode=fit.episode
canonical=episode.canonical
router=episode.router
EXPECTED={"us":set("ABDFG"),"ru-overlap":set("BCE"),"ru-impasse":set("CE")}
TIMING={"us":{"focused"},"ru-overlap":{"broad"},"ru-impasse":{"staged","broad"}}
RETRIES=MALI/"evidence/delayed-reply/results.json"
ROBUST=MALI/"evidence/robust-retry/results.json"
SEED=700619


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def eligible(role,item):
    scope,coordinator,consent=(item[k] for k in ("scope","coordination","explicit_consent"))
    return scope not in TIMING[role] and (
        coordinator in ("un","joint") if role=="us" else consent and coordinator in ("host","joint")
    )


def cases(offset=0):
    spec=load(HERE/"case.json")
    packages=tuple(p["id"] for p in spec["options"])
    labels=packages[offset:]+packages[:offset]
    width=len(labels)
    fields=canonical.descriptions(spec,labels)
    masks={label:1<<i for i,label in enumerate(labels)}
    def mask(options):
        return sum(masks[p] for p in options)

    menus={role:{p["id"] for p in spec["options"] if eligible(role,p)} for role in spec["cards"]}
    assert menus==EXPECTED and menus["us"]&menus["ru-overlap"]=={"B"}
    assert not menus["us"]&menus["ru-impasse"]
    tape={(r,t):(0,0) for r in range(2) for t in range(width+1)}
    for order,variant in product(("original","reversed"),("ru-overlap","ru-impasse")):
        cards=("us",variant) if order=="original" else (variant,"us")
        roles=spec["roles"] if order=="original" else spec["roles"][::-1]
        truth=tuple(mask(menus[c]) for c in cards)
        local=tuple(tuple(mask(k for k in labels if k not in spec["later_only"][c] and (k in menus[c])==v)
                          for v in (True,False)) for c in cards)
        scope=tuple(mask(p["id"] for p in spec["options"] if p["scope"] in TIMING[c]) for c in cards)
        later=[{masks[k]:k in menus[c] for k in labels} for c in cards]
        for a,b in product(*(sorted(menus[c]) for c in cards)):
            opening=masks[a],0,masks[b],0
            item=(width,truth,local,opening,scope),tape
            yield (order,variant,a+b),item,later,labels,roles,tuple(menus[c] for c in cards),fields


def trace_score(rows,previous,fits,thresholds):
    paired=episode.paired((item,fields,later) for _,item,later,_,_,_,fields in rows)
    comparison=fit.compare(paired,fits,thresholds,previous)
    extras={}
    for script in ("never","set_first"):
        metrics=Counter()
        for _,item,later,_,_,_,fields in rows:
            with canonical.enabled(fields,"public"):
                result=router.play(item,script,{},recorded=later)
            lhs,rhs=item[0][1]
            label="agreement" if lhs&rhs else "impasse"
            metrics[label,"presentations"]+=1
            for field,value in zip(("solved","slots","checks","questions","answers","scope"),result,strict=True):
                metrics[label,field]+=value
        extras[script]=router.sp.flatten(metrics)
    return {"paired_retry_policies":comparison,"fixed_no_retry":extras}


def evaluate():
    prior=load(RETRIES)["rules"]
    checkpoint=load(ROBUST)
    fits={tuple(k.split("/")):{**v,"weights":np.asarray(v["weights"])} for k,v in checkpoint["critics"].items()}
    thresholds={k:v["selected"] for k,v in checkpoint["validation"].items()}
    rows=list(cases())
    counts=Counter()
    for _,item,_,_,_,_,_ in rows:
        lhs,rhs=item[0][1]
        kind="agreement" if lhs&rhs else "impasse"
        counts[kind]+=1
    clean=trace_score(rows,prior,fits,thresholds)
    for offset in range(1,7):
        assert trace_score(list(cases(offset)),prior,fits,thresholds)==clean
    outputs={"clean":clean}
    physical=[item[0] for _,item,_,_,_,_,_ in rows]
    for name,p in (("independent",0),("persistent",episode.transport.PERSISTENCE)):
        data=[]
        for j in range(12):
            tape=episode.transport.delivery(physical,SEED+j,p)
            data.extend((key,item,*rest) for (key,_,*rest),item in zip(rows,tape,strict=True))
        outputs[name]=trace_score(data,prior,fits,thresholds)
    return {"source_sha256":{p.name:digest(p) for p in (HERE/"case.json",HERE/"facts.json",RETRIES)},
            "robust_fit_sha256":digest(ROBUST),"seed":SEED,
            "scope":"Fictional workshop. Authored role-local receipts and zero fresh verifier calls. Full-information analyst counts form an upper bound. Prior policies are frozen and trained on separate synthetic rows.",
            "full_information_analyst":counts,"clean_package_rotations":7,"conditions":outputs}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
