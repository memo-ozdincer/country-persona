"""Policy iteration for one role-local verification under a shared action budget."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PARTIAL = HERE.parent
sys.path.insert(0,str(PARTIAL))
from train import COST, ROOT, examples, groups, label, opened, record, terminal

TRAIN = 61419
TEST = 19032
MAX_UPDATES = 16
CHECK = 4


def choices(state, local, role, turn, n, credit, no_check=False):
    full = (1<<n)-1
    yes, no = local[role]
    local_groups = groups(local[role],state,role,full)
    actors = {}
    for idx, bucket in enumerate(local_groups):
        if bucket:
            bit = bucket & -bucket
            after = record(state,role,bit,bool(yes&bit))
            for stay in ((False,) if yes&bit else (False,True)):
                actors[(idx,stay)] = bit,after,role if stay else 1-role
    unknown = full & ~(yes | no | state[1] | state[3])
    peer_offered = unknown & state[2*(1-role)]
    lookup_options=peer_offered or unknown
    if credit and turn<n and lookup_options and not no_check:
        actors[(CHECK,True)] = lookup_options & -lookup_options,state,role
    group=next((g for g in (0,3,1,2) if local_groups[g]), -1)
    if group in (1,3):
        _,after,_=actors[group,False]
        assumed=(group,bool(no & ~(after[1]|after[3])))
    else:
        assumed=group,False
    if (CHECK,True) in actors and group!=0 and (peer_offered or group==-1):
        default=CHECK,True
    else:
        default=assumed
    if (-1,False) not in actors and (default==(-1,False) or not actors):
        actors[-1,False]=0,state,1-role
    if not no_check and (CHECK,True) in actors:
        # A lookup can compete with passing even when it is the only local move.
        if group==-1:
            actors[-1,False]=0,state,1-role
    key=(min(n+1-turn,3),(n+1-turn)-(full&~(state[1]|state[3])).bit_count(),
         tuple(min(b.bit_count(),2) for b in local_groups),bool(peer_offered),
         min(unknown.bit_count(),2),tuple(actors),default)
    return key,actors,default


def transition(entry, private, local, role, credit, move):
    bit, after, next_role = entry
    if move[0]!=CHECK:
        return after,local,next_role,credit
    yes,no=local[role]
    if private[role]&bit:
        yes |= bit
    else:
        no |= bit
    updated=list(local)
    updated[role]=(yes,no)
    return after,tuple(updated),next_role,0


def rollout(n, private, state, local, role, turn, credit, policy, no_check=False):
    checks=0
    for t in range(turn,n+1):
        if terminal(state,(1<<n)-1):
            return True,t-turn,checks
        key, options, default=choices(state,local,role,t,n,credit,no_check)
        move=policy.get(key,default)
        checks+=move[0]==CHECK
        state,local,role,credit=transition(options[move],private,local,role,credit,move)
    return terminal(state,(1<<n)-1),n+1-turn,checks


def play(row, policy, no_check=False):
    n,private,local,opening=row
    return rollout(n,private,opened(opening,local),local,1,0,1,policy,no_check)


def measure(rows, policy, no_check=False):
    sums=Counter()
    results=[]
    for row in rows:
        outcome=label(row)
        certified,cost,lookups=play(row,policy,no_check)
        for key,val in (("presentations",1),("certificates",certified),("slots",cost),("lookups",lookups)):
            sums[outcome,key]+=val
        results.append(certified)
    return sums,results


def effect(rows, policy):
    stats=defaultdict(Counter)
    for n,private,local,opening in rows:
        state,role,credit=opened(opening,local),1,1
        for step in range(n+1):
            if terminal(state,(1<<n)-1):
                break
            key, options, default=choices(state,local,role,step,n,credit)
            move=policy.get(key,default)
            after, known, next_role,next_credit=transition(options[move],private,local,role,credit,move)
            g,c,_=rollout(n,private,after,known,next_role,step+1,next_credit,policy)
            for other, entry in options.items():
                if other==move:
                    continue
                a,x,t,q=transition(entry,private,local,role,credit,other)
                g2,c2,_=rollout(n,private,a,x,t,step+1,q,policy)
                r=stats[key,other]
                r["visits"]+=1
                r["gains"]+=g2 and not g
                r["losses"]+=g and not g2
                r["slots_saved"]+=c-c2
            state, local, role, credit = after, known, next_role, next_credit
    return stats


def flatten(data):
    return {"/".join(k):v for k,v in sorted(data.items())}


def reward(data):
    return sum(data[k,"certificates"]-COST*data[k,"slots"] for k in ("agreement","impasse"))


def fit(rows):
    policy={}
    initial,_=measure(rows,policy)
    current=initial
    history=[]
    for _ in range(MAX_UPDATES):
        estimates=effect(rows,policy)
        candidates=sorted((-(v["gains"]-v["losses"]+COST*v["slots_saved"]),key)
                          for key,v in estimates.items() if v["visits"]>=3)
        accepted=False
        for estimated,(obs,action) in candidates:
            if estimated>=0:
                break
            proposal={**policy,obs:action}
            if action==obs[-1]:
                proposal.pop(obs,None)
            scores,_=measure(rows,proposal)
            if any(scores[k,"certificates"]<current[k,"certificates"] for k in ("agreement","impasse")):
                continue
            if reward(scores)<=reward(current):
                continue
            policy,current=proposal,scores
            history.append({"observation":obs,"action":action,"information_gain":dict(estimates[obs,action]),
                            "metrics":flatten(scores)})
            accepted=True
            break
        if not accepted:
            break
    return policy,{"initial":flatten(initial),"final":flatten(current),"updates":history}


def freeze(policy):
    return [[k,value] for k,value in sorted(policy.items())]


def restore(raw):
    return {(k[0],k[1],tuple(k[2]),k[3],k[4],tuple(map(tuple,k[5])),tuple(k[6])):tuple(a) for k,a in raw}


def compare(rows,policy):
    arms={"no_check":measure(rows,{},True),"scripted_check":measure(rows,{}),
          "learned_check":measure(rows,policy)}
    pairs=Counter()
    for arm, (_,flags) in arms.items():
        for row,a,b in zip(rows,arms["scripted_check"][1],flags,strict=True):
            pairs[arm,label(row),str(a),str(b)]+=1
    return {"metrics":{arm:flatten(val[0]) for arm,val in arms.items()},
            "paired_vs_script":flatten(pairs)}


def dump(path, data):
    path.write_text(json.dumps(data,indent=2)+"\n")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main(output):
    output.mkdir()
    pathlocks=[Path(__file__).resolve(),PARTIAL/"train.py",
               *(ROOT/n for n in ("learn.py","joint.py","environment.py","guard.py"))]
    dump(output/"launch.json",{
        "host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
        "start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
        "sources":{str(p.relative_to(ROOT)):digest(p) for p in pathlocks},
        "train_seed":TRAIN,"test_seed":TEST,"train_widths":[3,4],"test_widths":[5,6],
        "slot_budget":"n+1 including at most one local verification",
    })
    policy,journal=fit(list(examples((3,4),TRAIN)))
    dump(output/"training.json",journal)
    dump(output/"policy.json",freeze(policy))
    print("Accepted updates",len(journal["updates"]),flush=True)
    for n in (5,6):
        report=compare(list(examples((n,),TEST+n,stress=n==6)),policy)
        dump(output/f"heldout-{n}.json",report)
        print(n,report["metrics"],flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    main(p.parse_args().output)
