"""Allow a private question about a locally acceptable, unpublished package."""
import argparse
from collections import Counter
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
GUARD=HERE.parent/"space/guarded"
sys.path.insert(0,str(GUARD))
import exclusive_query as policy

FIRST,LAST=-1,-2
TRAIN,TEST=32949,796877
START="unannounced_first"
ORIGINAL_BASE=policy.BASE
ORIGINAL_AVAILABLE,ORIGINAL_DEFAULT,ORIGINAL_TRANSITION=policy.available,policy.default,policy.transition


def options(item,current):
    original,moves,ordinary=ORIGINAL_AVAILABLE(item,current)
    state,role,turn,credit=current
    width=item[0][0]
    if credit&policy.policy.CREDIT and turn+2<=width+1 and original[6]!=0:
        peer=1-role
        yes=item[0][2][role][0]
        pending=yes&~(state[1]|state[3]|state[2*peer]|state[2*role])
        if pending:
            moves[FIRST]=pending&-pending
            last=1<<(pending.bit_length()-1)
            if last!=moves[FIRST]:
                moves[LAST]=last
    return (tuple(moves),*original[1:]),moves,ordinary


def decide(state,mode):
    if mode==START and FIRST in state[0]:
        return FIRST
    if mode=="unannounced_last" and FIRST in state[0]:
        return LAST if LAST in state[0] else FIRST
    if mode=="after_opening" and FIRST in state[0] and not state[-1]:
        return FIRST
    if mode in (ORIGINAL_BASE,START,"unannounced_last","after_opening"):
        legal=state[0]
        for direct,scope in ((policy.policy.MATCH,policy.MATCH_SCOPE),(policy.policy.HOLE,policy.HOLE_SCOPE)):
            if direct in legal:
                return scope if scope in legal and (state[2]<=2 or not state[-1]) else direct
        return policy.policy.ROUTINE
    return ORIGINAL_DEFAULT(state,mode)


def step(item,current,move,choices,ordinary,recorded=None):
    if move not in (FIRST,LAST):
        return ORIGINAL_TRANSITION(item,current,move,choices,ordinary,recorded)
    target=choices[move]
    return ORIGINAL_TRANSITION(item,current,policy.policy.MATCH,{policy.policy.MATCH:target},
                               ordinary,recorded)


@contextmanager
def enable():
    with patch.object(policy,"available",new=options),patch.object(policy,"default",new=decide),          patch.object(policy,"transition",new=step),patch.object(policy,"BASE",START):
        yield


def decode(data):
    return {(tuple(k[0]),*k[1:]):v for k,v in data["policy"]}


def evaluate():
    sp,run=policy.sp,policy.guard.messages
    rows=sp.panels((4,5),TRAIN,270,2)+sp.panels((4,5),TRAIN+1,270,3)
    train=(run(rows,TRAIN+2,0,0),run(policy.routing.refit.drop_returns(rows,TRAIN+3),TRAIN+4,.16,.08))
    wide=sp.panels((6,7),TEST,800,3)
    cases={"clean":run(wide,TEST+1,0,0),
           "faults":run(policy.routing.refit.drop_returns(wide,TEST+2),TEST+1,.26,.11)}
    with enable():
        weights,history=policy.fit(train)
        arms={}
        for name,items in cases.items():
            learned,result=policy.measure(items,START,weights)
            summary={"learned":sp.flatten(result)}
            for mode in ("never","focused_first","scope_late","after_opening",START,"unannounced_last"):
                reference,counts=policy.measure(items,mode,{})
                pairs=Counter()
                for item,old,new in zip(items,reference,learned,strict=True):
                    a,b=item[0][1]
                    label="agreement" if a&b else "impasse"
                    pairs[label,str(old[0]),str(new[0])]+=1
                summary[mode]={"metrics":sp.flatten(counts),"pairs":sp.flatten(pairs)}
            arms[name]=summary
    return {"policy":[[k,v] for k,v in sorted(weights.items())],"train":history,"heldout":arms}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    args=p.parse_args()
    source_root=policy.sp.HERE.parents[1]
    recorded=json.loads((GUARD/"evidence/exclusive-query/launch.json").read_text())["sha256"]
    hashes={k:sha256((source_root/k).read_bytes()).hexdigest() for k in recorded}
    assert hashes==recorded
    hashes[str(Path(__file__).resolve().relative_to(source_root))]=sha256(Path(__file__).read_bytes()).hexdigest()
    launch,result=args.directory/"launch.json",args.directory/"results.json"
    if args.mode=="replay":
        assert json.loads(launch.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate()))==json.loads(result.read_text())
        print(json.dumps({"hashes":len(hashes),"exact":True}))
        return
    args.directory.mkdir()
    launch.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                  "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                  "run_directory":str(args.directory.resolve()),"command":[sys.executable,*sys.argv],
                                  "sha256":hashes},indent=2)+"\n")
    output=evaluate()
    result.write_text(json.dumps(output,indent=2)+"\n")
    print("accepted",len(output["train"]["updates"]),"updates")


if __name__=="__main__":
    main()
