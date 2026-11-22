"""Trade the respondent's remaining scope lookup for a focused package check."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import query_peer as policy

sp,guard,routing=policy.sp,policy.guard,policy.routing
HERE=Path(__file__).resolve().parent
ASK_ONLY_ADVANCE=policy.advance
STRESS=611894


def answer(item,current,action,options,normal,recorded=None):
    if action==policy.ROUTINE:
        return ASK_ONLY_ADVANCE(item,current,action,options,normal)
    row,tape=item
    ledger,actor,turn,credits=current
    target=options[action]
    respondent=1-actor
    yes,no=row[2][respondent]
    unknown=not ((yes|no)&target)
    charged=bool(unknown and credits&(1<<respondent))
    if not charged:
        return ASK_ONLY_ADVANCE(item,current,action,options,normal)
    if recorded is None:
        # A nonempty scope receipt represents the available simulator provider.
        response=bool(row[1][respondent]&target) if row[-1][respondent] else None
    else:
        response=recorded[respondent].get(target)
    updated=dict.fromkeys(("accept","exclude"),0)
    if response is not None:
        updated["accept" if response else "exclude"]=target
    copied=list(row[2])
    copied[respondent]=yes|updated["accept"],no|updated["exclude"]
    augmented=(*row[:2],tuple(copied),*row[3:])
    after,_,receipt=ASK_ONLY_ADVANCE((augmented,tape),(ledger,actor,turn,credits&~(1<<respondent)),
                                      action,options,normal)
    return after,True,{**receipt,"new_lookup":True}


def table(data):
    return {(tuple(k[0]),*k[1:]):v for k,v in data["policy"]}


def evaluate():
    path=HERE/"evidence/query/results.json"
    previous=table(json.loads(path.read_text()))
    with patch.object(policy,"advance",side_effect=answer):
        matched=policy.evaluate()
    transfer={}
    fresh=sp.panels((8,9),STRESS,650,4)
    variants={"reliable":guard.messages(fresh,STRESS+1,0,0),
              "faults":guard.messages(routing.refit.drop_returns(fresh,STRESS+2),STRESS+1,.26,.11)}
    for label,cohort in variants.items():
        reference=policy.compare(cohort,previous)
        with patch.object(policy,"advance",side_effect=answer):
            focused=policy.compare(cohort,table(matched))
        transfer[label]={"ask_known_only":reference,"focused":focused}
    return {"fit":matched,"fresh_wider":transfer,
            "scope":"One shared question credit. A focused lookup uses the respondent's existing verification allowance. Response may abstain. No new options or outcome rules."}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    args=p.parse_args()
    previous=HERE/"evidence/query"
    starter=json.loads((previous/"launch.json").read_text())["sha256"]
    root=sp.HERE.parents[1]
    hashes={k:sha256((root/k).read_bytes()).hexdigest() for k in starter}
    assert hashes==starter
    for path in (Path(__file__),previous/"results.json"):
        hashes[str(path.resolve().relative_to(root))]=sha256(path.read_bytes()).hexdigest()
    receipt,result=args.directory/"launch.json",args.directory/"results.json"
    if args.mode=="replay":
        assert json.loads(receipt.read_text())["sha256"]==hashes
        assert json.loads(json.dumps(evaluate()))==json.loads(result.read_text())
        print(json.dumps({"hashes":len(hashes),"fit_and_transfer_replay":True}))
        return
    args.directory.mkdir()
    receipt.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                  "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                  "run_directory":str(args.directory.resolve()),"command":[sys.executable,*sys.argv],
                                  "sha256":hashes},indent=2)+"\n")
    payload=evaluate()
    result.write_text(json.dumps(payload,indent=2)+"\n")
    print("accepted",len(payload["fit"]["train"]["updates"]),"updates")


if __name__=="__main__":
    main()
