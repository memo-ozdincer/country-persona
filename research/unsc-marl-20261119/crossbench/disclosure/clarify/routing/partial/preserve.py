"""Evaluate proof-preserving choices under incomplete role observations."""
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

from train import ROOT, HERE, TEST_SEED, opened, position, terminal, measure, flat, restore, examples, replay, label

FRESH_WIDTH = 7
FRESH_SEED = 77192
FRESH_PER_CLASS = 4000


def select(local, state, role, step, width, policy, mode):
    key, choices, default = position(local,state,role,step,width)
    action = policy.get(key,default)
    full = (1 << width)-1
    open_ = full & ~(state[1] | state[3])
    too_few_for_an_offer = width-step <= open_.bit_count()
    if mode != "raw" and action[0]==2 and default[0] in (1,3) and too_few_for_an_offer:
        cannot_ever_exclude = 0
        if mode=="local":
            cannot_ever_exclude = open_ & ~local[role][1] & state[2*(1-role)]
        if mode=="availability":
            peer_available = local[1-role][0] | local[1-role][1]
            cannot_ever_exclude = open_ & ~local[role][1] & (state[2*(1-role)] | ~peer_available)
        if not cannot_ever_exclude:
            action=default
    bit, accept, after, receiver = choices[action]
    if mode!="raw" and bit and not accept and receiver==role and not (local[role][1] & ~(after[1]|after[3])):
        receiver=1-role
    return bit, accept, after, receiver


def play(row,policy,mode):
    n, _, local, opening = row
    state, role, full = opened(opening,local), 1, (1 << n)-1
    for step in range(n):
        if terminal(state,full):
            return True, step
        _, _, state, role = select(local,state,role,step,n,policy,mode)
    return terminal(state,full),n


def fresh():
    # Reservoir sampling gives deterministic, stratified fixed-size cohorts
    # without inspecting a policy or outcome certificate.
    rng = random.Random(FRESH_SEED)
    groups={"agreement":[],"impasse":[]}
    seen=Counter()
    for row in examples((FRESH_WIDTH,),FRESH_SEED,stress=True):
        cls=label(row)
        seen[cls]+=1
        pool=groups[cls]
        if len(pool)<FRESH_PER_CLASS:
            pool.append(row)
        else:
            idx=rng.randrange(seen[cls])
            if idx<FRESH_PER_CLASS:
                pool[idx]=row
    return groups["agreement"]+groups["impasse"]


def report(worlds, policy):
    names=("baseline","raw","local","availability","strict")
    runs=[lambda r:replay(r,{}),*(lambda r, mode=mode:play(r,policy,mode) for mode in names[1:])]
    statuses={key:measure(worlds,run) for key,run in zip(names,runs,strict=True)}
    effects=Counter()
    control=statuses["baseline"][1]
    for key, (_,predictions) in statuses.items():
        for row,before,after in zip(worlds,control,predictions,strict=True):
            effects[key,label(row),str(before),str(after)]+=1
    return {"metrics":{k:flat(v[0]) for k,v in statuses.items()},"paired":flat(effects)}


def run(policy_path, output):
    output.mkdir()
    policy=restore(json.loads(policy_path.read_text()))
    deps=(Path(__file__).resolve(),HERE/"train.py",
          *(ROOT/n for n in ("environment.py","joint.py","guard.py","learn.py")))
    launch={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
            "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
            "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
            "sha256":{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in deps},
            "policy_sha256":sha256(policy_path.read_bytes()).hexdigest(),"fresh_seed":FRESH_SEED,
            "fresh_width":FRESH_WIDTH,"fresh_per_class":FRESH_PER_CLASS}
    (output/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    for name,cohort in [
        ("exposed-5",list(examples((5,),TEST_SEED+5))),
        ("exposed-6",list(examples((6,),TEST_SEED+6,stress=True))),
        ("fresh-7",fresh()),
    ]:
        scores=report(cohort,policy)
        (output/f"{name}.json").write_text(json.dumps(scores,indent=2)+"\n")
        print(name,{k:(v["agreement/certificates"],v["impasse/certificates"],
                        v["agreement/slots"]) for k,v in scores["metrics"].items()},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("policy",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    run(a.policy,a.output)
