"""Learn when an early request beats the same policy with a delayed opening."""
import argparse
from collections import Counter
from contextlib import ExitStack
from itertools import combinations, product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import reuse_receipt as reuse
import trajectory_fit as reference

HERE=Path(__file__).resolve().parent
study,group,policy=reference.study,reference.group,reference.policy
sp=group.SP
FEATURES=("peer_offer_visible","own_offer_visible","peer_offer_known_reject","peer_offer_unknown",
          "already_offered_candidate","three_candidates","verifiable_scope_turn","bundle_turn",
          "two_unjudged_active_packages","three_unjudged_active_packages","three_known_exclusions")
SEEDS={"train":410827,"validation":700171,"heldout":914417}


def local_features(item,state,moves,ordinary):
    public,actor,_,_=state
    width,_,known,_,_=item[0]
    peer_offer=public[2*(1-actor)]
    mine=public[2*actor]
    yes,no=known[actor]
    unseen=((1<<width)-1)&~(yes|no|public[1]|public[3])
    targets=moves[group.OFFER_SET]
    action=ordinary[0]
    bits=(peer_offer,mine,peer_offer&no,peer_offer&unseen,mine&targets,targets.bit_count()==3,
          action==policy.routing.offers.CHECK,action==policy.routing.BUNDLE,
          unseen.bit_count()>=2,unseen.bit_count()>=3,no.bit_count()>=3)
    return tuple(map(bool,bits))


def enabled():
    stack=ExitStack()
    stack.enter_context(reuse.singleton_enabled())
    base_available,base_default=policy.available,policy.default

    def available(item,state):
        obs,moves,ordinary=base_available(item,state)
        view=None
        if state[2]==0 and group.OFFER_SET in moves:
            view=local_features(item,state,moves,ordinary)
        return (*obs,view),moves,ordinary

    stack.enter_context(patch.object(policy,"available",new=available))
    stack.enter_context(patch.object(policy,"default",new=lambda obs,mode:base_default(obs[:-1],mode)))
    return stack


class Gate:
    def __init__(self,conditions):
        self.conditions=conditions
        self.early=0

    def get(self,obs,default=None):
        view=obs[-1]
        if view is not None and matches(view,self.conditions):
            self.early+=1
            return group.OFFER_SET
        return default


def matches(view,rules):
    return any(all(view[i]==value for i,value in rule) for rule in rules)


def paired(items):
    samples=[]
    for item in items:
        width,truth,local,opening,_=item[0]
        state=sp.opened(opening,local),1,0,7
        obs,_,_=policy.available(item,state)
        a=policy.play(item,group.BASE,{})
        b=policy.play(item,"set_first",{}) if obs[-1] is not None else a
        kind="agreement" if truth[0]&truth[1] else "impasse"
        samples.append((obs[-1],kind,a,b))
    return samples


def totals(samples,rules):
    score=Counter()
    for view,label,late,early in samples:
        take=view is not None and matches(view,rules)
        selected=early if take else late
        score[label,"presentations"]+=1
        score[label,"eligible"]+=view is not None
        score[label,"asked_early"]+=take
        for k,v in zip(("solved","slots","checks","requests","replies","scope"),selected,strict=True):
            score[label,k]+=v
        score[label,"gained"]+=selected[0]>late[0]
        score[label,"lost"]+=selected[0]<late[0]
    return score


def reward(counts):
    return sum(map(reference.quality,counts))


def fit(train,dev):
    atoms=list(product(range(len(FEATURES)),(False,True)))
    candidates=[(),*((a,) for a in atoms),
                *((a,b) for a,b in combinations(atoms,2) if a[0]!=b[0])]
    rules=()
    anchors=[[totals(rows,rules) for rows in split] for split in (train,dev)]
    training,validation=map(reward,anchors)
    log=[]
    for _ in range(3):
        best=None
        tested=Counter()
        for q in candidates:
            if q in rules:
                continue
            proposal=(*rules,q)
            fit_counts=[totals(rows,proposal) for rows in train]
            score=reward(fit_counts)
            if score<=training or not protected(anchors[0],fit_counts):
                continue
            tested["passes_training"]+=1
            dev_counts=[totals(rows,proposal) for rows in dev]
            val=reward(dev_counts)
            if val<validation or not protected(anchors[1],dev_counts):
                continue
            tested["passes_validation"]+=1
            rank=(score,val,-len(q))
            if best is None or rank>best[0]:
                best=rank,proposal,fit_counts,dev_counts
        log.append({"candidate_counts":dict(tested)})
        if best is None:
            break
        (training,validation,_),rules,fit_counts,dev_counts=best
        log[-1].update(accepted=rules[-1],training=[sp.flatten(v) for v in fit_counts],
                       validation=[sp.flatten(v) for v in dev_counts])
    return rules,log


def protected(anchor,new):
    return all(b[k,"solved"]>=a[k,"solved"]
               for a,b in zip(anchor,new,strict=True) for k in ("agreement","impasse"))


def evaluate(metrics):
    world=[reference.panels(widths,SEEDS[label],count,missing)
           for label,widths,count,missing in (("train",(4,5,6),550,2),
                                              ("validation",(6,),400,3),("heldout",(7,8),450,3))]
    with enabled():
        train,dev,test=[{tag:paired(rows) for tag,rows in each.items()} for each in world]
        rules,log=fit(tuple(train.values()),tuple(dev.values()))
        held={}
        for tag,items in test.items():
            held[tag]={arm:sp.flatten(totals(items,plan))
                       for arm,plan in (("fixed_after",()),("fixed_early",((),)),("learned",rules))}
            meter=Gate(rules)
            actual=policy.measure(world[-1][tag],group.BASE,meter)[1]
            assert all(actual[k,r]==held[tag]["learned"][k+"/"+r] for k in ("agreement","impasse")
                       for r in ("solved","slots","checks"))
            assert meter.early==sum(held[tag]["learned"][k+"/asked_early"] for k in ("agreement","impasse"))
    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    replay={}
    with patch.object(study.reply,"enabled",new=enabled):
        for tag in ("pooled","authored"):
            evidence=metrics["conditions"][tag]
            gate=Gate(rules)
            replay[tag]={**study.certify(case,menus,evidence["package"],evidence["scope"],gate),
                         "early_requests":gate.early}
    return {"seeds":SEEDS,"features":FEATURES,"rules":rules,"fit":log,"heldout":held,"transfer":replay,
            "scope":"Only the opening action is learned from paired team returns. All subsequent agents use the same fixed continuation."}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    root=HERE.parents[1]
    hashes=study.hashes()
    files=(Path(__file__),Path(reuse.__file__),Path(reference.__file__),Path(reference.defer.__file__),
           Path(reuse.singleton_control.__file__),args.metrics)
    hashes.update({str(f.resolve().relative_to(root)):reference.digest(f) for f in files})
    launch=args.directory/"launch.json"
    result=args.directory/"results.json"
    metrics=study.mali.load(args.metrics)
    if args.mode=="replay":
        assert study.mali.load(launch)["sha256"]==hashes
        assert json.loads(json.dumps(evaluate(metrics)))==study.mali.load(result)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    meta={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
          "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
          "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(meta,indent=2)+"\n")
    data=evaluate(metrics)
    result.write_text(json.dumps(data,indent=2)+"\n")
    print({"rules":len(data["rules"])},flush=True)


if __name__=="__main__":
    main()
