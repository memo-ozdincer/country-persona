"""Learn when to request a single verified package sign from the other delegate."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import robust_bundle as guard

sp,routing=guard.sp,guard.routing
CREDIT=4
ROUTINE,MATCH,HOLE=range(3)
TRAIN,TEST=543771,921613
START="match_then_hole"


def pick(mask):
    return mask & -mask


def choices(item,current):
    row,_=item
    width,_,evidence,_,_=row
    state,actor,turn,credits=current
    basis,obs,moves=routing.available(row,current,1)
    turn_action=routing.choose(basis,obs,routing.START)
    may_query=credits&CREDIT and turn+2<=width+1 and basis[0][6]!=0
    full=(1<<width)-1
    peer=1-actor
    local_yes,local_no=evidence[actor]
    blocked=state[1]|state[3]
    pending=full&~(blocked|state[2*peer]|state[2*peer+1])
    offered=state[2*actor]&pending
    match=pick(offered) if may_query else 0
    unresolved=full&~blocked
    hole_mask=pending&~(local_yes|local_no)
    hole=pick(hole_mask) if may_query and unresolved.bit_count()<=2 else 0
    options={ROUTINE:None}
    if match:
        options[MATCH]=match
    if hole and hole!=match:
        options[HOLE]=hole
    key=(tuple(options),min(width+1-turn,4),min(unresolved.bit_count(),3),
         min(offered.bit_count(),2),bool(state[2*peer]&unresolved),
         bool(credits&(1<<peer)),basis[0][6],turn<=1)
    return key,options,(turn_action,moves)


def fallback(obs,script):
    legal=obs[0]
    if MATCH in legal and (script in ("match_only",START) or script=="early_match" and obs[-1]):
        return MATCH
    if HOLE in legal and script==START:
        return HOLE
    return ROUTINE


def advance(item,current,pick_action,options,normal):
    row,tape=item
    public,role,step,credit=current
    if pick_action==ROUTINE:
        base,actions=normal
        after,_=guard.settle(row,tape,current,base,actions,False)
        return after,base==routing.offers.CHECK,None
    target=options[pick_action]
    peer=1-role
    yes,no=row[2][peer]
    proof=bool(target&yes) if target&(yes|no) else None
    response=public if proof is None else sp.record(public,peer,target,proof)
    synthetic={routing.offers.WAIT:(target,response,role)}
    after,_=guard.settle(row,tape,(public,peer,step+1,credit&~CREDIT),routing.offers.WAIT,synthetic,False)
    delivered=bool((after[0][peer*2]|after[0][peer*2+1])&target)
    event={"asker":role,"respondent":peer,"slot":step,"target":target,"reply":proof,"admitted":delivered}
    return after,False,event


def play(item,script,policy,start=None,trace=None,events=None):
    row,_=item
    width,truth,local,opening,_=row
    current=start or (sp.opened(opening,local),1,0,7)
    full=(1<<width)-1
    checks=questions=answers=0
    while current[2]<width+1 and not sp.terminal(current[0],full):
        obs,available,base=choices(item,current)
        selected=policy.get(obs,fallback(obs,script))
        if trace is not None and len(available)>1:
            trace.append((obs,checks,{a:advance(item,current,a,available,base)
                                      for a in available if a!=selected}))
        subsequent,checked,asked=advance(item,current,selected,available,base)
        if events is not None:
            changes=[]
            for role in range(2):
                for stance in range(2):
                    i=2*role+stance
                    new=subsequent[0][i]&~current[0][i]
                    if new:
                        changes.append((role,stance,new))
            events.append({"slot":current[2],"actor":current[1],"query":asked,
                           "new_signed_masks":changes})
        checks+=checked
        questions+=asked is not None
        answers+=bool(asked and asked["admitted"])
        current=subsequent
    assert all(not(current[0][2*r]&~t or current[0][2*r+1]&t) for r,t in enumerate(truth))
    return sp.terminal(current[0],full),current[2],checks,questions,answers


def measure(items,script,table):
    seen,counts=[],Counter()
    for item in items:
        out=play(item,script,table)
        seen.append(out)
        a,b=item[0][1]
        key="agreement" if a&b else "impasse"
        counts[key,"paths"]+=1
        for field,value in zip(("solved","slots","checks","questions","answers"),out,strict=True):
            counts[key,field]+=value
    return seen,counts


def fit(cohorts):
    original=[measure(c,START,{})[1] for c in cohorts]
    value=sum(map(sp.fitness,original))
    table,steps={},[]
    for _ in range(8):
        deltas,hits=defaultdict(float),Counter()
        for items in cohorts:
            for item in items:
                trace=[]
                done,end,calls,*_=play(item,START,table,trace=trace)
                for obs,prefix,actions in trace:
                    for k,(state,checked,_) in actions.items():
                        solved,time,rest,*_=play(item,START,table,start=state)
                        key=obs,k
                        deltas[key]+=int(solved)-int(done)+sp.COST*(end-time)+sp.CHECK_COST*(calls-prefix-rest-checked)
                        hits[key]+=1
        ranked=sorted((-delta,key) for key,delta in deltas.items() if delta>0 and hits[key]>=8)
        for _,(obs,action) in ranked:
            proposed={**table,obs:action}
            scores=[measure(items,START,proposed)[1] for items in cohorts]
            if any(next_[k,"solved"]<prev[k,"solved"]
                   for next_,prev in zip(scores,original,strict=True) for k in ("agreement","impasse")):
                continue
            score=sum(map(sp.fitness,scores))
            if score<=value:
                continue
            table,value=proposed,score
            steps.append({"observation":obs,"action":action,"support":hits[obs,action],
                          "train":[sp.flatten(score) for score in scores]})
            break
        else:
            break
    return table,{"baseline":[sp.flatten(x) for x in original],"updates":steps}


def compare(items,policy):
    test,fitted=measure(items,START,policy)
    output={"learned":sp.flatten(fitted)}
    for method in ("never","early_match","match_only",START):
        base,counts=measure(items,method,{})
        paired=Counter()
        for a,b,item in zip(base,test,items,strict=True):
            x,y=item[0][1]
            paired["agreement" if x&y else "impasse",str(a[0]),str(b[0])]+=1
        output[method]={"metrics":sp.flatten(counts),"pairs":sp.flatten(paired)}
    return output


def evaluate():
    train=sp.panels((4,5),TRAIN,280,2)+sp.panels((4,5),TRAIN+1,280,3)
    policy,history=fit((guard.messages(train,TRAIN+2,0,0),
                        guard.messages(routing.refit.drop_returns(train,TRAIN+3),TRAIN+4,.16,.08)))
    wider=sp.panels((6,7),TEST,850,3)
    variants={"clean":guard.messages(wider,TEST+1,0,0),
              "faults":guard.messages(routing.refit.drop_returns(wider,TEST+2),TEST+1,.26,.11)}
    for cases in variants.values():
        for item in cases[:120]:
            assert play(item,"never",{})[:3]==guard.rollout(item,routing.START,{})[:3]
    return {"train":history,"policy":[[obs,a] for obs,a in sorted(policy.items())],
            "test":{k:compare(items,policy) for k,items in variants.items()}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    a=p.parse_args()
    files=(Path(__file__),Path(guard.__file__),guard.HERE/"admit.py",Path(routing.__file__),
           Path(routing.refit.__file__),Path(routing.offers.__file__),Path(sp.__file__),
           sp.LOOKUP/"lookup.py",sp.LOOKUP.parent/"train.py",sp.LOOKUP.parents[1]/"environment.py")
    hashes={str(f.resolve().relative_to(sp.HERE.parents[1])):sha256(f.read_bytes()).hexdigest() for f in files}
    receipt,output=a.directory/"launch.json",a.directory/"results.json"
    if a.mode=="replay":
        assert json.loads(receipt.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate()))==json.loads(output.read_text())
        print(json.dumps({"hashes":len(hashes),"replay_exact":True}))
        return
    a.directory.mkdir()
    receipt.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                   "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                   "run_directory":str(a.directory.resolve()),"command":[sys.executable,*sys.argv],
                                   "sha256":hashes},indent=2)+"\n")
    x=evaluate()
    output.write_text(json.dumps(x,indent=2)+"\n")
    print("accepted",len(x["train"]["updates"]),"updates")


if __name__=="__main__":
    main()
