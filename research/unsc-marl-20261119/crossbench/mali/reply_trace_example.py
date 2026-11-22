"""Find a reproducible archive witness with a delayed, delivered acceptance."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import delayed_reply_fit as fit

router,sp=fit.router,fit.sp


def trace(item,labels,roles,terms,recorded,choose):
    steps=[]
    resent={}
    standard=fit.delay.authorized_retry
    _,decode=fit.canonical.encoder(tuple(sorted(range(len(terms)),key=terms.__getitem__)))

    def capture(item,state,sender,yes,no):
        following,delivered=standard(item,state,sender,yes,no)
        for stance,mask in enumerate(delivered):
            resent[sender,stance]=decode(mask)
        return following,delivered

    with patch.object(fit.delay,"authorized_retry",new=capture),fit.canonical.enabled(
            terms,"public",lambda:fit.delay.enabled(choose)):
        result=router.play(item,fit.canonical.BASE,{},events=steps,recorded=recorded)
    claims=[]

    def labels_of(mask):
        return [k for i,k in enumerate(labels) if mask&(1<<i)]

    first=sp.opened(item[0][3],item[0][2])
    staged=[]
    for owner in range(2):
        if first[2*owner]:
            staged.append((-1,"opening",owner,False,first[2*owner]))
    for turn in steps:
        query=turn["query"]
        for owner,negative,bits in turn["disclosed"]:
            retransmitted=bits&resent.get((owner,negative),0) if query else 0
            if retransmitted:
                staged.append((query["retry_slot"],"resend",owner,negative,retransmitted))
                bits&=~retransmitted
            if not bits:
                continue
            if not query:
                slot,origin=turn["slot"],"ordinary"
            elif owner==query.get("handoff_role"):
                slot,origin=query["handoff_slot"],"intervening disclosure"
            else:
                slot,origin=query["slot"]+1,"reply"
            staged.append((slot,origin,owner,negative,bits))
    for slot,origin,owner,negative,bits in sorted(staged,key=lambda event:event[0]):
        names=labels_of(bits)
        claims.append({"id":f"m{len(claims)+1}","role":roles[owner],"origin":origin,"slot":slot,
                       "accepts":[] if negative else names,"excludes":names if negative else []})
    proof=fit.base.study.readout(labels,roles,claims)
    return {"result":result,"events":steps,"admitted_signs":claims,"proof":proof}


def find(rules):
    rows=list(fit.canonical.myanmar(0))
    physical=[item[0] for _,item,_,_,_,_,_ in rows]
    for offset in range(12):
        seed=fit.SEEDS["case_faults"]+offset
        faults=fit.transport.delivery(physical,seed,fit.transport.PERSISTENCE)
        for (key,_,recorded,labels,roles,menus,terms),item in zip(rows,faults,strict=True):
            if key[1]!="uk-overlap":
                continue
            first=trace(item,labels,roles,terms,recorded,lambda _:"immediate")
            if first["result"][0]:
                continue
            learned=trace(item,labels,roles,terms,recorded,
                          lambda v:fit.ACTIONS[fit.pick(v,"learned",rules)])
            if not learned["result"][0]:
                continue
            query=next(t["query"] for t in learned["events"] if t["query"])
            if not (query.get("retry_action")=="delayed" and query.get("retry_signs",0)
                    and any(c["origin"]=="resend" and c["accepts"] for c in learned["admitted_signs"])):
                continue
            assert any(r["origin"]=="resend" for r in learned["admitted_signs"])
            for arm in (first,learned):
                for c in arm["admitted_signs"]:
                    assert fit.base.study.truthful_disclosure(c,menus[roles.index(c["role"])])
            return {"seed":seed,"opening":key,"package_order":labels,
                    "immediate":first,"learned":learned,
                    "idea_accounting":"A resend counts as another delivery attempt of the same signed proposition. Its first successful receipt can enable a new proof."}
    raise ValueError("No suitable archive witness")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fit",type=Path)
    args=p.parse_args()
    print(json.dumps(find(fit.base.study.mali.load(args.fit)["rules"]),indent=2))
