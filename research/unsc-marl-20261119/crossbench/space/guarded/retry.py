"""Learn whether the sender should retransmit a withheld sign before handing off."""
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

sp, routing = guard.sp, guard.routing
TRAIN, TEST = 365908, 307241
BASE = "terminal_retry"


def fallback(obs, mode):
    return mode == "always_retry" or (mode == BASE and obs[0])


def opportunity(item, before, after, action, options):
    row,_ = item
    width, _, _, _, _ = row
    start, actor, _, _ = before
    public, next_actor, turn, credit = after
    if turn > width or action == routing.offers.CHECK or sp.terminal(public,(1<<width)-1):
        return None
    intended = routing.step(row,before,action,options,1)[0]
    missing_yes = intended[actor*2] & ~public[actor*2]
    missing_no = intended[actor*2+1] & ~public[actor*2+1]
    if not (missing_yes or missing_no):
        return None
    open_ = ((1<<width)-1) & ~(public[1] | public[3])
    certain = bool(missing_yes & public[2*(1-actor)] or (open_ & ~missing_no)==0)
    obs = (certain,bool(missing_yes),bool(missing_no),min(open_.bit_count(),3),
           min(width+1-turn,3),next_actor==actor)
    pending = sp.record(sp.record(public,actor,missing_yes,True),actor,missing_no,False)
    resume = (public,actor,turn,credit)
    moves = {routing.offers.WAIT:(missing_yes|missing_no,pending,next_actor)}
    retransmit = guard.settle(row,item[1],resume,routing.offers.WAIT,moves,False)[0]
    return obs,retransmit


def play(item,mode,policy,current=None,trace=None):
    row,tape = item
    width,truth,local,opening,_ = row
    current = current or (sp.opened(opening,local),1,0,3)
    checks = attempts = 0
    full = (1<<width)-1
    while current[2] < width+1 and not sp.terminal(current[0],full):
        base,obs,moves = routing.available(row,current,1)
        action = routing.choose(base,obs,routing.START)
        following,_ = guard.settle(row,tape,current,action,moves,False)
        recovery = opportunity(item,current,following,action,moves)
        checks += action==routing.offers.CHECK
        if recovery:
            key,retry = recovery
            choose = policy.get(key,fallback(key,mode))
            if trace is not None:
                trace.append((key,choose,checks,following if choose else retry))
            following = retry if choose else following
            attempts += choose
        current = following
    assert all(not (current[0][2*r]&~gold or current[0][2*r+1]&gold) for r,gold in enumerate(truth))
    return sp.terminal(current[0],full),current[2],checks,attempts


def measure(items,mode,policy):
    counts, outcomes = Counter(), []
    for item in items:
        result = play(item,mode,policy)
        outcomes.append(result)
        left,right = item[0][1]
        label = "agreement" if left&right else "impasse"
        counts[label,"paths"] += 1
        for key,value in zip(("solved","slots","checks","retry"),result,strict=True):
            counts[label,key] += value
    return outcomes,counts


def fit(items):
    _,initial = measure(items,BASE,{})
    previous,table,log = initial,{},[]
    for _ in range(8):
        delta,hits = defaultdict(float),Counter()
        for row in items:
            trace=[]
            ok,time,calls,_ = play(row,BASE,table,trace=trace)
            for key,chosen,prefix,alt in trace:
                certified,end,rest,_ = play(row,BASE,table,current=alt)
                tag = key,not chosen
                delta[tag] += int(certified)-int(ok)+sp.COST*(time-end)+sp.CHECK_COST*(calls-prefix-rest)
                hits[tag] += 1
        candidates = sorted((-value,key) for key,value in delta.items() if value>0 and hits[key]>=8)
        for _,(obs,choice) in candidates:
            attempt={**table,obs:choice}
            _,score = measure(items,BASE,attempt)
            if any(score[k,"solved"]<initial[k,"solved"] for k in ("agreement","impasse")):
                continue
            if sp.fitness(score)<=sp.fitness(previous):
                continue
            table,previous = attempt,score
            log.append({"observation":obs,"retry":choice,"visits":hits[obs,choice],"metrics":sp.flatten(score)})
            break
        else:
            break
    return table,{"initial":sp.flatten(initial),"updates":log}


def evaluate():
    train = sp.panels((4,5),TRAIN,300,2) + sp.panels((4,5),TRAIN+1,300,3)
    table,journal = fit(guard.messages(train,TRAIN+2,.18,.09))
    fresh = sp.panels((6,7),TEST,750,3)
    sets = {"moderate":guard.messages(fresh,TEST+1,.12,.07),
            "heavy":guard.messages(routing.refit.drop_returns(fresh,TEST+2),TEST+1,.28,.12)}
    result={"policy":[[obs,x] for obs,x in sorted(table.items())],"training":journal,"heldout":{}}
    for label,cases in sets.items():
        learned,counts = measure(cases,BASE,table)
        metrics={"learned":sp.flatten(counts)}
        for mode in ("never_retry",BASE,"always_retry"):
            baseline,counts = measure(cases,mode,{})
            paired=Counter()
            for item,a,b in zip(cases,baseline,learned,strict=True):
                l,r=item[0][1]
                paired["agreement" if l&r else "impasse",str(a[0]),str(b[0])] += 1
            metrics[mode]={"metrics":sp.flatten(counts),"paired":sp.flatten(paired)}
        result["heldout"][label]=metrics
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    args=p.parse_args()
    files=(Path(__file__),Path(guard.__file__),guard.HERE/"admit.py",Path(routing.__file__),
           Path(routing.offers.__file__),Path(sp.__file__),sp.LOOKUP/"lookup.py",
           sp.LOOKUP.parent/"train.py",sp.LOOKUP.parents[1]/"environment.py")
    hashes={str(f.resolve().relative_to(sp.HERE.parents[1])):sha256(f.read_bytes()).hexdigest() for f in files}
    launch,output=args.directory/"launch.json",args.directory/"results.json"
    if args.mode=="replay":
        assert json.loads(launch.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate()))==json.loads(output.read_text())
        print(json.dumps({"verified_hashes":len(hashes),"replay_exact":True}))
        return
    args.directory.mkdir()
    launch.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                 "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                 "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes},indent=2)+"\n")
    result=evaluate()
    output.write_text(json.dumps(result,indent=2)+"\n")
    print("Accepted",len(result["training"]["updates"]),"updates")


if __name__=="__main__":
    main()
