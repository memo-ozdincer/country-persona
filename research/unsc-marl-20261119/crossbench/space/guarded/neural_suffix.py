"""Learn a local policy from paired returns under the same continuation policy."""
import argparse
from collections import Counter
from functools import lru_cache
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

import neural_router as neural

guard,sp,routing = neural.guard,neural.sp,neural.routing
HERE = Path(__file__).resolve().parent


def sample(item,rng):
    row,_=item
    width,_,local,opening,_=row
    full=(1<<width)-1
    start=sp.opened(opening,local),1,0,3

    def ended(state):
        return sp.terminal(state[0],full) or state[2]>=width+1

    def next_(state,action,moves):
        after=neural.next_state(item,state,action,moves)
        cost=sp.COST*(after[2]-state[2])+sp.CHECK_COST*(action==routing.offers.CHECK)
        return after,cost

    @lru_cache(maxsize=None)
    def fixed(state):
        if ended(state):
            return float(sp.terminal(state[0],full))
        moves,default=neural.candidates(item,state,neural.BASE)
        after,cost=next_(state,default,moves)
        return fixed(after)-cost

    @lru_cache(maxsize=None)
    def optimal(state):
        if ended(state):
            return float(sp.terminal(state[0],full))
        moves,_=neural.candidates(item,state,neural.BASE)
        return max(optimal(after)-cost for after,cost in (next_(state,k,moves) for k in moves))

    seen,output=set(),[]
    for guided in (False,True):
        state=start
        while not ended(state):
            moves,default=neural.candidates(item,state,neural.BASE)
            values={k:next_(state,k,moves) for k in moves}
            if len(moves)>1 and state not in seen:
                seen.add(state)
                scores={k:fixed(after)-cost for k,(after,cost) in values.items()}
                offset=scores[default]
                output.append((neural.state_features(row,state,moves,default),
                               [scores.get(k,offset)-offset for k in range(neural.ACTIONS)],
                               [k in moves for k in range(neural.ACTIONS)]))
            if guided:
                action=max(values,key=lambda i:(optimal(values[i][0])-values[i][1],i==default,-i))
            else:
                action=default if rng.random()>.25 else rng.choice(tuple(moves))
            state=values[action][0]
    ceiling=optimal(start)
    optimal.cache_clear()
    fixed.cache_clear()
    return output,ceiling


def evaluate():
    seeds=neural.TRAIN,neural.TEST
    seed,test=seeds
    familiar=sp.panels((4,5),seed,250,2)+sp.panels((4,5),seed+1,250,3)
    train=(guard.messages(familiar,seed+2,0,0)
           +guard.messages(routing.refit.drop_returns(familiar,seed+3),seed+4,.16,.08))
    rng=random.Random(seed+5)
    vectors=[]
    for item in train:
        points,_=sample(item,rng)
        vectors.extend(points)
    learned,updates=neural.train(vectors)
    fresh=sp.panels((6,7),test,900,3)
    panels={"clean":guard.messages(fresh,test+1,0,0),
            "faults":guard.messages(routing.refit.drop_returns(fresh,test+2),test+1,.26,.11)}
    heldout={k:neural.score(v,learned) for k,v in panels.items()}
    bounds={}
    for k,items in panels.items():
        tally=Counter()
        rng=random.Random(test+15)
        for item in items:
            truth=item[0][1]
            label="agreement" if truth[0]&truth[1] else "impasse"
            if tally[label,"n"]==128:
                continue
            _,cap=sample(item,rng)
            tally[label,"n"]+=1
            tally[label,"optimal"]+=cap>0
            tally[label,"bundle_first"]+=neural.play(item,neural.BASE)[0]
            tally[label,"learned"]+=neural.play(item,neural.BASE,learned)[0]
        bounds[k]=sp.flatten(tally)
    return {"training":{**updates,"presentations":len(train),"threshold":neural.THRESHOLD},
            "weights":[a.tolist() for a in learned],"heldout":heldout,"centralized_bound_subset":bounds}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    a=p.parse_args()
    original=HERE/"evidence/neural/launch.json"
    source=sp.HERE.parents[1]
    dependencies=json.loads(original.read_text())["sha256"]
    hashes={k:neural.sha256((source/k).read_bytes()).hexdigest() for k in dependencies}
    assert hashes==dependencies
    hashes[str(Path(__file__).resolve().relative_to(source))]=neural.sha256(Path(__file__).read_bytes()).hexdigest()
    launch,results=a.directory/"launch.json",a.directory/"results.json"
    if a.mode=="replay":
        assert json.loads(launch.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate()))==json.loads(results.read_text())
        print(json.dumps({"hashes":len(hashes),"fit_replays":True}))
        return
    a.directory.mkdir()
    launch.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                 "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                 "run_directory":str(a.directory.resolve()),"command":[sys.executable,*sys.argv],
                                 "numpy":neural.np.__version__,"sha256":hashes},indent=2)+"\n")
    data=evaluate()
    results.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps(data["training"]))


if __name__=="__main__":
    main()
