"""Train a bundle router on selective admission with missing or flipped claims."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

from admit import admit_masks

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import bundle_policy as routing

sp = routing.sp
START = routing.START
TRAIN, TEST = 555321, 452513


def messages(rows, seed, loss, flips):
    rng = random.Random(seed)
    panels = []
    for row in rows:
        width = row[0]
        tape = {}
        for role in range(2):
            for turn in range(width+1):
                dropped = sum(1 << i for i in range(width) if rng.random() < loss)
                flipped = sum(1 << i for i in range(width) if rng.random() < flips)
                tape[role,turn] = dropped, flipped
        panels.append((row, tape))
    return panels


def settle(row, tape, current, action, options, atomic):
    before, actor, turn, _ = current
    after, next_role, end, remaining = routing.step(row,current,action,options,1)
    if action == routing.offers.CHECK:
        return (after, next_role, end, remaining), (0,0,0)
    slot = 2*actor
    accept, exclude = after[slot] & ~before[slot], after[slot+1] & ~before[slot+1]
    intent = accept | exclude
    loss, flip = tape[actor,turn]
    proposed_yes = ((accept & ~flip) | (exclude & flip)) & ~loss
    proposed_no = ((exclude & ~flip) | (accept & flip)) & ~loss
    yes,no,blocked = admit_masks(proposed_yes,proposed_no,*row[2][actor],atomic=atomic)
    dropped = intent & loss
    if atomic and dropped:
        yes = no = 0
    post = sp.record(sp.record(before,actor,yes,True),actor,no,False)
    return (post,next_role,end,remaining), ((yes|no).bit_count(),blocked.bit_count(),dropped.bit_count())


def rollout(item, script, policy, atomic=False, current=None, trace=None):
    row,tape = item
    width,truth,local,opening,_ = row
    current = current or (sp.opened(opening,local),1,0,3)
    full = (1<<width)-1
    totals = [0,0,0,0]
    while current[2] < width+1 and not sp.terminal(current[0],full):
        base,obs,moves = routing.available(row,current,1)
        action = policy.get(obs,routing.choose(base,obs,script))
        if trace is not None and len(moves)>1:
            trace.append((obs,totals[0],{other:settle(row,tape,current,other,moves,atomic)[0]
                                         for other in moves if other!=action}))
        current, evidence = settle(row,tape,current,action,moves,atomic)
        totals[0] += action == routing.offers.CHECK
        for i,value in enumerate(evidence,start=1):
            totals[i] += value
    state = current[0]
    assert all(not (state[2*r] & ~value or state[2*r+1] & value) for r,value in enumerate(truth))
    return (sp.terminal(state,full),current[2],*totals)


def measure(items, script, policy, atomic=False):
    outcomes, counts = [], Counter()
    for item in items:
        results = rollout(item,script,policy,atomic)
        outcomes.append(results)
        row,_ = item
        kind = "agreement" if row[1][0] & row[1][1] else "impasse"
        counts[kind,"paths"] += 1
        for k,v in zip(("solved","slots","checks","admitted","guard_withheld","dropped"),results,strict=True):
            counts[kind,k] += v
    return outcomes,counts


def fit(cohorts):
    init = [measure(c,START,{})[1] for c in cohorts]
    table, journal = {}, []
    current = sum(map(sp.fitness,init))
    for _ in range(8):
        values, seen = defaultdict(float), Counter()
        for items in cohorts:
            for row in items:
                trace = []
                solved,finish,calls,*_ = rollout(row,START,table,trace=trace)
                for obs,prev,alternatives in trace:
                    for action,where in alternatives.items():
                        ok,end,rest,*_ = rollout(row,START,table,current=where)
                        key = obs,action
                        values[key] += (int(ok)-int(solved)+sp.COST*(finish-end)
                                        +sp.CHECK_COST*(calls-prev-rest-(action==routing.offers.CHECK)))
                        seen[key] += 1
        candidates = sorted((-value,key) for key,value in values.items() if value>0 and seen[key]>=8)
        for _,(obs,action) in candidates:
            trial = {**table,obs:action}
            scores = [measure(c,START,trial)[1] for c in cohorts]
            if any(new[tag,"solved"] < old[tag,"solved"]
                   for new,old in zip(scores,init,strict=True) for tag in routing.refit.CLASSES):
                continue
            objective = sum(map(sp.fitness,scores))
            if objective <= current:
                continue
            table,current = trial,objective
            journal.append({"observation":obs,"action":action,"visits":seen[obs,action],
                            "train":[sp.flatten(c) for c in scores]})
            break
        else:
            break
    return table,{"baseline":[sp.flatten(c) for c in init],"updates":journal}


def compare(items, table, previous):
    fitted, metrics = measure(items,START,table)
    data = {"learned":sp.flatten(metrics)}
    for name,script,policy,atomic in (
        ("verification_first","verify_first",{},False),("offer_first","offer_first",{},False),
        ("bundle_first",START,{},False),("opening_bundle","bundle_open",{},False),
        ("atomic_bundle",START,{},True),("prior_learned",START,previous,False),
    ):
        paths,values = measure(items,script,policy,atomic)
        pairs = Counter()
        for item,a,b in zip(items,paths,fitted,strict=True):
            truth = item[0][1]
            kind = "agreement" if truth[0]&truth[1] else "impasse"
            pairs[kind,str(a[0]),str(b[0])] += 1
        data[name] = {"metrics":sp.flatten(values),"paired_vs_learned":sp.flatten(pairs)}
    return data


def evaluate(previous):
    train = sp.panels((4,5),TRAIN,280,2) + sp.panels((4,5),TRAIN+1,280,3)
    table,journal = fit((messages(train,TRAIN+2,0,0),
                         messages(routing.refit.drop_returns(train,TRAIN+3),TRAIN+4,.12,.07)))
    fresh = sp.panels((6,7),TEST,800,3)
    clean = messages(fresh,TEST+1,0,0)
    for item in clean[:200]:
        old = routing.rollout(item[0],START,{})
        assert rollout(item,START,{})[:3] == old[:3]
    variants = {"clean":clean,"moderate":messages(fresh,TEST+1,.12,.07),
                "heavy":messages(routing.refit.drop_returns(fresh,TEST+2),TEST+1,.28,.12)}
    return {"policy":[[obs,act] for obs,act in sorted(table.items())],"training":journal,
            "heldout":{name:compare(items,table,previous) for name,items in variants.items()}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    a=p.parse_args()
    predecessor=HERE.parent/"evidence/bundle-policy/results.json"
    previous={(tuple(k[0]),*k[1:]):v for k,v in json.loads(predecessor.read_text())["policy"]}
    files=(Path(__file__),HERE/"admit.py",predecessor,Path(routing.__file__),
           Path(routing.refit.__file__),Path(routing.offers.__file__),Path(sp.__file__),
           sp.LOOKUP/"lookup.py",sp.LOOKUP.parent/"train.py",sp.LOOKUP.parents[1]/"environment.py")
    hashes={str(f.resolve().relative_to(sp.HERE.parents[1])):sha256(f.read_bytes()).hexdigest() for f in files}
    launch, output=a.directory/"launch.json",a.directory/"results.json"
    if a.mode=="replay":
        assert json.loads(launch.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate(previous)))==json.loads(output.read_text())
        print(json.dumps({"verified_hashes":len(hashes),"rollouts_replay":True}))
        return
    a.directory.mkdir()
    launch.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                 "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                 "command":[sys.executable,*sys.argv],"run_directory":str(a.directory.resolve()),
                                 "sha256":hashes},indent=2)+"\n")
    bundle=evaluate(previous)
    output.write_text(json.dumps(bundle,indent=2)+"\n")
    print("Accepted",len(bundle["training"]["updates"]),"updates")


if __name__=="__main__":
    main()
