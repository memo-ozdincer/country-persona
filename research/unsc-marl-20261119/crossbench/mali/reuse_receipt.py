"""Reuse the role-local result of a joint check in a later requested reply."""
import argparse
from collections import Counter
from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import defer_scope as defer
import local_capacity
import singleton_control

study,group,policy=defer.study,defer.group,defer.policy
ROUTER=policy.policy
CACHE=8


def transition(item,state,move,actions,ordinary,recorded=None):
    row,tape=item
    public,actor,slot,credit=state
    peer=1-actor
    target=0
    if credit&(CACHE<<peer):
        if move in (ROUTER.MATCH,ROUTER.HOLE):
            target=actions[move]
        elif move==group.OFFER_SET:
            target=group.select(actions[move],*row[2][peer],public[2*actor])
    if target and not target&(row[2][peer][0]|row[2][peer][1]):
        sign=(recorded[peer].get(target) if recorded is not None else
              bool(row[1][peer]&target) if row[-1][peer] else None)
        if sign is not None:
            observed=list(row[2])
            yes,no=observed[peer]
            observed[peer]=(yes|target,no) if sign else (yes,no|target)
            augmented=(*row[:2],tuple(observed),*row[3:])
            after,checked,event=group.FOCUS.answer((augmented,tape),state,ROUTER.MATCH,
                                                    {ROUTER.MATCH:target},ordinary,recorded)
            assert not checked and event["respondent"]==peer
            event={**event,"cached":True}
            if move==group.OFFER_SET:
                event["request_set"]=actions[move]
            return after,False,event

    after,checked,event=defer.step(item,state,move,actions,ordinary,recorded)
    if checked and move==ROUTER.ROUTINE and ordinary[0]==defer.OFFERS.CHECK:
        # The fact that a check happened is public. Receipt availability and
        # its package evidence are only tested inside the respondent's reply.
        assert not after[3]&(1<<actor)
        after=(*after[:3],after[3]|(CACHE<<actor))
    return after,checked,event


def enabled():
    stack=ExitStack()
    stack.enter_context(defer.enabled())
    stack.enter_context(patch.object(policy,"transition",new=transition))
    return stack


def singleton_enabled():
    def available(item,state):
        if state[3]&(CACHE<<(1-state[1])):
            return singleton_control.allow_singleton(item,state)
        return singleton_control.MULTIPLE_ONLY(item,state)

    stack=ExitStack()
    stack.enter_context(patch.object(group,"optional_set",new=available))
    stack.enter_context(enabled())
    return stack


class AskAfterCheck:
    def get(self,obs,default=None):
        if default==ROUTER.ROUTINE and ROUTER.MATCH in obs[0] and not obs[5]:
            return ROUTER.MATCH
        return default


def compare(metrics, singleton=False):
    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    scores={}
    variants=(("discarded",defer.enabled),("reused",enabled))
    if singleton:
        variants=(*variants,("reused_singleton",singleton_enabled))
    for name,context in variants:
        scores[name]={}
        with patch.object(study.reply,"enabled",new=context):
            for cond in ("pooled","authored"):
                receipt=metrics["conditions"][cond]
                scores[name][cond]=study.certify(case,menus,receipt["package"],receipt["scope"],AskAfterCheck())
    limits={}
    for name,context in variants:
        with context():
            cases={key:(item,later) for key,item,later in local_capacity.episodes(metrics,("pooled",))}
            result={}
            # Disable DEFER in both arms to measure whether a coordinated
            # deferral sequence is still necessary.
            available=policy.available

            def without_deferral(item,state):
                obs,moves,normal=available(item,state)
                moves.pop(defer.DEFER,None)
                return (tuple(moves),*obs[1:]),moves,normal

            with patch.object(policy,"available",new=without_deferral):
                for key,(item,later) in cases.items():
                    result["/".join(key)]=len(local_capacity.routes(item,later))
            limits[name]=result
    return {"scope":"Matched replay with one acquisition of the same compound role receipt. The cache enables only a requested, signed target and changes no public action cost. No refit or model calls.",
            "schedules":scores,"local_route_counts_without_deferral":limits}


def synthetic():
    import trajectory_fit as lanes

    heldout=lanes.panels((6,7),lanes.TEST,350,3)
    output={}
    for condition,rows in heldout.items():
        runs={}
        for name,context in (("discarded",defer.enabled),("reused",enabled),
                             ("reused_singleton",singleton_enabled)):
            with context():
                runs[name]={script:policy.measure(rows,script,{})
                            for script in (group.BASE,"set_first","never")}
        report={}
        for name,arms in runs.items():
            report[name]={}
            for script,(paths,counts) in arms.items():
                pairs=Counter()
                for item,before,after in zip(rows,runs["discarded"][script][0],paths,strict=True):
                    left,right=item[0][1]
                    outcome="agreement" if left&right else "impasse"
                    pairs[outcome,str(before[0]),str(after[0])]+=1
                report[name][script]={"metrics":policy.sp.flatten(counts),"pairs":policy.sp.flatten(pairs)}
        output[condition]=report
    return {"scope":"The held-out six/seven-option panels from trajectory_fit. Fixed policies use the same reward and signed-action rules. Reduced verification availability is shared across variants.",
            "seed":lanes.TEST,"heldout":output}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path,nargs="?")
    p.add_argument("--singleton",action="store_true")
    p.add_argument("--synthetic",action="store_true")
    args=p.parse_args()
    if args.synthetic:
        result=synthetic()
    else:
        result=compare(study.mali.load(args.metrics),args.singleton)
        result["input_sha256"]=sha256(args.metrics.read_bytes()).hexdigest()
    print(json.dumps(result,indent=2))
