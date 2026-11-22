"""Test whether training on more deferral-dependent simulations improves transfer."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import trajectory_fit as fit

HERE=Path(__file__).resolve().parent
policy,study,group=fit.policy,fit.study,fit.group
DEFER=fit.defer.DEFER
TRAIN,DEV,TEST=411631,709819,983809
PER_GROUP,QUOTA=85,18


def case_class(item):
    l,r=item[0][1]
    return "agreement" if l&r else "impasse"


def dependency(items):
    plans=[fit.plan(item) for item in items]
    available=policy.available

    def without_deferral(item,state):
        obs,moves,ordinary=available(item,state)
        if DEFER in moves:
            moves.pop(DEFER)
            obs=(tuple(moves),*obs[1:])
        return obs,moves,ordinary

    with patch.object(policy,"available",new=without_deferral):
        limit=[fit.plan(item)[1] for item in items]
    return plans,[sum(a==DEFER for _,a in p[2]) if p[1] and not old else 0
                  for p,old in zip(plans,limit,strict=True)]


def samples(items,depth,enhance):
    groups=defaultdict(list)
    for i,item in enumerate(items):
        groups[item[0][0],case_class(item)].append(i)
    picked=[]
    for batch in groups.values():
        front=[i for i in batch if depth[i]>=3][:QUOTA] if enhance else []
        rest=[i for i in batch if i not in front][:PER_GROUP-len(front)]
        picked.extend(front+rest)
    return sorted(picked)


def evaluate(metrics):
    with fit.defer.enabled():
        train=fit.panels((4,5,6),TRAIN,175,2)
        development=tuple(fit.panels((6,),DEV,125,3).values())
        tested=fit.panels((7,8),TEST,200,3)
        data=[(items,*dependency(items)) for items in train.values()]
        test_depth={name:dependency(items)[1] for name,items in tested.items()}
        weights,reports={},{}
        for arm,enrich in (("uniform",False),("enriched",True)):
            split=[]
            stats=[]
            for items,plans,depth in data:
                ids=samples(items,depth,enrich)
                stats.append(dict(Counter(depth[i] for i in ids)))
                split.append(([items[i] for i in ids],[plans[i] for i in ids]))
            w,log=fit.fit([s[0] for s in split],development,[s[1] for s in split],True)
            weights[arm]=w
            reports[arm]={"counts_by_required_plan_deferrals":stats,
                          "weights":[[k,a] for k,a in sorted(w.items())],**log}
        held={}
        for name,items in tested.items():
            scored = {arm:fit.measure(items,w,mode) for arm,mode,w in (
                ("after_opening",group.BASE,{}),("early","set_first",{}),
                ("no_query","never",{}),
                *((arm,group.BASE,w) for arm,w in weights.items()),
            )}
            held[name]={}
            for arm,(outcomes,counts,actions) in scored.items():
                paired=Counter()
                for item,before,after,depth in zip(items,scored["uniform"][0],outcomes,test_depth[name],strict=True):
                    difficulty="multiple_deferrals" if depth>=3 else "other"
                    paired[difficulty,case_class(item),str(before[0]),str(after[0])]+=1
                held[name][arm]={"metrics":group.SP.flatten(counts),"actions":actions,
                                 "pairs_vs_uniform":group.SP.flatten(paired)}
    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    results={}
    with patch.object(study.reply,"enabled",new=fit.defer.enabled):
        for label in ("pooled","authored"):
            source=metrics["conditions"][label]
            results[label]={}
            for arm,weights_ in weights.items():
                table=fit.Table(weights_)
                out=study.certify(case,menus,source["package"],source["scope"],table)
                results[label][arm]={**out,"actions":table.actions}
    return {"protocol":{"train":TRAIN,"validation":DEV,"test":TEST,
                        "quota":QUOTA,"per_width_class_cohort":PER_GROUP,
                        "depth":"Zero unless all no-deferral paths fail. Otherwise count deferrals in the exact highest-utility witness.",
                        "candidate_fit":"Matched search, reward, validation and held-out episodes. Training stratified by width and outcome class."},
            "fit":reports,"heldout":held,"mali":results}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    root=HERE.parents[1]
    previous=study.mali.load(HERE/"evidence/trajectory-fit/launch.json")["sha256"]
    hashes={**study.hashes(),"trajectory":fit.digest(Path(fit.__file__)),
            "deferral":fit.digest(Path(fit.defer.__file__)),
            "mali_receipts":fit.digest(args.metrics),
            "stepwise":fit.digest(HERE/"evidence/joint-transfer/defer-fit.json")}
    assert previous==hashes
    hashes[str(Path(__file__).resolve().relative_to(root))]=sha256(Path(__file__).read_bytes()).hexdigest()
    metrics=study.mali.load(args.metrics)
    launch=args.directory/"launch.json"
    results=args.directory/"results.json"
    if args.mode=="replay":
        assert study.mali.load(launch)["sha256"]==hashes
        assert json.loads(json.dumps(evaluate(metrics)))==study.mali.load(results)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    record={"host":socket.gethostname(),"pid":os.getpid(),"gpu_uuids":[],"device":"CPU",
            "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
            "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(record,indent=2)+"\n")
    outcome=evaluate(metrics)
    results.write_text(json.dumps(outcome,indent=2)+"\n")
    print({a:len(r["accepted"]) for a,r in outcome["fit"].items()},flush=True)


if __name__=="__main__":
    main()
