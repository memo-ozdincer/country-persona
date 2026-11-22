"""Fit verification timing while keeping the original signed-disclosure rules."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

from lookup import (HERE, ROOT, TEST, TRAIN, MAX_UPDATES, CHECK, COST, choices,
                    compare, digest, dump, effect, examples, flatten, freeze,
                    label, measure, reward)

FRESH = 79137
PER_CLASS = 4000


def fit(rows):
    policy={}
    initial,_=measure(rows,policy)
    current=initial
    history=[]
    for _ in range(MAX_UPDATES):
        stats=effect(rows,policy)
        rank=sorted(
            (-(v["gains"]-v["losses"]+COST*v["slots_saved"]),k)
            for k,v in stats.items()
            if v["visits"]>=3 and (k[1]==(CHECK,True) or
                (k[0] in policy and k[1]==k[0][-1]))
        )
        accepted=False
        for estimate,(obs,action) in rank:
            if estimate>=0:
                break
            candidate={**policy,obs:action}
            if action==obs[-1]:
                candidate.pop(obs)
            scores,_=measure(rows,candidate)
            if any(scores[name,"certificates"]<current[name,"certificates"]
                   for name in ("agreement","impasse")):
                continue
            if reward(scores)<=reward(current):
                continue
            policy,current=candidate,scores
            accepted=True
            history.append({"observation":obs,"action":action,"counterfactual":dict(stats[obs,action]),
                            "metrics":flatten(scores)})
            break
        if not accepted:
            break
    return policy,{"initial":flatten(initial),"final":flatten(current),"updates":history}


def fresh():
    rng=random.Random(FRESH)
    groups={"agreement":[],"impasse":[]}
    seen=Counter()
    for row in examples((7,),FRESH,stress=True):
        name=label(row)
        seen[name]+=1
        bucket=groups[name]
        if len(bucket)<PER_CLASS:
            bucket.append(row)
        else:
            selected=rng.randrange(seen[name])
            if selected<PER_CLASS:
                bucket[selected]=row
    return groups["agreement"]+groups["impasse"]


def main(output):
    output.mkdir()
    sources=[Path(__file__).resolve(),HERE/"lookup.py",HERE.parent/"train.py",
             *(ROOT/n for n in ("environment.py","joint.py","guard.py","learn.py"))]
    dump(output/"launch.json",{
        "host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
        "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
        "sha256":{str(p.relative_to(ROOT)):digest(p) for p in sources},
        "training_seed":TRAIN,"exposed_test_seed":TEST,"fresh_seed":FRESH,"fresh_per_class":PER_CLASS,
    })
    policy,journal=fit(list(examples((3,4),TRAIN)))
    dump(output/"training.json",journal)
    dump(output/"policy.json",freeze(policy))
    print("Accepted timing updates",len(journal["updates"]),flush=True)
    for name, rows in [
        ("exposed-5",list(examples((5,),TEST+5))),
        ("exposed-6",list(examples((6,),TEST+6,stress=True))),
        ("fresh-7",fresh())
    ]:
        report=compare(rows,policy)
        dump(output/f"{name}.json",report)
        print(name,report["metrics"],flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    main(a.output)
