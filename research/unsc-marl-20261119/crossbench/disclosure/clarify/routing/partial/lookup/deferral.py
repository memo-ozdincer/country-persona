"""Learn check-or-defer decisions with a frozen signed-disclosure controller."""
import argparse
from collections import Counter, defaultdict
from itertools import product
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

from lookup import (ROOT, HERE, CHECK, COST, choices, digest, dump, examples, flatten,
                    label, opened, terminal, transition)
from environment import presentations

TRAIN_WIDTHS = (3,4)
TEST_SEED = 33725
FRESH_SEED = 771044
FRESH_PER_CLASS = 3500
MAX_UPDATES = 12


def train_set():
    for n in TRAIN_WIDTHS:
        full = (1 << n)-1
        for gold, first in presentations(n):
            for missing in product(range(n),repeat=2):
                known = [full ^ (1 << k) for k in missing]
                yield n,gold,tuple((truth & avail, ~truth & avail)
                                  for truth,avail in zip(gold,known,strict=True)),first


def options(state, local, role, step, n, credit):
    key, offered, default = choices(state,local,role,step,n,credit)
    _, skip, continuation = choices(state,local,role,step,n,credit,True)
    allowed = {False:skip[continuation]}
    initial = default[0]==CHECK
    if (CHECK,True) in offered:
        allowed[True]=offered[CHECK,True]
    # Inputs are compact public facts and the acting delegate's masks.
    # The other delegate's signs and the hidden truthful answer are absent.
    full=(1 << n)-1
    own_yes,own_no=local[role]
    peer_yes=state[2*(1-role)]
    obs=(key[0],key[1],key[2],key[3],key[4],continuation,initial,
         min(peer_yes.bit_count(),2), min(own_yes.bit_count(),2),
         bool((full & ~(state[1]|state[3])) & peer_yes & ~(own_yes|own_no)))
    return obs,allowed,initial


def step(entry, private, local, role, credit, lookup):
    # Only the simulator uses the hidden mandate, and only after a check
    # is selected. Ordinary signed actions have fixed effects.
    return transition(entry,private,local,role,credit,(CHECK,True) if lookup else (-1,False))


def run(n,private,state,local,role,turn,credit,policy):
    calls=0
    full=(1 << n)-1
    for i in range(turn,n+1):
        if terminal(state,full):
            return True, i-turn, calls
        key,allowed,baseline=options(state,local,role,i,n,credit)
        choose=policy.get(key,baseline) if True in allowed else False
        calls += choose
        state,local,role,credit=step(allowed[choose],private,local,role,credit,choose)
    return terminal(state,full), n+1-turn, calls


def play(row,policy):
    n,private,local,opening=row
    return run(n,private,opened(opening,local),local,1,0,1,policy)


def measure(rows,policy):
    counts, outcomes=Counter(),[]
    for row in rows:
        cls=label(row)
        certificate, cost, calls=play(row,policy)
        for key,val in (("presentations",1),("certificates",certificate),
                        ("slots",cost),("checks",calls)):
            counts[cls,key]+=val
        outcomes.append(certificate)
    return counts, outcomes


def alternatives(rows,policy):
    evaluated=defaultdict(Counter)
    for n,private,local,opening in rows:
        state,role,credit=opened(opening,local),1,1
        full=(1 << n)-1
        for turn in range(n+1):
            if terminal(state,full):
                break
            key,allowed,base=options(state,local,role,turn,n,credit)
            action=policy.get(key,base) if True in allowed else False
            after,known,receiver,remaining=step(allowed[action],private,local,role,credit,action)
            if True in allowed:
                opposite=not action
                alt=step(allowed[opposite],private,local,role,credit,opposite)
                a, cost, _=run(n,private,after,known,receiver,turn+1,remaining,policy)
                b, cost2, _=run(n,private,alt[0],alt[1],alt[2],turn+1,alt[3],policy)
                stats=evaluated[key,opposite]
                stats["visits"]+=1
                stats["gains"]+=b and not a
                stats["losses"]+=a and not b
                stats["slots_saved"]+=cost-cost2
            state,local,role,credit=after,known,receiver,remaining
    return evaluated


def reward(stats):
    return sum(stats[cls,"certificates"]-COST*stats[cls,"slots"] for cls in ("agreement","impasse"))


def fit(rows):
    policy={}
    initial,protected=measure(rows,policy)
    current=initial
    changes=[]
    for _ in range(MAX_UPDATES):
        est=alternatives(rows,policy)
        ranked=sorted((-(v["gains"]-v["losses"]+COST*v["slots_saved"]),k)
                      for k,v in est.items() if v["visits"]>=5)
        updated=False
        for margin,(key,action) in ranked:
            if margin>=0:
                break
            proposal={**policy,key:action}
            if action==key[6]:
                proposal.pop(key)
            values,matched=measure(rows,proposal)
            if any(a and not b for a,b in zip(protected,matched,strict=True)):
                continue
            if reward(values)<=reward(current):
                continue
            policy,current=proposal,values
            changes.append({"observation":key,"check":action,
                            "counterfactual":dict(est[key,action]),"metrics":flatten(values)})
            updated=True
            break
        if not updated:
            break
    return policy,{"initial":flatten(initial),"final":flatten(current),"updates":changes}


def freeze(policy):
    return [[k,v] for k,v in sorted(policy.items())]


def restore(raw):
    return {tuple(k[:2])+(tuple(k[2]),k[3],k[4],tuple(k[5]),*k[6:]):v for k,v in raw}


def fresh():
    rnd=random.Random(FRESH_SEED)
    buckets={"agreement":[],"impasse":[]}
    seen=Counter()
    for row in examples((7,),FRESH_SEED,stress=True):
        cls=label(row)
        keep=buckets[cls]
        seen[cls]+=1
        if len(keep)<FRESH_PER_CLASS:
            keep.append(row)
        else:
            pos=rnd.randrange(seen[cls])
            if pos<FRESH_PER_CLASS:
                keep[pos]=row
    return buckets["agreement"]+buckets["impasse"]


def compare(rows,policy):
    before,bases=measure(rows,{})
    after,learned=measure(rows,policy)
    pairs=Counter((label(row),str(a),str(b)) for row,a,b in zip(rows,bases,learned,strict=True))
    return {"script":flatten(before),"learned":flatten(after),"paired":flatten(pairs)}


def main(out):
    out.mkdir()
    paths=[Path(__file__).resolve(),HERE/"lookup.py",HERE.parent/"train.py",
           *(ROOT/n for n in ("environment.py","joint.py","learn.py","guard.py"))]
    dump(out/"launch.json",{
        "host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
        "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "command":[sys.executable,*sys.argv],"run_directory":str(out.resolve()),
        "sha256":{str(p.relative_to(ROOT)):digest(p) for p in paths},
        "train_widths":TRAIN_WIDTHS,"test_seed":TEST_SEED,"fresh_seed":FRESH_SEED,
        "fresh_per_class":FRESH_PER_CLASS,"slot_budget":"n+1 including at most one local verification",
    })
    policy,detail=fit(list(train_set()))
    dump(out/"policy.json",freeze(policy))
    dump(out/"training.json",detail)
    print("Accepted changes:",len(detail["updates"]),flush=True)
    for name, rows in (("width-5",list(examples((5,),TEST_SEED+5))),
                       ("width-6",list(examples((6,),TEST_SEED+6,stress=True))),
                       ("fresh-7",fresh())):
        stats=compare(rows,policy)
        dump(out/f"{name}.json",stats)
        print(name,stats["script"],stats["learned"],flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    main(p.parse_args().output)
