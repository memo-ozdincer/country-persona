"""Learn when to resend now, yield one ordinary slot, or continue."""
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
import delayed_reply as delay
import reply_channel as transport

HERE=Path(__file__).resolve().parent
base=transport.base
router,sp=delay.router,delay.sp
ACTIONS=("immediate","delayed","continue")
FEATURES=(*base.FEATURES,"at_least_three_slots","previous_signed_packet",
          "previous_packet_missing","same_signature_recently_missing")
SEEDS={"train":561093,"dev":200033,"test":635599,"case_faults":118423}


def rollout(item,terms,choose,recorded):
    events=[]
    with canonical.enabled(terms,"public",lambda:delay.enabled(choose)):
        result=router.play(item,canonical.BASE,{},events=events,recorded=recorded)
    replies=[e["query"] for e in events if e["query"]]
    assert len(replies)<=1
    retry=next((o for o in replies if o.get("retry_opportunity")),None)
    attempt=int(retry is not None and "retry_slot" in retry)
    handoff=int(retry is not None and "handoff_slot" in retry)
    if attempt:
        assert retry["retry_slot"]==retry["slot"]+2+handoff
    return (*result,attempt,(retry or {}).get("retry_signs",0),handoff)


def paired(rows):
    paired=[]
    for item,terms,recorded in rows:
        view=[]

        def choose(obs):
            assert not view
            view.append(obs)
            return "continue"

        none=rollout(item,terms,choose,recorded)
        obs=view[0] if view else None
        if obs is None:
            outcomes=(none,none,none)
        else:
            always=rollout(item,terms,lambda _:"immediate",recorded)
            late=rollout(item,terms,lambda _:"delayed",recorded) if obs[5] else always
            outcomes=always,late,none
        l,r=item[0][1]
        label="agreement" if l&r else "impasse"
        paired.append((label,obs,outcomes))
    return paired


def pick(view,mode,rules):
    if view is None:
        return 0
    if mode=="decisive_now":
        return 0 if view[0] else 2
    if mode in ACTIONS:
        return 0 if mode=="delayed" and not view[5] else ACTIONS.index(mode)
    for a,predicate in reversed(rules):
        if all(view[i]==v for i,v in predicate):
            return 0 if a==1 and not view[5] else a
    return 0


def score(data,arm,rules=()):
    metrics,pairs=Counter(),Counter()
    for label,obs,ends in data:
        action=pick(obs,arm,rules)
        selected=ends[action]
        for key,val in zip(("solved","slots","checks","queries","answers","scope","retries","retry_signs","handoffs"),
                           selected,strict=True):
            metrics[label,key]+=val
        metrics[label,"presentations"]+=1
        metrics[label,"opportunities"]+=obs is not None
        if obs is not None:
            metrics[label,ACTIONS[action]]+=1
        pairs[label,str(ends[0][0]),str(selected[0])]+=1
    return metrics,pairs


def fit(training,dev):
    atoms=list(product(range(len(FEATURES)),(False,True)))
    predicates=[(),*((a,) for a in atoms),*((a,b) for a,b in combinations(atoms,2) if a[0]!=b[0])]
    candidates=list(product(range(len(ACTIONS)),predicates))
    # Scenarios without a retry decision contribute identical totals to every
    # candidate. Filtering them here cannot change a difference or guard.
    splits=tuple([[r for r in panel if r[1] is not None] for panel in sets] for sets in (training,dev))
    anchors=tuple([score(rows,"immediate")[0] for rows in sets] for sets in splits)
    value=lambda metric:sum(map(base.objective.quality,metric))
    starting=tuple(map(value,anchors))
    rules=()
    journal=[]
    for _ in range(4):
        best=None
        turns=Counter()
        for rule in candidates:
            proposal=(*rules,rule)
            before=[score(rows,"learned",proposal)[0] for rows in splits[0]]
            train=value(before)
            if train<=starting[0] or not base.synth.protects(anchors[0],before):
                continue
            turns["train"]+=1
            held=[score(rows,"learned",proposal)[0] for rows in splits[1]]
            val=value(held)
            if val<starting[1] or not base.synth.protects(anchors[1],held):
                continue
            turns["dev"]+=1
            rank=train,val,-len(rule[1])
            if best is None or rank>best[0]:
                best=rank,proposal,before,held
        journal.append({"rules_passing":turns})
        if best is None:
            break
        (train,val,_),rules,before,held=best
        starting=train,val
        journal[-1].update(accepted=rules[-1],train=list(map(sp.flatten,before)),dev=list(map(sp.flatten,held)))
    return rules,journal


