"""Choose one verification mode per question before seeing either result."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
from unittest.mock import patch
import socket
import subprocess
import sys

import focused_query as focus

HERE=Path(__file__).resolve().parent
policy,sp,routing,guard=focus.policy,focus.sp,focus.routing,focus.guard
MATCH_SCOPE,HOLE_SCOPE=3,4
TRAIN,TEST=903311,514829
BASE="scope_late"


def available(item,current):
    signature,options,normal=policy.choices(item,current)
    role=current[1]
    if current[3]&(1<<(1-role)):
        for source,target in ((policy.MATCH,MATCH_SCOPE),(policy.HOLE,HOLE_SCOPE)):
            if source in options:
                options[target]=options[source]
    # Mode selection uses only the same local/public state used for a direct query.
    return (tuple(options),*signature[1:]),options,normal


def default(key,mode):
    legal=key[0]
    if mode=="never":
        return policy.ROUTINE
    for direct,clause in ((policy.MATCH,MATCH_SCOPE),(policy.HOLE,HOLE_SCOPE)):
        if direct not in legal:
            continue
        if clause in legal and (mode=="scope_first" or (mode==BASE and (key[2] <= 2 or not key[-1]))):
            return clause
        return direct
    return policy.ROUTINE


def transition(item,current,action,options,ordinary,recorded=None):
    if action<MATCH_SCOPE:
        return focus.answer(item,current,action,options,ordinary,recorded)
    row,tape=item
    public,actor,turn,credit=current
    peer=1-actor
    assert credit&(1<<peer)
    target=options[action]
    scope=row[-1][peer]&~(public[1]|public[3])
    yes,no=row[2][peer]
    # No package oracle is called. A scope clause only licenses exclusions.
    supported=list(row[2])
    supported[peer]=yes,no|scope
    updated=(*row[:2],tuple(supported),*row[3:])
    proposal=sp.record(public,peer,scope,False)
    next_move={routing.offers.WAIT:(scope,proposal,actor)}
    after,_=guard.settle(updated,tape,(public,peer,turn+1,credit&~(1<<peer)&~policy.CREDIT),
                         routing.offers.WAIT,next_move,False)
    admitted=after[0][2*peer+1]&~public[2*peer+1]
    signal=(False if scope&target else None)
    return after,True,{"asker":actor,"respondent":peer,"slot":turn,"target":target,
                       "lookup":"scope_only","reply":signal,"admitted":bool(admitted&target),
                       "scope":scope,"published":admitted}


def play(item,mode,weights,start=None,trace=None,events=None,recorded=None):
    row,_=item
    width,truth,local,opening,_=row
    current=start or (sp.opened(opening,local),1,0,7)
    full=(1<<width)-1
    checks=questions=answers=scoped=0
    while current[2]<width+1 and not sp.terminal(current[0],full):
        obs,options,ordinary=available(item,current)
        choice=weights.get(obs,default(obs,mode))
        if trace is not None and len(options)>1:
            trace.append((obs,checks,{a:transition(item,current,a,options,ordinary,recorded)
                                      for a in options if a!=choice}))
        following,checked,reply=transition(item,current,choice,options,ordinary,recorded)
        if events is not None:
            disclosed=[(r,s,following[0][2*r+s]&~current[0][2*r+s])
                       for r in range(2) for s in range(2)
                       if following[0][2*r+s]&~current[0][2*r+s]]
            events.append({"slot":current[2],"query":reply,"disclosed":disclosed})
        checks+=checked
        questions+=reply is not None
        answers+=bool(reply and reply["admitted"])
        scoped+=choice>=MATCH_SCOPE
        current=following
    assert all(not(current[0][2*r]&~v or current[0][2*r+1]&v) for r,v in enumerate(truth))
    return sp.terminal(current[0],full),current[2],checks,questions,answers,scoped


def measure(items,mode,model):
    outcomes,counts=[],Counter()
    for row in items:
        result=play(row,mode,model)
        outcomes.append(result)
        l,r=row[0][1]
        label="agreement" if l&r else "impasse"
        counts[label,"paths"]+=1
        for k,v in zip(("solved","slots","checks","questions","answered","scope_queries"),result,strict=True):
            counts[label,k]+=v
    return outcomes,counts


def fit(cohorts):
    original=[measure(items,BASE,{})[1] for items in cohorts]
    current=sum(map(sp.fitness,original))
    table,changes={},[]
    for _ in range(8):
        delta,hits=defaultdict(float),Counter()
        for items in cohorts:
            for row in items:
                trace=[]
                solved,time,calls,*_=play(row,BASE,table,trace=trace)
                for key,prefix,moves in trace:
                    for action,(world,used,_) in moves.items():
                        outcome,end,rest,*_=play(row,BASE,table,start=world)
                        target=key,action
                        delta[target]+=int(outcome)-int(solved)+sp.COST*(time-end)+sp.CHECK_COST*(calls-prefix-rest-used)
                        hits[target]+=1
        ranked=sorted((-v,key) for key,v in delta.items() if v>0 and hits[key]>=8)
        for _,(key,choice) in ranked:
            proposal={**table,key:choice}
            scores=[measure(items,BASE,proposal)[1] for items in cohorts]
            if any(after[g,"solved"]<before[g,"solved"]
                   for before,after in zip(original,scores,strict=True) for g in ("agreement","impasse")):
                continue
            score=sum(map(sp.fitness,scores))
            if score<=current:
                continue
            current,table=score,proposal
            changes.append({"view":key,"choice":choice,"visits":hits[key,choice],
                            "paired_training":[sp.flatten(x) for x in scores]})
            break
        else:
            break
    return table,{"start":[sp.flatten(x) for x in original],"updates":changes}


def compare(items,learned):
    fitted,stats=measure(items,BASE,learned)
    arms={"learned":sp.flatten(stats)}
    for mode in ("never","focused_first","scope_first",BASE):
        baseline,counts=measure(items,mode,{})
        paired=Counter()
        for item,a,b in zip(items,baseline,fitted,strict=True):
            l,r=item[0][1]
            g="agreement" if l&r else "impasse"
            paired[g,str(a[0]),str(b[0])]+=1
        arms[mode]={"metrics":sp.flatten(counts),"pairs":sp.flatten(paired)}
    return arms


def evaluate():
    rows=sp.panels((4,5),TRAIN,250,2)+sp.panels((4,5),TRAIN+1,250,3)
    cohorts=(guard.messages(rows,TRAIN+2,0,0),
             guard.messages(routing.refit.drop_returns(rows,TRAIN+3),TRAIN+4,.16,.08))
    weights,history=fit(cohorts)
    wider=sp.panels((6,7),TEST,750,3)
    data={"reliable":guard.messages(wider,TEST+1,0,0),
          "faults":guard.messages(routing.refit.drop_returns(wider,TEST+2),TEST+1,.26,.11)}
    with patch.object(policy,"advance",side_effect=focus.answer):
        for sample in data.values():
            for row in sample[:120]:
                assert play(row,"focused_first",{})[:5] == policy.play(row,policy.START,{})
    return {"training":history,"policy":[[k,v] for k,v in sorted(weights.items())],
            "holdout":{name:compare(sample,weights) for name,sample in data.items()}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    a=p.parse_args()
    root=sp.HERE.parents[1]
    prior=json.loads((HERE/"evidence/focused-query/launch.json").read_text())["sha256"]
    hashes={k:sha256((root/k).read_bytes()).hexdigest() for k in prior}
    assert hashes==prior
    hashes[str(Path(__file__).resolve().relative_to(root))]=sha256(Path(__file__).read_bytes()).hexdigest()
    launch,result=a.directory/"launch.json",a.directory/"results.json"
    if a.mode=="replay":
        assert json.loads(launch.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate()))==json.loads(result.read_text())
        print(json.dumps({"hashes":len(hashes),"exact":True}))
        return
    a.directory.mkdir()
    launch.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                  "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                  "run_directory":str(a.directory.resolve()),"command":[sys.executable,*sys.argv],
                                  "sha256":hashes},indent=2)+"\n")
    data=evaluate()
    result.write_text(json.dumps(data,indent=2)+"\n")
    print("accepted",len(data["training"]["updates"]),"updates")


if __name__=="__main__":
    main()
