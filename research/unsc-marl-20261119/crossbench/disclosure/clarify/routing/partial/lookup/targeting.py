"""Counterfactual target selection on a fixed verification schedule."""
import argparse
from collections import Counter, defaultdict
from itertools import combinations, product
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

from lookup import (HERE, ROOT, CHECK, COST, choices, digest, dump, examples,
                    flatten, label, opened, terminal, transition)
from environment import presentations

TEST_SEED = 58741
FRESH_SEED = 90328
PER_CLASS = 3000
MAX_UPDATES = 12


def training():
    """Exhaustively mask two signs per actor on the small option grids."""
    for width in (3,4):
        full=(1<<width)-1
        counts=[sum(1<<i for i in pair) for pair in combinations(range(width),2)]
        for truth,first in presentations(width):
            for l,r in product(counts,repeat=2):
                local=tuple((menu & ~skip & full, ~menu & ~skip & full)
                            for menu,skip in zip(truth,(l,r),strict=True))
                yield width,truth,local,first


def decision(n,state,local,role,turn,credit):
    observation,entries,default=choices(state,local,role,turn,n,credit)
    entry=entries[default]
    if default[0]!=CHECK:
        return None,{"script":entry},False
    full=(1<<n)-1
    yes,no=local[role]
    unknown=full & ~(yes|no|state[1]|state[3])
    peer=unknown & state[2*(1-role)]
    other=unknown & ~peer
    targets={"script":entry}
    for tag,mask in (("offered",peer),("unoffered",other)):
        if mask:
            targets[f"{tag}_first"]=(mask & -mask,state,role)
            targets[f"{tag}_last"]=(1<<(mask.bit_length()-1),state,role)
    key=(observation[0],observation[1],observation[2],
         min(peer.bit_count(),2),min(other.bit_count(),2),min(yes.bit_count(),2),
         min(state[2*(1-role)].bit_count(),2),tuple(targets))
    return key,targets,True


def run(n,truth,state,local,role,t,credit,policy):
    checks=0
    full=(1<<n)-1
    for turn in range(t,n+1):
        if terminal(state,full):
            return True,turn-t,checks
        key,go,checking=decision(n,state,local,role,turn,credit)
        move=(CHECK,True) if checking else (-1,False)
        entry=go[policy.get(key,"script")]
        state,local,role,credit=transition(entry,truth,local,role,credit,move)
        checks+=checking
    return terminal(state,full),n+1-t,checks


def play(row,policy):
    n,truth,local,first=row
    return run(n,truth,opened(first,local),local,1,0,1,policy)


def assess(rows,policy):
    counts, flags=Counter(),[]
    for row in rows:
        cls=label(row)
        cert,slots,checks=play(row,policy)
        for metric,value in (("all",1),("certificates",cert),("slots",slots),("checks",checks)):
            counts[cls,metric]+=value
        flags.append(cert)
    return counts,flags


def alternatives(rows,policy):
    totals=defaultdict(Counter)
    for n,truth,local,opening in rows:
        state,role,credit=opened(opening,local),1,1
        for t in range(n+1):
            if terminal(state,(1<<n)-1):
                break
            key,choices_,checking=decision(n,state,local,role,t,credit)
            chosen=policy.get(key,"script")
            if checking:
                move=(CHECK,True)
                current=transition(choices_[chosen],truth,local,role,credit,move)
                score,slots,_=run(n,truth,current[0],current[1],current[2],t+1,current[3],policy)
                for name,entry in choices_.items():
                    if entry==choices_[chosen]:
                        continue
                    other=transition(entry,truth,local,role,credit,move)
                    value,cost,_=run(n,truth,other[0],other[1],other[2],t+1,other[3],policy)
                    c=totals[key,name]
                    c["visits"]+=1
                    c["gain"]+=value and not score
                    c["loss"]+=score and not value
                    c["slots_saved"]+=slots-cost
                break
            state,local,role,credit=transition(choices_[chosen],truth,local,role,credit,(-1,False))
    return totals


def value(metrics):
    return sum(metrics[k,"certificates"]-COST*metrics[k,"slots"] for k in ("agreement","impasse"))