def panels(widths,n,missing,seed):
    rows,terms=zip(*base.synth.worlds(widths,n,missing,seed),strict=True)
    pruned=router.routing.refit.drop_returns(rows,seed+1)
    return {mode:paired((item,fields,None) for item,fields in
                        zip(transport.delivery(pruned,seed+2,p),terms,strict=True))
            for mode,p in (("independent",0),("persistent",transport.PERSISTENCE))}


def measure(data,rules):
    output={}
    for arm in (*ACTIONS,"decisive_now","learned"):
        totals,pairs=score(data,arm,rules)
        output[arm]={"metrics":sp.flatten(totals),"pairs_vs_immediate":sp.flatten(pairs)}
    return output


def archived(metrics,rules):
    families={"mali":list(canonical.mali(metrics,0)),"myanmar":list(canonical.myanmar(0))}
    output={}
    for name,rows in families.items():
        output[name]={}
        physical=[item[0] for _,item,_,_,_,_,_ in rows]
        clean=paired((item,terms,recorded) for _,item,recorded,_,_,_,terms in rows)
        output[name]["clean"]=measure(clean,rules)
        for mode,p in (("independent",0),("persistent",transport.PERSISTENCE)):
            samples=[]
            for j in range(12):
                noisy=transport.delivery(physical,SEEDS["case_faults"]+j,p)
                samples.extend((item,terms,recorded) for item,(_,_,recorded,_,_,_,terms)
                               in zip(noisy,rows,strict=True))
            output[name][mode]=measure(paired(samples),rules)
    return output


def evaluate(metrics):
    train=panels((5,6),650,2,SEEDS["train"])
    val=panels((6,),550,3,SEEDS["dev"])
    test=panels((7,8),550,3,SEEDS["test"])
    rules,journal=fit(tuple(train.values()),tuple(val.values()))
    return {"protocol":{"seeds":SEEDS,"features":FEATURES,"actions":ACTIONS,
                        "scope":"One verified resend, scheduled immediately or after an ordinary disclosure. The sender's own previous delivery evidence is local. Fitting compares complete synthetic team outcomes."},
            "rules":rules,"journal":journal,"heldout":{k:measure(rows,rules) for k,rows in test.items()},
            "archives":archived(metrics,rules)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    root=HERE.parents[1]
    hashes=base.study.hashes()
    previous=base.study.mali.load(HERE/"evidence/retry-reply/launch.json")["sha256"]
    assert all(base.objective.digest(root/k)==v for k,v in previous.items())
    hashes.update(previous)
    for path in (Path(__file__),Path(delay.__file__),Path(transport.__file__),args.metrics):
        hashes[str(path.resolve().relative_to(root))]=base.objective.digest(path)
    launch=args.directory/"launch.json"
    result=args.directory/"results.json"
    metrics=base.study.mali.load(args.metrics)
    if args.mode=="replay":
        assert base.study.mali.load(launch)["sha256"]==hashes
        assert json.loads(json.dumps(evaluate(metrics)))==base.study.mali.load(result)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    record={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
            "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
            "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(record,indent=2)+"\n")
    outcome=evaluate(metrics)
    result.write_text(json.dumps(outcome,indent=2)+"\n")
    print({"rules":len(outcome["rules"])},flush=True)


if __name__=="__main__":
    main()
