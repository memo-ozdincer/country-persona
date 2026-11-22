"""Run the same signed actions in an order derived from public package descriptions."""
import argparse
from collections import Counter
from contextlib import ExitStack
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import cache_transfer as transfer
import reuse_receipt as reuse

study,router=transfer.study,transfer.router
BASE=transfer.BASE
HERE=Path(__file__).resolve().parent
MASK_FIELDS=("target","scope","published","request_set","qualified_acceptance","qualified_exclusions")


def descriptions(case,labels):
    by_id={opt["id"]:tuple(sorted((k,json.dumps(v)) for k,v in opt.items() if k!="id"))
           for opt in case["options"]}
    rows=tuple(by_id[k] for k in labels)
    if len(set(rows))!=len(rows):
        raise ValueError("Duplicate public packages must share one canonical proposal")
    return rows


def distance(a,b):
    return sum(left!=right for left,right in zip(a,b,strict=True))


def order_of(public,actor,features,mode):
    if mode=="public":
        return sorted(range(len(features)),key=features.__getitem__)
    # A disclosed offer is public evidence about a peer, even if another
    # delegate already removed that offer from the common frontier.
    peer=public[2*(1-actor)]
    mine=public[2*actor]
    anchors=(peer,mine) if mode=="peer_near" else (mine,peer)

    def key(i):
        return (*[min((distance(features[i],f) for j,f in enumerate(features) if mask&(1<<j)),default=0)
                  for mask in anchors],features[i])
    return sorted(range(len(features)),key=key)


@lru_cache(maxsize=4096)
def encoder(order):
    positions=[0]*len(order)
    for j,i in enumerate(order):
        positions[i]=j

    def recode(mask):
        return sum(1<<j for i,j in enumerate(positions) if mask&(1<<i))

    def decode(mask):
        return sum(1<<i for j,i in enumerate(order) if mask&(1<<j))

    return recode,decode


def enabled(features,mode,context=reuse.singleton_enabled):
    if mode=="index":
        return context()
    stack=ExitStack()
    stack.enter_context(context())
    base_available,base_transition=router.available,router.transition

    def available(item,state):
        row,tape=item
        public,actor,slot,credit=state
        chosen=mode(public,actor,row[2][actor],slot,credit,features) if callable(mode) else mode
        pack,unpack=encoder(tuple(order_of(public,actor,features,chosen)))
        width,truth,local,first,scope=row
        transformed=(width,tuple(map(pack,truth)),
                     tuple(tuple(map(pack,sign)) for sign in local),
                     tuple(map(pack,first)),tuple(map(pack,scope)))
        frame=(transformed,{k:tuple(map(pack,v)) for k,v in tape.items()})
        status=tuple(map(pack,public)),actor,slot,credit
        obs,moves,normal=base_available(frame,status)
        return obs,moves,(frame,status,normal,pack,unpack)

    def transition(item,state,move,actions,context,recorded=None):
        frame,status,normal,pack,unpack=context
        answers=None if recorded is None else [{pack(k):v for k,v in p.items()} for p in recorded]
        after,checked,event=base_transition(frame,status,move,actions,normal,answers)
        if event is not None:
            event={k:unpack(v) if k in MASK_FIELDS else v for k,v in event.items()}
        return (tuple(map(unpack,after[0])),*after[1:]),checked,event

    stack.enter_context(patch.object(router,"available",new=available))
    stack.enter_context(patch.object(router,"transition",new=transition))
    return stack


def evaluate_case(items,mode,script="set_after_opening"):
    totals,paths=Counter(),{}
    for key,item,later,labels,roles,menus,features in items:
        events=[]
        with enabled(features,mode):
            result=router.play(item,script,{},events=events,recorded=later)
        material=[]
        first=router.sp.opened(item[0][3],item[0][2])
        disclosures=[(r,0,first[2*r]) for r in range(2) if first[2*r]]
        for event in events:
            q=event["query"]
            if q and q.get("cached"):
                assert all(r==q["respondent"] and not bits&~q["target"]
                           for r,_,bits in event["disclosed"])
            disclosures.extend(event["disclosed"])
        for role,negative,mask in disclosures:
            names=sorted(p for i,p in enumerate(labels) if mask&(1<<i))
            claim={"id":f"m{len(material)+1}","role":roles[role],
                   "accepts":[] if negative else names,"excludes":names if negative else []}
            assert study.truthful_disclosure(claim,menus[role])
            material.append(claim)
        proof=study.readout(tuple(sorted(labels)),roles,material)
        expected="AGREEMENT_POSSIBLE" if key[1].endswith("overlap") else "IMPASSE"
        assert result[0]==(proof["state"]==expected)
        paths["/".join(key)]={"cost":result,"proof":proof,"claims":material}
        for name,value in zip(("solved","slots","checks","questions","answers","scope"),result,strict=True):
            totals[key[0],key[1],name]+=value
    return {"totals":router.sp.flatten(totals),"paths":paths}


def myanmar(offset):
    spec=study.mali.load(transfer.MYANMAR/"case.json")
    pack=study.mali.load(transfer.FACTORED)
    for row in transfer.cases(pack,offset):
        yield (*row,descriptions(spec,row[3]))


def mali(metrics,offset):
    import local_capacity as local

    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    labels=tuple(o["id"] for o in case["options"])
    remapping=tuple(range(offset,len(labels)))+tuple(range(offset))
    encoded,decode=encoder(remapping)
    assert all(decode(encoded(1<<i))==1<<i for i in range(len(labels)))
    rotated=tuple(labels[i] for i in remapping)
    features=descriptions(case,rotated)
    for key,item,proof in local.episodes(metrics,("pooled",)):
        _,order,variant,opening=key
        row,tape=item
        width,truth,known,start,scope=row
        roles=case["roles"] if order=="original" else case["roles"][::-1]
        cards=(variant,"russia") if order=="original" else ("russia",variant)
        mapped=(width,tuple(map(encoded,truth)),tuple(tuple(map(encoded,s)) for s in known),
                tuple(map(encoded,start)),tuple(map(encoded,scope)))
        later=[{encoded(k):v for k,v in a.items()} for a in proof]
        yield (order,variant,opening),(mapped,tape),later,rotated,roles,tuple(menus[r] for r in cards),features


def evaluate(metrics):
    families={"myanmar":myanmar,"mali":lambda i:mali(metrics,i)}
    output={}
    for family,rows in families.items():
        output[family]={}
        for arm,script in product(("index","public","peer_near","own_near"),(BASE,"set_first")):
            reference=evaluate_case(rows(0),arm,script)
            totals={}
            for offset in range(7):
                rotated=evaluate_case(rows(offset),arm,script)
                totals[offset]=rotated["totals"]
                if arm!="index":
                    assert rotated==reference
            output[family][f"{arm}/{script}"]={"rotations":totals,"reference":reference}
    return output


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mali_receipts",type=Path)
    args=p.parse_args()
    out=evaluate(study.mali.load(args.mali_receipts))
    print(json.dumps({"input_sha256":{str(p.name):sha256(p.read_bytes()).hexdigest()
                                     for p in (args.mali_receipts,transfer.FACTORED)},
                      "cases":out},indent=2))
