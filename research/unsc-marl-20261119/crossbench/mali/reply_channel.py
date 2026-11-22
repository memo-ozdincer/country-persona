"""Test retransmission under temporally correlated simulated delivery failures."""
import argparse
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

import retry_reply_fit as base

SEED=112607
LOSS,FLIP,PERSISTENCE=.22,.09,.85


def delivery(rows,seed,persistence):
    rng=random.Random(seed)
    for row in rows:
        width=row[0]
        tape={}
        for role in range(2):
            previous=(0,0)
            for step in range(width+1):
                changes=tuple(sum(1<<i for i in range(width) if rng.random()<rate)
                              for rate in (LOSS,FLIP))
                keep=sum(1<<i for i in range(width) if rng.random()<persistence)
                tape[role,step]=tuple((old&keep)|(new&~keep) for old,new in zip(previous,changes,strict=True)
                                      ) if step else changes
                previous=tape[role,step]
        yield row,tape


def panels(widths,count,missing,seed):
    rows,terms=zip(*base.synth.worlds(widths,count,missing,seed),strict=True)
    pruned=base.router.routing.refit.drop_returns(rows,seed+1)
    return {name:base.paired((item,d,None) for item,d in zip(delivery(pruned,seed+2,p),terms,strict=True))
            for name,p in (("independent",0),("persistent",PERSISTENCE))}


def evaluate(archive):
    train=panels((5,6),450,2,SEED)
    dev=panels((6,),350,3,SEED+5)
    heldout=panels((7,8),400,3,SEED+10)
    first=archive["rules"]
    reranked,journal=base.fit(tuple(train.values()),tuple(dev.values()))
    results={}
    for name,group in heldout.items():
        metrics=base.compare(group,reranked)
        previous,pairs=base.score(group,"learned",first)
        metrics["previous_fit"]={"counts":base.sp.flatten(previous),"pairs_vs_decisive":base.sp.flatten(pairs)}
        results[name]=metrics
    return {"scope":"Only transport changes. Adjacent slots can copy a previous per-package drop/flip bit. A fresh draw preserves the original marginal rates. Verifier availability and package descriptions are held fixed per episode.",
            "seed":SEED,"rates":{"drop":LOSS,"flip":FLIP,"copy_previous":PERSISTENCE},
            "prior_rules":first,"refit_rules":reranked,"fit":journal,"heldout":results}


def transfer(metrics,rules,previous):
    families={"mali":list(base.canonical.mali(metrics,0)),"myanmar":list(base.canonical.myanmar(0))}
    outputs={}
    for family,rows in families.items():
        outputs[family]={}
        original=[item[0] for _,item,_,_,_,_,_ in rows]
        for label,persistence in (("independent",0),("persistent",PERSISTENCE)):
            samples=[]
            for seed in range(SEED+20,SEED+32):
                tape=delivery(original,seed,persistence)
                samples.extend((item,terms,later) for item,(_,_,later,_,_,_,terms)
                               in zip(tape,rows,strict=True))
            paired=base.paired(samples)
            results=base.compare(paired,rules)
            counts,pairs=base.score(paired,"learned",previous)
            results["previous_fit"]={"counts":base.sp.flatten(counts),"pairs_vs_decisive":base.sp.flatten(pairs)}
            outputs[family][label]=results
    return outputs


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("previous",type=Path)
    p.add_argument("--fitted",type=Path)
    p.add_argument("--receipts",type=Path)
    p.add_argument("--run-record",type=Path)
    args=p.parse_args()
    if args.run_record is not None:
        dependencies=(Path(__file__),Path(base.__file__),Path(base.reply.__file__),
                      Path(base.canonical.__file__),Path(base.synth.__file__),args.previous)
        record={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                "directory":str(args.run_record.resolve().parent),"command":[sys.executable,*sys.argv],
                "sha256":{p.name:base.objective.digest(p) for p in dependencies}}
        with args.run_record.open("x") as file:
            json.dump(record,file,indent=2)
            file.write("\n")
    load=base.study.mali.load
    previous=load(args.previous)
    if args.fitted is None:
        data=evaluate(previous)
    else:
        data={"families":transfer(load(args.receipts),load(args.fitted)["refit_rules"],previous["rules"]),
              "archive_sha256":base.objective.digest(args.receipts),
              "fit_sha256":base.objective.digest(args.fitted)}
    data["previous_sha256"]=base.objective.digest(args.previous)
    print(json.dumps(data,indent=2))