def fit(rows):
    policy={}
    before,protected=assess(rows,policy)
    current=before
    changes=[]
    for _ in range(MAX_UPDATES):
        scores=alternatives(rows,policy)
        ranked=sorted((-(c["gain"]-c["loss"]+COST*c["slots_saved"]),k)
                      for k,c in scores.items() if c["visits"]>=5)
        improved=False
        for negative,(key,target) in ranked:
            if negative>=0:
                break
            trial={**policy,key:target}
            if target=="script":
                trial.pop(key,None)
            metrics,flags=assess(rows,trial)
            if any(a and not b for a,b in zip(protected,flags,strict=True)):
                continue
            if value(metrics)<=value(current):
                continue
            policy,current=trial,metrics
            improved=True
            changes.append({"observation":key,"target":target,
                            "counterfactual":dict(scores[key,target]),"metrics":flatten(metrics)})
            break
        if not improved:
            break
    return policy,{"initial":flatten(before),"final":flatten(current),"updates":changes}


def freeze(policy):
    return [[k,name] for k,name in sorted(policy.items())]


def restore(data):
    return {(k[0],k[1],tuple(k[2]),*k[3:7],tuple(k[7])):v for k,v in data}


def best(row):
    n,truth,local,opening=row
    state,role=opened(opening,local),1
    full=(1<<n)-1
    for t in range(n+1):
        if terminal(state,full):
            return True
        _,entries,checking=decision(n,state,local,role,t,1)
        if checking:
            for i in range(n):
                bit=1<<i
                yes,no=local[role]
                if bit & (yes|no|state[1]|state[3]):
                    continue
                after,seen,actor,credit=transition((bit,state,role),truth,local,role,1,(CHECK,True))
                if run(n,truth,after,seen,actor,t+1,credit,{})[0]:
                    return True
            return False
        state,local,role,_=transition(entries["script"],truth,local,role,1,(-1,False))
    return terminal(state,full)


def evaluate(rows,policy):
    script,before=assess(rows,{})
    learned,after=assess(rows,policy)
    oracle, paired=Counter(),Counter()
    for row,a,b in zip(rows,before,after,strict=True):
        cls=label(row)
        cap=best(row)
        assert cap or not (a or b)
        oracle[cls,"certificates"]+=cap
        paired[cls,str(a),str(b)]+=1
    return {"script":flatten(script),"learned":flatten(learned),
            "perfect_target_choice":flatten(oracle),"paired":flatten(paired)}


def fresh():
    rng=random.Random(FRESH_SEED)
    rows={"agreement":[],"impasse":[]}
    seen=Counter()
    for row in examples((7,),FRESH_SEED,stress=True):
        cls=label(row)
        seen[cls]+=1
        if len(rows[cls])<PER_CLASS:
            rows[cls].append(row)
        else:
            index=rng.randrange(seen[cls])
            if index<PER_CLASS:
                rows[cls][index]=row
    return rows["agreement"]+rows["impasse"]


def main(out):
    out.mkdir()
    deps=[Path(__file__).resolve(),HERE/"lookup.py",HERE.parent/"train.py",
          *(ROOT/n for n in ("environment.py","learn.py","guard.py","joint.py"))]
    dump(out/"launch.json",{"command":[sys.executable,*sys.argv],"device":"CPU","host":socket.gethostname(),
        "pid":os.getpid(),"process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "run_directory":str(out.resolve()),"sha256":{str(p.relative_to(ROOT)):digest(p) for p in deps},
        "budget":"n+1 slots, one check, only target changes","test_seed":TEST_SEED,"fresh_seed":FRESH_SEED})
    policy,log=fit(list(training()))
    dump(out/"training.json",log)
    dump(out/"policy.json",freeze(policy))
    print("Accepted target changes",len(log["updates"]),flush=True)
    for name, rows in (("width-5",list(examples((5,),TEST_SEED+5,stress=True))),
                       ("width-6",list(examples((6,),TEST_SEED+6,stress=True))),
                       ("fresh-7",fresh())):
        result=evaluate(rows,policy)
        dump(out/f"{name}.json",result)
        print(name,{k:v for k,v in result.items() if k!="paired"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    main(p.parse_args().output)
