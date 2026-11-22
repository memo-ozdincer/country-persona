"""Replay one compound receipt through the role-bound decision ledger."""
import argparse
from contextlib import ExitStack
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import target_set as group
import target_transfer

policy,sp=group.policy,group.SP
BASE_TRANSITION=group.transition
GROUP_ENABLED=group.enabled


def transition(item,state,move,actions,routine,recorded=None):
    if move!=group.OFFER_SET:
        return BASE_TRANSITION(item,state,move,actions,routine,recorded)
    row,tape=item
    public,asker,turn,credit=state
    peer=1-asker
    allowed=1<<peer
    yes,no=row[2][peer]
    targets=actions[move]
    target=group.select(targets,yes,no,public[2*asker])
    if not target or target&(yes|no) or not credit&allowed:
        return BASE_TRANSITION(item,state,move,actions,routine,recorded)

    scope=row[-1][peer]&~(public[1]|public[3])
    if recorded is not None:
        sign=recorded[peer].get(target)
    else:
        # A simulated missing receipt supplies neither component.
        sign=bool(target&row[1][peer]) if row[-1][peer] else None
    positive=target if sign is True else 0
    negative=scope|(target if sign is False else 0)
    assert not positive&negative
    public_reply=sp.record(sp.record(public,peer,positive,True),peer,negative,False)
    support=list(row[2])
    support[peer]=yes|positive,no|negative
    augmented=(*row[:2],tuple(support),*row[3:])
    wait=policy.routing.offers.WAIT
    remaining=credit&~allowed&~policy.policy.CREDIT
    after,_=policy.guard.settle(augmented,tape,(public,peer,turn+1,remaining),wait,
                                {wait:(positive|negative,public_reply,asker)},False)
    admitted=bool((after[0][2*peer]|after[0][2*peer+1])&target)
    return after,True,{"asker":asker,"respondent":peer,"slot":turn,"request_set":targets,
                       "target":target,"lookup":"joint_fields","reply":sign,"admitted":admitted,
                       "qualified_acceptance":positive,"qualified_exclusions":negative}


def enabled():
    stack=ExitStack()
    stack.enter_context(GROUP_ENABLED())
    stack.enter_context(patch.object(policy,"transition",new=transition))
    return stack


def digests(archived,live):
    root=group.HERE.parents[1]
    original=group.HERE/"evidence/set-policy/launch.json"
    inputs=json.loads(original.read_text())["sha256"]
    assert all(sha256((root/name).read_bytes()).hexdigest()==value for name,value in inputs.items())
    paths=(original,Path(__file__).resolve(),Path(target_transfer.__file__),
           group.HERE/"evidence/set-policy/results.json",archived.resolve(),live.resolve())
    return {**inputs,**{str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in paths}}


def evaluate(archived,live):
    hashes=digests(archived,live)
    with patch.object(group,"enabled",new=enabled):
        training=group.evaluate()
    fit=group.decode(training)
    transfers={}
    for label,file in (("separate_field_batch",archived),("joint_field_batch",live)):
        transfers[label]=target_transfer.evaluate(file,bundle=True,joint=(enabled,fit))
    return {"scope":"One already defined private mandate. A check may return the selected package sign and scope-backed exclusions. Raw mandate remains role local.",
            "sha256":hashes,"training":training,"transfer":transfers}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("run","replay"))
    parser.add_argument("directory",type=Path)
    parser.add_argument("archived",type=Path)
    parser.add_argument("live",type=Path)
    args=parser.parse_args()
    receipt=args.directory/"routing-launch.json"
    result=args.directory/"routing-results.json"
    hashes=digests(args.archived,args.live)
    if args.mode=="replay":
        assert json.loads(receipt.read_text())["sha256"]==hashes
        data=evaluate(args.archived,args.live)
        assert json.loads(json.dumps(data))==json.loads(result.read_text())
        print(json.dumps({"exact":True,"hashes":len(hashes),"updates":len(data["training"]["training"]["updates"])}))
    else:
        launch={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                "run_directory":str(args.directory.resolve()),"command":[sys.executable,*sys.argv],
                "sha256":hashes}
        with receipt.open("x") as file:
            json.dump(launch,file,indent=2)
            file.write("\n")
        data=evaluate(args.archived,args.live)
        with result.open("x") as file:
            json.dump(data,file,indent=2)
            file.write("\n")
        print("accepted",len(data["training"]["training"]["updates"]),"updates")
