"""Measure sensitivity to peer-history truncation under matched budgets."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0,str(ROOT))
from environment import presentations, record, terminal
from guard import guarded
from joint import committee, restore
from learn import write_json

WIDTH = 6


def local_state(ledger, actor, window):
    if window is None:
        state=(0,0,0,0)
        for role,bit,accepts in ledger:
            state=record(state,role,bit,accepts)
        return state
    if window=="compact":
        state=local_state(ledger,actor,None)
        return state[0],state[1]|state[3],state[2],0
    selected_peer=[i for i,row in enumerate(ledger) if row[0]!=actor][-window:]
    state=(0,0,0,0)
    for i,(role,bit,accepts) in enumerate(ledger):
        if role==actor or i in selected_peer:
            state=record(state,role,bit,accepts)
    return state


def episode(n,world,opening,choose,window):
    state,role,full=opening,1,(1<<n)-1
    ledger=[(0,opening[0],True),(1,opening[2],True)]
    trace,redundant=[],0
    for k in range(n):
        if terminal(state,full):
            break
        local = state if window is None else local_state(ledger,role,window)
        _,moves,pick=choose(world,local,role,k,full)
        bit,_,next_role=moves[pick] if moves else (0,local,1-role)
        yes=bool(world[role]&bit)
        if bit:
            redundant += int(not yes and bool((state[1]|state[3])&bit))
            state=record(state,role,bit,yes)
            ledger.append((role,bit,yes))
        trace.append((role,bit,yes,next_role))
        role=next_role
    return terminal(state,full),trace,redundant


def experiment(policy):
    variants={"script":committee({}),"learned":guarded(policy)}
    modes={"full":None,"one_peer_turn":1,"two_peer_turns":2,"compact":"compact"}
    stats,paired=Counter(),Counter()
    n=WIDTH
    for world,opening in presentations(n):
        category="agreement" if world[0]&world[1] else "impasse"
        for method,choose in variants.items():
            full=episode(n,world,opening,choose,None)
            for label,window in modes.items():
                observed=full if label=="full" else episode(n,world,opening,choose,window)
                ok,trace,red=observed
                if label=="compact":
                    assert observed==full
                for metric,value in (("cases",1),("certified",ok),("slots",len(trace)),("redundant_exclusions",red)):
                    stats[(method,label,category,metric)] += value
                paired[(method,label,category,str(full[0]),str(ok))] += 1
    return {"width":n,"capacity_slots":n,
            "metrics":{"/".join(k):v for k,v in stats.items()},
            "paired":{"/".join(k):v for k,v in paired.items()},
            "compact_matches_full_on_every_path":True}


def main(output):
    output.mkdir()
    path=ROOT/"evidence/joint/policy.json"
    runtime={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
             "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
             "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
             "optimizer_updates":0, "locks":{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest()
                      for p in [Path(__file__).resolve(),path,*(ROOT/x for x in ("environment.py","guard.py","joint.py","learn.py"))]}}
    write_json(output/"launch.json",runtime)
    result=experiment(restore(json.loads(path.read_text())))
    write_json(output/"metrics.json",result)
    for key,v in result["metrics"].items():
        if key.endswith("/certified"):
            print(key,v)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    main(p.parse_args().output)
