"""Allow known evidence to be published before spending the scope-check credit."""
import argparse
from collections import Counter
from contextlib import ExitStack
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import joint_bound
import joint_transfer as study

group=study.group
policy=group.policy
DEFER=-4
OFFERS=policy.routing.offers
COMPOUND_ENABLED=study.reply.enabled


def available(item,state):
    obs,moves,routine=group.optional_set(item,state)
    action,_=routine
    if action==OFFERS.CHECK:
        moves[DEFER]=None
    public,actor,_,_=state
    yes,no=item[0][2][actor]
    pending=public[2*(1-actor)]&~(public[1]|public[3]|yes|no)
    return (tuple(moves),*obs[1:],bool(pending)),moves,routine


def choose(obs,mode):
    base=obs[:-1]
    if mode in ("defer_opening","defer_pending"):
        default=group.decision(base,group.BASE)
        if default==policy.policy.ROUTINE and DEFER in obs[0]:
            if mode=="defer_opening" and base[-1] or mode=="defer_pending" and obs[-1]:
                return DEFER
        return default
    return group.decision(base,mode)


def step(item,state,move,options,routine,recorded=None):
    if move==DEFER:
        action,ordinary=routine
        assert action==OFFERS.CHECK
        return study.reply.transition(item,state,policy.policy.ROUTINE,options,(OFFERS.WAIT,ordinary),recorded)
    return study.reply.transition(item,state,move,options,routine,recorded)


def enabled():
    stack=ExitStack()
    stack.enter_context(COMPOUND_ENABLED())
    for label,fn in (("available",available),("default",choose),("transition",step)):
        stack.enter_context(patch.object(policy,label,new=fn))
    return stack


def project(metrics):
    """Start from the same signed openings, evidence and roles as the frozen archive."""
    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    values={"conditions":{}}
    with patch.object(study.reply,"enabled",new=enabled):
        for name in ("authored","archived","stable","pooled"):
            condition=metrics["conditions"][name]
            values["conditions"][name]={**condition,**study.certify(
                case,menus,condition["package"],condition["scope"],{})}
        bound=joint_bound.measure(values)
    return bound


def fit_and_transfer(metrics):
    with patch.object(group,"enabled",new=enabled):
        result=group.evaluate()
    fitted=group.decode(result)
    sp=group.SP
    base=sp.panels((6,7),group.TEST,900,3)
    wrap=policy.guard.messages
    cohorts={"reliable":wrap(base,group.TEST+1,0,0),
             "faults":wrap(policy.routing.refit.drop_returns(base,group.TEST+2),group.TEST+1,.26,.11)}
    controls={}
    for name,items in cohorts.items():
        policies={}
        with enabled():
            learned=policy.measure(items,group.BASE,fitted)[0]
            for mode in ("defer_opening","defer_pending"):
                baseline,totals=policy.measure(items,mode,{})
                pairs=Counter()
                for item,before,after in zip(items,baseline,learned,strict=True):
                    left,right=item[0][1]
                    kind="agreement" if left&right else "impasse"
                    pairs[kind,str(before[0]),str(after[0])]+=1
                policies[mode]={"totals":sp.flatten(totals),"pairs":sp.flatten(pairs)}
        controls[name]=policies

    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    transfers={}
    with patch.object(study.reply,"enabled",new=enabled):
        for name in ("pooled","authored"):
            d=metrics["conditions"][name]
            transfers[name]=study.certify(case,menus,d["package"],d["scope"],fitted)
    return {"fit":result,"fixed_deferral_controls":controls,"transfer":transfers}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics",type=Path)
    parser.add_argument("--fit",choices=("run","replay"))
    parser.add_argument("--directory",type=Path)
    args=parser.parse_args()
    metrics=study.mali.load(args.metrics)
    if not args.fit:
        out=project(metrics)
        out["input_sha256"]=sha256(args.metrics.read_bytes()).hexdigest()
        out["scope"]="Clairvoyant upper bound with costed ordinary disclosure as an explicit alternative to the automatic scope check."
        print(json.dumps(out,indent=2))
    else:
        hashes={**study.hashes(),"deferral":sha256(Path(__file__).read_bytes()).hexdigest(),
                "mali_receipts":sha256(args.metrics.read_bytes()).hexdigest()}
        launch=args.directory/"defer-launch.json"
        results=args.directory/"defer-fit.json"
        if args.fit=="run":
            receipt={"host":socket.gethostname(),"pid":os.getpid(),"gpu_uuids":[],"device":"CPU",
                     "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                     "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
            with launch.open("x") as file:
                json.dump(receipt,file,indent=2)
                file.write("\n")
            result=fit_and_transfer(metrics)
            with results.open("x") as file:
                json.dump(result,file,indent=2)
                file.write("\n")
            print("accepted",len(result["fit"]["training"]["updates"]),"updates")
        else:
            assert json.loads(launch.read_text())["sha256"]==hashes
            result=fit_and_transfer(metrics)
            assert json.loads(json.dumps(result))==json.loads(results.read_text())
            print(json.dumps({"exact":True,"hashes":len(hashes),"updates":len(result["fit"]["training"]["updates"])}))
