"""Ask about a set while letting the respondent select one verified reply."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import new_targets as old

HERE=Path(__file__).resolve().parent
policy=old.policy
FOCUS=policy.focus
SP=policy.sp
OFFER_SET=-3
BASE="set_after_opening"
TRAIN,TEST=162023,857939


def optional_set(item,state):
    row,_=item
    width,_,local,_,_=row
    public,actor,turn,credit=state
    obs,moves,routine=old.ORIGINAL_AVAILABLE(item,state)
    fits=credit&policy.policy.CREDIT and turn+2<=width+1 and obs[6]!=0
    other=1-actor
    viable=local[actor][0]&~(public[1]|public[3]|public[2*other])
    if fits and 2<=viable.bit_count()<=3:
        moves[OFFER_SET]=viable
    return (tuple(moves),*obs[1:],min(viable.bit_count(),4),turn==0),moves,routine


def decision(obs,mode):
    core=obs[:-2]
    if mode in ("set_first",BASE,"set_three"):
        if OFFER_SET in obs[0] and (mode=="set_first" or mode==BASE and not obs[-1]
                                     or mode=="set_three" and obs[-2]==3):
            return OFFER_SET
        return policy.policy.ROUTINE
    return old.decide(core,mode)


def select(candidates,yes,no,offered):
    """Reject index tie-breaking, including ties among unknown candidates."""
    usable=candidates&yes
    if not usable:
        usable=candidates&~(yes|no)
    if usable.bit_count()==1:
        return usable
    pending=usable&offered
    return pending if pending.bit_count()==1 else 0


def transition(item,state,move,actions,routine,recorded=None):
    if move!=OFFER_SET:
        return old.ORIGINAL_TRANSITION(item,state,move,actions,routine,recorded)
    row,_=item
    public,asker,turn,credit=state
    peer=1-asker
    targets=actions[move]
    answer=select(targets,*row[2][peer],public[2*asker])
    if not answer:
        return ((public,asker,turn+2,credit&~policy.policy.CREDIT),False,
                {"asker":asker,"respondent":peer,"slot":turn,"target":0,
                 "request_set":targets,"reply":None,"admitted":False})
    stop,charged,receipt=FOCUS.answer(item,state,policy.policy.MATCH,{policy.policy.MATCH:answer},routine,recorded)
    return stop,charged,{**receipt,"request_set":targets}


def enabled():
    from contextlib import ExitStack
    from unittest.mock import patch
    stack=ExitStack()
    for label,func in (("available",optional_set),("default",decision),("transition",transition),("BASE",BASE)):
        stack.enter_context(patch.object(policy,label,new=func))
    return stack


def decode(result):
    return {(tuple(key[0]),*key[1:]):action for key,action in result["policy"]}


def evaluate():
    rows=SP.panels((4,5),TRAIN,300,2)+SP.panels((4,5),TRAIN+1,300,3)
    wrap=policy.guard.messages
    drop=policy.routing.refit.drop_returns
    train=(wrap(rows,TRAIN+2,0,0),wrap(drop(rows,TRAIN+3),TRAIN+4,.16,.08))
    fresh=SP.panels((6,7),TEST,900,3)
    held={"reliable":wrap(fresh,TEST+1,0,0),"faults":wrap(drop(fresh,TEST+2),TEST+1,.26,.11)}
    with enabled():
        table,journal=policy.fit(train)
        results={}
        for name,items in held.items():
            learned,score=policy.measure(items,BASE,table)
            report={"learned":SP.flatten(score)}
            for arm in ("never","focused_first","scope_first","set_first",BASE,"set_three"):
                before,counts=policy.measure(items,arm,{})
                paired=Counter()
                for source,a,b in zip(items,before,learned,strict=True):
                    l,r=source[0][1]
                    paired["agreement" if l&r else "impasse",str(a[0]),str(b[0])]+=1
                report[arm]={"metrics":SP.flatten(counts),"pairs":SP.flatten(paired)}
            results[name]=report
    return {"training":journal,"policy":[[k,v] for k,v in sorted(table.items())],
            "heldout":results,"cap":"2 or 3 requested packages; at most one focused source check; no requester sign."}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    a=p.parse_args()
    root=SP.HERE.parents[1]
    upstream=HERE/"evidence/target-policy/launch.json"
    addresses=json.loads(upstream.read_text())["sha256"]
    hashes={k:sha256((root/k).read_bytes()).hexdigest() for k in addresses}
    assert hashes==addresses
    hashes[str(Path(__file__).resolve().relative_to(root))]=sha256(Path(__file__).read_bytes()).hexdigest()
    rec,data=a.directory/"launch.json",a.directory/"results.json"
    if a.mode=="replay":
        assert json.loads(rec.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate()))==json.loads(data.read_text())
        print(json.dumps({"hashes":len(hashes),"exact":True}))
        return
    a.directory.mkdir()
    rec.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                               "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                               "run_directory":str(a.directory.resolve()),"command":[sys.executable,*sys.argv],
                               "sha256":hashes},indent=2)+"\n")
    results=evaluate()
    data.write_text(json.dumps(results,indent=2)+"\n")
    print("accepted",len(results["training"]["updates"]),"updates")


if __name__=="__main__":
    main()
