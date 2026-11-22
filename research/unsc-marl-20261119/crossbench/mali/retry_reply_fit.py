"""Fit a shared sender policy from paired retransmit/continue team returns."""
import argparse
from collections import Counter
from itertools import combinations, product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import canonical_menu as canonical
import retry_reply as reply
import semantic_order_fit as synth
import trajectory_fit as objective

HERE=Path(__file__).resolve().parent
study,router,sp=canonical.study,canonical.router,canonical.router.sp
SEEDS={"train":415919,"dev":712201,"test":616991,"families":378211}
FEATURES=("would_complete","missing_acceptance","missing_exclusion","missing_target",
          "at_most_three_active","at_least_two_slots","multiple_missing",
          "cached_reply","joint_receipt")
BASE="decisive"


class Capture:
    def __init__(self,retry):
        self.retry=retry
        self.observation=None

    def __call__(self,obs):
        assert self.observation is None
        self.observation=obs
        return self.retry


def branch(item,terms,retry,later=None):
    capture=Capture(retry)
    events=[]
    with canonical.enabled(terms,"public",lambda:reply.enabled(capture)):
        result=router.play(item,canonical.BASE,{},events=events,recorded=later)
    queries=[e["query"] for e in events if e["query"] is not None]
    assert len(queries)<=1
    for e in events:
        if e["query"] and e["query"].get("retried"):
            assert all(r==e["query"]["respondent"] for r,_,_ in e["disclosed"])
    return capture.observation,(*result,sum(e.get("retried",False) for e in queries),
                               sum(e.get("retry_disclosures",0) for e in queries))


def paired(rows):
    data=[]
    for item,fields,later in rows:
        obs,continue_=branch(item,fields,False,later)
        if obs is None:
            retransmit=continue_
        else:
            check,retransmit=branch(item,fields,True,later)
            assert check==obs and continue_[2]>=0 and retransmit[-2]==1
        left,right=item[0][1]
        data.append(("agreement" if left&right else "impasse",obs,continue_,retransmit))
    return data


def take(obs,mode,rules):
    if obs is None:
        return False
    if mode=="never":
        return False
    if mode=="always":
        return True
    for decision,predicate in reversed(rules):
        if all(obs[i]==v for i,v in predicate):
            return decision
    return obs[0]


def score(data,mode,rules=()):
    totals,pairs=Counter(),Counter()
    for label,obs,late,early in data:
        chosen=take(obs,mode,rules)
        result=early if chosen else late
        before=early if take(obs,BASE,()) else late
        totals[label,"presentations"]+=1
        totals[label,"opportunities"]+=obs is not None
        for field,val in zip(("solved","slots","checks","queries","answers","scope","retries","retry_signs"),
                             result,strict=True):
            totals[label,field]+=val
        pairs[label,str(before[0]),str(result[0])]+=1
    return totals,pairs


def fit(training,dev):
    atoms=list(product(range(len(FEATURES)),(False,True)))
    predicates=[(),*((a,) for a in atoms),*((a,b) for a,b in combinations(atoms,2) if a[0]!=b[0])]
    candidates=list(product((False,True),predicates))
    rules=()
    baseline=[[score(p,BASE)[0] for p in sets] for sets in (training,dev)]
    value=lambda counts:sum(map(objective.quality,counts))
    current=tuple(map(value,baseline))
    journal=[]
    for _ in range(4):
        trials,best=[],None
        for patch in candidates:
            decision=(*rules,patch)
            counts=[score(panel,BASE,decision)[0] for panel in training]
            change=value(counts)-current[0]
            note={"rule":patch,"train_gain":change}
            if change>0 and synth.protects(baseline[0],counts):
                held=[score(p,BASE,decision)[0] for p in dev]
                delta=value(held)-current[1]
                passed=delta>=0 and synth.protects(baseline[1],held)
                note.update(dev_gain=delta,passed=passed)
                rank=change,delta,-len(patch[1])
                if passed and (best is None or rank>best[0]):
                    best=rank,decision,counts,held
            trials.append(note)
        journal.append({"trials":trials})
        if best is None:
            break
        _,rules,counts,held=best
        current=value(counts),value(held)
        journal[-1].update(accepted=rules[-1],train=list(map(sp.flatten,counts)),dev=list(map(sp.flatten,held)))
    return rules,journal


def cabinet(widths,n,missing,seed):
    return {name:paired((item,fields,None) for item,fields in group)
            for name,group in synth.panels(widths,n,missing,seed).items()}


def compare(data,rules):
    arms={}
    for name,rule in (("never",()),("decisive",()),("always",()),("learned",rules)):
        counts,pairs=score(data,name,rule)
        arms[name]={"counts":sp.flatten(counts),"pairs_vs_decisive":sp.flatten(pairs)}
    return arms


def transfer(metrics,rules):
    rows={"mali":list(canonical.mali(metrics,0)),"myanmar":list(canonical.myanmar(0))}
    output={}
    for family,cases in rows.items():
        output[family]={}
        clean=[(item,terms,later) for _,item,later,_,_,_,terms in cases]
        originals=[item[0] for item,_,_ in clean]
        output[family]["clean"]=compare(paired(clean),rules)
        bouts=[]
        for replica in range(12):
            injected=router.guard.messages(originals,SEEDS["families"]+replica,.22,.09)
            bouts.extend((item,terms,later) for item,(_,terms,later) in zip(injected,clean,strict=True))
        output[family]["noisy_delivery"]=compare(paired(bouts),rules)
    return output


def evaluate(metrics):
    train=cabinet((5,6),650,2,SEEDS["train"])
    development=cabinet((6,),450,3,SEEDS["dev"])
    heldout=cabinet((7,8),500,3,SEEDS["test"])
    rules,journal=fit(tuple(train.values()),tuple(development.values()))
    return {"protocol":{"seeds":SEEDS,"features":FEATURES,
                        "scope":"One extra public slot for acknowledged missing signatures from a verified reply. Team-return training uses paired simulated episode outcomes only."},
            "rules":rules,"journal":journal,"heldout":{k:compare(p,rules) for k,p in heldout.items()},
            "archive":transfer(metrics,rules)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    root=HERE.parents[1]
    hashes=study.hashes()
    for path in (Path(__file__),Path(reply.__file__),Path(canonical.__file__),Path(synth.__file__),
                 Path(objective.__file__),Path(reply.reuse.__file__),Path(reply.reuse.defer.__file__),
                 Path(reply.reuse.singleton_control.__file__),canonical.transfer.FACTORED,args.metrics):
        hashes[str(path.resolve().relative_to(root))]=objective.digest(path)
    launch=args.directory/"launch.json"
    result=args.directory/"results.json"
    metrics=study.mali.load(args.metrics)
    if args.mode=="replay":
        assert study.mali.load(launch)["sha256"]==hashes
        assert json.loads(json.dumps(evaluate(metrics)))==study.mali.load(result)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    meta={"host":socket.gethostname(),"pid":os.getpid(),"gpu_uuids":[],"device":"CPU",
          "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
          "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(meta,indent=2)+"\n")
    data=evaluate(metrics)
    result.write_text(json.dumps(data,indent=2)+"\n")
    print({"rules":len(data["rules"])},flush=True)


if __name__=="__main__":
    main()
