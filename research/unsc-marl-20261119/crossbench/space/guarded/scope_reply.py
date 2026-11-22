"""Evaluate scope-backed answers as an extension of focused peer verification."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import focused_query as focused

HERE=Path(__file__).resolve().parent
policy,sp,routing,guard=focused.policy,focused.sp,focused.routing,focused.guard


def reply(item,current,action,options,normal,recorded=None):
    after,checked,event=focused.answer(item,current,action,options,normal,recorded)
    if event is None or not event.get("new_lookup") or event["reply"] is not False:
        return after,checked,event
    row,tape=item
    before,asker,turn,credit=current
    peer=event["respondent"]
    target=event["target"]
    blocked=before[1]|before[3]
    scope=row[-1][peer]&~blocked
    if not (scope&target) or scope.bit_count()<2:
        return after,checked,event
    yes,no=row[2][peer]
    assert not scope&row[1][peer]
    local=list(row[2])
    local[peer]=(yes,no|scope)
    augmented=(*row[:2],tuple(local),*row[3:])
    desired=sp.record(before,peer,scope,False)
    action_set={routing.offers.WAIT:(scope,desired,asker)}
    final,_=guard.settle(augmented,tape,(before,peer,turn+1,credit&~(1<<peer)&~policy.CREDIT),
                        routing.offers.WAIT,action_set,False)
    added=final[0][2*peer+1]&~before[2*peer+1]
    assert final[2:]==after[2:]
    return final,checked,{**event,"scope_mask":scope,"admitted_scope_mask":added,"admitted":bool(added&target)}


def fit():
    prior=HERE/"evidence/focused-query"
    archived=json.loads((prior/"results.json").read_text())
    with patch.object(policy,"advance",side_effect=reply):
        result=policy.evaluate()
    # Compare response capacities in a new width-eight/nine panel without refitting either schedule.
    seed=782943
    cases=sp.panels((8,9),seed,650,4)
    tables={"focused":focused.table(archived["fit"]),"scoped":focused.table(result)}
    panels={"reliable":guard.messages(cases,seed+1,0,0),
            "faults":guard.messages(routing.refit.drop_returns(cases,seed+2),seed+1,.26,.11)}
    comparisons={}
    for name,items in panels.items():
        outcomes={}
        for arm,compiler in (("focused",focused.answer),("scoped",reply)):
            with patch.object(policy,"advance",side_effect=compiler):
                outcomes[arm]=policy.compare(items,tables[arm])
        comparisons[name]=outcomes
    return {"input_sha256":sha256((prior/"results.json").read_bytes()).hexdigest(),
            "training":result,"fresh_width_8_9":comparisons}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("out",type=Path)
    args=p.parse_args()
    prior=HERE/"evidence/focused-query"
    source=sp.HERE.parents[1]
    old=json.loads((prior/"launch.json").read_text())["sha256"]
    hashes={k:sha256((source/k).read_bytes()).hexdigest() for k in old}
    assert hashes==old
    for p in (Path(__file__),prior/"results.json"):
        hashes[str(p.resolve().relative_to(source))]=sha256(p.read_bytes()).hexdigest()
    receipt,result=args.out/"launch.json",args.out/"results.json"
    if args.mode=="replay":
        assert json.loads(receipt.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(fit()))==json.loads(result.read_text())
        print(json.dumps({"verified_hashes":len(hashes),"exact_replay":True}))
        return
    args.out.mkdir()
    receipt.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                  "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                  "run_directory":str(args.out.resolve()),"command":[sys.executable,*sys.argv],
                                  "sha256":hashes},indent=2)+"\n")
    results=fit()
    result.write_text(json.dumps(results,indent=2)+"\n")
    print("accepted",len(results["training"]["train"]["updates"]),"updates")


if __name__=="__main__":
    main()
