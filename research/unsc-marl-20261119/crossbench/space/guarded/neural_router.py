"""Centralized counterfactual value training with a shared decentralized actor."""
import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

import numpy as np
import robust_bundle as guard

sp, routing = guard.sp, guard.routing
TRAIN, TEST = 451128, 850355
BASE = routing.START
ACTIONS = 4
THRESHOLD = .025


def actor_view(width, own, public, role, turn, credit, options, default):
    """No peer private evidence, world labels, or fault tape enter the actor."""
    own_yes, own_no = own
    peer = public[2*(1-role)]
    mine = public[2*role]
    blocked = public[1] | public[3]
    open_ = ((1<<width)-1)&~blocked
    visible = (
        own_yes&open_,own_no&open_,open_&~(own_yes|own_no),peer&open_,mine&open_,
        own_yes&peer&open_,own_no&peer&open_,peer&open_&~(own_yes|own_no),
        own_yes&open_&~mine,blocked,open_,
    )
    return [
        *(m.bit_count()/width for m in visible),
        (width+1-turn)/(width+1), min(3,width+1-turn)/3, float(turn==0),
        float(bool(credit&(1<<role))),float(bool(credit&(1<<(1-role)))),
        *(float(i in options) for i in range(ACTIONS)),
        *(float(i==default) for i in range(ACTIONS)),
    ]


def state_features(row,current,options,default):
    width,_,local,_,_ = row
    public,role,turn,credit = current
    return actor_view(width,local[role],public,role,turn,credit,options,default)


def candidates(item, state, continuation):
    row,tape = item
    basis, obs, moves = routing.available(row,state,1)
    default = routing.choose(basis,obs,continuation)
    return moves,default


def next_state(item,state,action,moves):
    row,tape = item
    return guard.settle(row,tape,state,action,moves,False)[0]


def sample(item, rng):
    width,_,local,opening,_=item[0]
    root=sp.opened(opening,local),1,0,3
    full=(1<<width)-1

    @lru_cache(maxsize=None)
    def value(state):
        if sp.terminal(state[0],full):
            return 1.
        if state[2] >= width+1:
            return 0.
        moves,_=candidates(item,state,BASE)
        return max(branch(state,action,moves)[0] for action in moves)

    def branch(state,action,moves):
        following=next_state(item,state,action,moves)
        penalty=sp.COST*(following[2]-state[2])+sp.CHECK_COST*(action==routing.offers.CHECK)
        return value(following)-penalty,following

    seen=set()
    examples=[]
    for guided in (False,True):
        state=root
        while state[2] < width+1 and not sp.terminal(state[0],full):
            moves,default=candidates(item,state,BASE)
            choices={action:branch(state,action,moves) for action in moves}
            if len(choices)>1 and state not in seen:
                seen.add(state)
                x=state_features(item[0],state,moves,default)
                offset=choices[default][0]
                q=[choices[a][0]-offset if a in choices else 0. for a in range(ACTIONS)]
                examples.append((x,q,[a in choices for a in range(ACTIONS)]))
            if guided:
                picked=max(choices,key=lambda i:(choices[i][0],i==default,-i))
            else:
                picked=default if rng.random()>.25 else rng.choice(tuple(moves))
            state=choices[picked][1]
    bound=value(root)
    value.cache_clear()
    return examples,bound


