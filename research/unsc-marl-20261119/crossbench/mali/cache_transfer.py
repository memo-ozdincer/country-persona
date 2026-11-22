"""Replay receipt reuse and frozen policies on the Myanmar case family."""
import argparse
from collections import Counter
import json
from itertools import product
from pathlib import Path

import numpy as np

import opening_gate as opening
import receipt_actor as neural
import reuse_receipt as reuse

study,group,router=opening.study,opening.group,opening.policy
MYANMAR=study.MYANMAR
BASE=group.BASE
FACTORED=MYANMAR/"evidence/factored/metrics.json"
PROFILE=MYANMAR/"evidence/joint-receipt/pooled-layouts.json"
RAW=MYANMAR/"evidence/metrics.json"
STABLE=MYANMAR/"evidence/joint-receipt/metrics.json"


def cases(pack,offset):
    spec=study.mali.load(MYANMAR/"case.json")
    labels=tuple(o["id"] for o in spec["options"])
    width=len(labels)
    labels=labels[offset:]+labels[:offset]
    bits={label:1<<i for i,label in enumerate(labels)}
    menus={role:{p for p,sign in pack["package"][role].items() if sign["expected"]}
           for role in spec["cards"]}
    truth={"india":set("ABG"),"uk-overlap":set("BCD"),"uk-impasse":set("CD")}
    assert menus==truth
    tape={(r,t):(0,0) for r in range(2) for t in range(width+1)}
    for order,variant in product(("original","reversed"),("uk-overlap","uk-impasse")):
        cards=("india",variant)
        roles=spec["roles"]
        if order=="reversed":
            cards,roles=cards[::-1],roles[::-1]
        private=tuple(sum(bits[p] for p in menus[role]) for role in cards)
        local=tuple(tuple(sum(bits[p] for p in labels if p not in spec["later_only"][role]
                              and pack["package"][role][p]["admitted"] is v)
                          for v in (True,False)) for role in cards)
        scope=tuple(sum(bits[p] for p in pack["scope"][role]["admitted_exclusions"]) for role in cards)
        later=[{bits[p]:pack["package"][role][p]["admitted"] for p in labels} for role in cards]
        for left,right in product(*(sorted(menus[role]) for role in cards)):
            first=(bits[left],0,bits[right],0)
            case=(width,private,local,first,scope)
            key=order,variant,left+right
            yield key,(case,tape),later,labels,roles,tuple(menus[r] for r in cards)


def replay(pack,actors,saved_gate,offset):
    variants=(
        ("discarded_after",reuse.defer.enabled,BASE,{}),
        ("discarded_early",reuse.defer.enabled,"set_first",{}),
        ("reused_after",reuse.enabled,BASE,{}),
        ("singleton_after",reuse.singleton_enabled,BASE,{}),
        ("singleton_early",reuse.singleton_enabled,"set_first",{}),
        ("singleton_no_query",reuse.singleton_enabled,"never",{}),
        ("opening_gate",opening.enabled,BASE,opening.Gate(saved_gate)),
        ("neural_final",neural.enabled,BASE,neural.Actor(actors)),
    )
    totals,paths=Counter(),{}
    for key,item,later,labels,roles,menus in cases(pack,offset):
        order,variant,opening_id=key
        first=router.sp.opened(item[0][3],item[0][2])
        for arm,context,script,trained in variants:
            events=[]
            with context():
                result=router.play(item,script,trained,events=events,recorded=later)
            claims=[]
            disclosures=[(r,0,first[2*r]) for r in range(2) if first[2*r]]
            for event in events:
                q=event["query"]
                if q and q.get("cached"):
                    assert all(role==q["respondent"] and not bits&~q["target"]
                               for role,_,bits in event["disclosed"])
                disclosures.extend(event["disclosed"])
            for role,negative,bits in disclosures:
                names=[p for i,p in enumerate(labels) if bits&(1<<i)]
                claim={"id":f"m{len(claims)+1}","role":roles[role],
                       "accepts":[] if negative else names,"excludes":names if negative else []}
                assert study.truthful_disclosure(claim,menus[role])
                claims.append(claim)
            verdict=study.readout(labels,roles,claims)
            expected="AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
            assert result[0]==(verdict["state"]==expected)
            prefix=order,variant,arm
            for name,val in zip(("solved","slots","checks","queries","answers","scope"),result,strict=True):
                totals[*prefix,name]+=val
            totals[*prefix,"cached_replies"]+=sum(bool(t["query"] and t["query"].get("cached")) for t in events)
            paths["/".join((*prefix,opening_id))]={"events":events,"claims":claims,"verdict":verdict}
    return {"totals":router.sp.flatten(totals),"paths":paths}


def evaluate(actor_file,gate_file):
    load=study.mali.load
    actors=[np.asarray(w) for w in load(actor_file)["parameters"]["last"]]
    gate=load(gate_file)["rules"]
    factored,pooled=load(FACTORED),load(PROFILE)
    assert all(factored["package"][r][p]["admitted"]==v["admitted"]
               for r,signs in pooled["package"].items() for p,v in signs.items())
    assert all(factored["scope"][r]["winner"]==v["stable_fields"]["scope"] for r,v in pooled["readings"].items())
    outputs={name:replay(data,actors,gate,0) for name,data in
             (("complete",factored),("stable_only",load(STABLE)),("raw_package",load(RAW)))}
    rotated={i:replay(factored,actors,gate,i)["totals"] for i in range(7)}
    return {"scope":"Frozen policies and archived model receipts. Complete pooled and separately read fields support identical admitted signs. Rotations preserve roles and package dispositions.",
            "inputs":{str(p.relative_to(study.HERE.parents[1])):opening.reference.digest(p)
                      for p in (FACTORED,PROFILE,STABLE,RAW,actor_file.resolve(),gate_file.resolve())},
            "conditions":outputs,"rotations":rotated}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("actor",type=Path)
    p.add_argument("gate",type=Path)
    args=p.parse_args()
    print(json.dumps(evaluate(args.actor,args.gate),indent=2))
