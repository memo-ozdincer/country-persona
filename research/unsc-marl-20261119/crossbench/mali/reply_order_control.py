"""Swap resend and ordinary disclosure while keeping the two actions available."""
import argparse
from collections import Counter
from contextlib import ExitStack
import json
from pathlib import Path
from unittest.mock import patch

import delayed_reply_fit as fit

router,sp=fit.router,fit.sp
delay=fit.delay
reuse=delay.reuse


def resend_then_disclose():
    stack=ExitStack()
    stack.enter_context(delay.enabled(lambda _: "immediate"))
    opening=router.transition
    available=router.available

    def step(item,state,action,options,ordinary,recorded=None):
        after,checked,event=opening(item,state,action,options,ordinary,recorded)
        width=item[0][0]
        if not event or "retry_slot" not in event or after[2]>=width+1:
            return after,checked,event
        if sp.terminal(after[0],(1<<width)-1):
            return after,checked,event
        _,moves,normal=available(item,after)
        move,plan=normal
        spend=(delay.WAIT if move==delay.CHECK else move),plan
        before=after
        after,extra,q=reuse.transition(item,after,reuse.ROUTER.ROUTINE,moves,spend,recorded)
        assert not extra and q is None and after[2:]==(before[2]+1,before[3])
        return after,checked,{**event,"handoff_role":before[1],"handoff_slot":before[2]}

    stack.enter_context(patch.object(router,"transition",new=step))
    return stack


def rollout(item,terms,recorded):
    events=[]
    with fit.canonical.enabled(terms,"public",resend_then_disclose):
        outcome=router.play(item,fit.canonical.BASE,{},events=events,recorded=recorded)
    query=next((t["query"] for t in events if t["query"] is not None),{})
    result=(*outcome,int("retry_slot" in query),query.get("retry_signs",0),int("handoff_slot" in query))
    return result


def compare(rows,rules):
    meters={arm:Counter() for arm in ("immediate","disclose_then_resend","resend_then_disclose","learned")}
    matched=Counter()
    for item,terms,recorded in rows:
        before=fit.rollout(item,terms,lambda _:"immediate",recorded)
        after=fit.rollout(item,terms,lambda _:"delayed",recorded)
        swapped=rollout(item,terms,recorded)
        learned=fit.rollout(item,terms,lambda v:fit.ACTIONS[fit.pick(v,"learned",rules)],recorded)
        l,r=item[0][1]
        case="agreement" if l&r else "impasse"
        for key,result in zip(meters,(before,after,swapped,learned),strict=True):
            for field,val in zip(("solved","slots","checks","questions","answered","scope","retries","signs","handoffs"),
                                 result,strict=True):
                meters[key][case,field]+=val
            meters[key][case,"paths"]+=1
        matched[case,str(swapped[0]),str(after[0])]+=1
    return {"metrics":{arm:sp.flatten(v) for arm,v in meters.items()},
            "paired_resend_first_to_disclose_first":sp.flatten(matched)}


def evaluate(metrics,rules):
    samples,terms=zip(*fit.base.synth.worlds((7,8),550,3,fit.SEEDS["test"]),strict=True)
    tests=router.routing.refit.drop_returns(samples,fit.SEEDS["test"]+1)
    grouped={tag:compare(((row,t,None) for row,t in
                          zip(fit.transport.delivery(tests,fit.SEEDS["test"]+2,p),terms,strict=True)),rules)
             for tag,p in (("independent",0),("persistent",fit.transport.PERSISTENCE))}
    families={"mali":list(fit.canonical.mali(metrics,0)),"myanmar":list(fit.canonical.myanmar(0))}
    archives={}
    for name,rows in families.items():
        physical=[item[0] for _,item,_,_,_,_,_ in rows]
        archives[name]={}
        for tag,p in (("independent",0),("persistent",fit.transport.PERSISTENCE)):
            cases=[]
            for offset in range(12):
                injections=fit.transport.delivery(physical,fit.SEEDS["case_faults"]+offset,p)
                cases.extend((item,t,later) for item,(_,_,later,_,_,_,t) in zip(injections,rows,strict=True))
            archives[name][tag]=compare(cases,rules)
    return {"scope":"Both order arms allow the same two nominal actions where time permits. The state seen by the ordinary speaker can differ, and a completed proof cancels the next action.",
            "heldout":grouped,"archives":archives}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    p.add_argument("fitted",type=Path)
    args=p.parse_args()
    load=fit.base.study.mali.load
    data=evaluate(load(args.metrics),load(args.fitted)["rules"])
    data["inputs"]={f.name:fit.base.objective.digest(f) for f in (args.metrics,args.fitted)}
    print(json.dumps(data,indent=2))