def train(examples):
    x,y,mask=map(np.asarray,zip(*examples,strict=True))
    rng=np.random.default_rng(TRAIN+9)
    weights=[rng.normal(0,.11,(x.shape[1],32)),np.zeros(32),
             rng.normal(0,.11,(32,ACTIONS)),np.zeros(ACTIONS)]
    first=[np.zeros_like(w) for w in weights]
    second=[np.zeros_like(w) for w in weights]
    tick=0
    curve=[]
    for epoch in range(22):
        for indexes in np.array_split(rng.permutation(len(x)),max(1,len(x)//128)):
            a,b,c=[arr[indexes] for arr in (x,y,mask)]
            w1,b1,w2,b2=weights
            h=np.tanh(a@w1+b1)
            difference=(h@w2+b2-b)*c
            error=2*difference/max(1,c.sum())
            hidden=error@w2.T*(1-h*h)
            gradients=(a.T@hidden,hidden.sum(axis=0),h.T@error,error.sum(axis=0))
            tick+=1
            for n,g in enumerate(gradients):
                first[n]=.9*first[n]+.1*g
                second[n]=.999*second[n]+.001*g*g
                weights[n]-=.003*(first[n]/(1-.9**tick))/(np.sqrt(second[n]/(1-.999**tick))+1e-8)
        w1,b1,w2,b2=weights
        residual=(np.tanh(x@w1+b1)@w2+b2-y)*mask
        curve.append(float((residual**2).sum()/mask.sum()))
    return weights, {"examples":len(examples),"gradient_updates":tick,"loss":curve}


def play(item,script,weights=None, events=None):
    row,_=item
    width,truth,local,opening,_=row
    state=sp.opened(opening,local),1,0,3
    full=(1<<width)-1
    calls=changes=0
    while state[2] < width+1 and not sp.terminal(state[0],full):
        moves,default=candidates(item,state,script)
        picked=default
        if weights is not None and len(moves)>1:
            w1,b1,w2,b2=weights
            x=np.asarray(state_features(row,state,moves,default))
            estimate=np.tanh(x@w1+b1)@w2+b2
            best=max(moves,key=lambda a:(estimate[a],a==default,-a))
            if estimate[best]-estimate[default]>THRESHOLD:
                picked=best
        if events is not None:
            actor=state[1]
            after=next_state(item,state,picked,moves)
            events.append({"actor":actor,"slot":state[2],"action":picked,
                           "accept":after[0][2*actor]&~state[0][2*actor],
                           "exclude":after[0][2*actor+1]&~state[0][2*actor+1]})
            state=after
        else:
            state=next_state(item,state,picked,moves)
        calls+=picked==routing.offers.CHECK
        changes+=picked!=default
    assert all(not (state[0][2*r]&~gold or state[0][2*r+1]&gold) for r,gold in enumerate(truth))
    return sp.terminal(state[0],full),state[2],calls,changes


def score(rows,weights):
    totals,paired=Counter(),Counter()
    for item in rows:
        row,_=item
        tag="agreement" if row[1][0]&row[1][1] else "impasse"
        learned=play(item,BASE,weights)
        for arm,values in [("learned",learned),*((name,play(item,name)) for name in routing.SCRIPTS)]:
            totals[arm,tag,"paths"]+=1
            for k,v in zip(("solved","slots","checks","overrides"),values,strict=True):
                totals[arm,tag,k]+=v
            paired[arm,tag,str(values[0]),str(learned[0])]+=1
    return {"metrics":sp.flatten(totals),"paired":sp.flatten(paired)}


def evaluate():
    familiar=sp.panels((4,5),TRAIN,250,2)+sp.panels((4,5),TRAIN+1,250,3)
    train_rows=(guard.messages(familiar,TRAIN+2,0,0)
                +guard.messages(routing.refit.drop_returns(familiar,TRAIN+3),TRAIN+4,.16,.08))
    rng=random.Random(TRAIN+5)
    examples=[]
    for item in train_rows:
        vectors,_=sample(item,rng)
        examples.extend(vectors)
    weights,training=train(examples)
    fresh=sp.panels((6,7),TEST,900,3)
    cohorts={"clean":guard.messages(fresh,TEST+1,0,0),
             "faults":guard.messages(routing.refit.drop_returns(fresh,TEST+2),TEST+1,.26,.11)}
    return {"training":{**training,"presentations":len(train_rows),"widths":[4,5],"threshold":THRESHOLD},
            "weights":[w.tolist() for w in weights],"heldout":{k:score(v,weights) for k,v in cohorts.items()}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    a=p.parse_args()
    files=(Path(__file__),Path(guard.__file__),guard.HERE/"admit.py",Path(routing.__file__),
           Path(routing.refit.__file__),Path(routing.offers.__file__),Path(sp.__file__),sp.LOOKUP/"lookup.py",
           sp.LOOKUP.parent/"train.py",sp.LOOKUP.parents[1]/"environment.py")
    hashes={str(f.resolve().relative_to(sp.HERE.parents[1])):sha256(f.read_bytes()).hexdigest() for f in files}
    launch,result=a.directory/"launch.json",a.directory/"results.json"
    if a.mode=="replay":
        assert json.loads(launch.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate()))==json.loads(result.read_text())
        print(json.dumps({"verified_hashes":len(hashes),"exact":True}))
        return
    a.directory.mkdir()
    launch.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                  "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                  "run_directory":str(a.directory.resolve()),"command":[sys.executable,*sys.argv],
                                  "numpy":np.__version__,"sha256":hashes},indent=2)+"\n")
    out=evaluate()
    result.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out["training"]))


if __name__=="__main__":
    main()
