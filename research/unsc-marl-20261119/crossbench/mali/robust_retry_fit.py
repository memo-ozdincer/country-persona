"""Fit shared retry decisions from the team-return deltas of legal actions."""
import argparse
from collections import Counter
import json
from itertools import combinations
import os
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np

import delayed_reply_fit as episode

HERE=Path(__file__).resolve().parent
sp,base=episode.sp,episode.base
ACTIONS=episode.ACTIONS
THRESHOLDS=(0.,.01,.03,.06,.10)
SEEDS={"train":248189,"validation":762499,"heldout":391057,"archive":490513}


def features(obs):
    return np.asarray((1.,*obs,*(a and b for a,b in combinations(obs,2))),dtype=np.float64)


def utility(result):
    return base.objective.utility(*result[:3])/200


def learn(data):
    fits={}
    for condition,rows in data.items():
        for label in ("agreement","impasse"):
            for i,action in enumerate(ACTIONS[1:],start=1):
                examples=[(features(obs),utility(ends[i])-utility(ends[0]))
                          for kind,obs,ends in rows if kind==label and obs is not None and (i!=1 or obs[5])]
                if not examples:
                    raise ValueError(f"Missing decisions in {condition}/{label}/{action}")
                x,y=map(np.asarray,zip(*examples,strict=True))
                penalty=6*np.eye(x.shape[1])
                penalty[0,0]=1
                weights=np.linalg.solve(x.T@x+penalty,x.T@y)
                fits[condition,label,action]={"weights":weights,"examples":len(examples)}
    return fits


def estimate(obs,fits,conservative):
    if obs is None:
        return 0,0.
    x=features(obs)
    signals=[]
    for i,action in enumerate(ACTIONS[1:],start=1):
        if i==1 and not obs[5]:
            continue
        predicted=[x@r["weights"] for label,r in fits.items() if label[2]==action]
        advantage=min(predicted) if conservative else np.mean(predicted)
        signals.append((float(advantage),i))
    value,chosen=max(signals)
    return chosen,value


def actions_for(rows,fits,conservative):
    observations={obs for _,obs,_ in rows}
    return {obs:estimate(obs,fits,conservative) for obs in observations}


def score(rows,policy):
    counters,pairs=Counter(),Counter()
    for case,obs,paths in rows:
        index=policy(obs)
        result=paths[index]
        counters[case,"presentations"]+=1
        if obs is not None:
            counters[case,"opportunities"]+=1
            counters[case,ACTIONS[index]]+=1
        for name,value in zip(("solved","slots","checks","queries","answers","scope","retries","retry_signs","handoffs"),
                              result,strict=True):
            counters[case,name]+=value
        pairs[case,str(paths[0][0]),str(result[0])]+=1
    return counters,pairs


def chosen(values,threshold):
    def policy(obs):
        action,advantage=values[obs]
        return action if threshold is not None and advantage>threshold else 0
    return policy


def validate(panels,fits,conservative):
    defaults=[score(rows,lambda _:0)[0] for rows in panels.values()]
    baseline=sum(map(base.objective.quality,defaults))
    best=baseline
    tables=[actions_for(rows,fits,conservative) for rows in panels.values()]
    trials=[]
    selected=None
    for margin in THRESHOLDS:
        values=[score(rows,chosen(table,margin))[0] for rows,table in zip(panels.values(),tables,strict=True)]
        value=sum(map(base.objective.quality,values))
        guard=base.synth.protects(defaults,values)
        trials.append({"threshold":margin,"counts":list(map(sp.flatten,values)),
                       "advantage":value-baseline,"guard":guard})
        if guard and value>best:
            best,selected=value,margin
    return selected,trials


def compare(rows,fits,thresholds,previous):
    arms={
        "immediate":lambda _:0,
        "delayed":lambda obs:int(obs is not None and obs[5]),
        "previous_rules":lambda obs:episode.pick(obs,"learned",previous),
        "mean_critic":chosen(actions_for(rows,fits,False),thresholds["mean_critic"]),
        "worst_group_critic":chosen(actions_for(rows,fits,True),thresholds["worst_group_critic"]),
    }
    result={}
    for name,actor in arms.items():
        counts,pairs=score(rows,actor)
        result[name]={"metrics":sp.flatten(counts),"pairs":sp.flatten(pairs)}
    return result


def archived(metrics,fits,thresholds,previous):
    results={}
    for name,source in (("mali",episode.canonical.mali(metrics,0)),("myanmar",episode.canonical.myanmar(0))):
        rows=list(source)
        physical=[item[0] for _,item,_,_,_,_,_ in rows]
        results[name]={}
        for label,p in (("independent",0),("persistent",episode.transport.PERSISTENCE)):
            samples=[]
            for j in range(12):
                tape=episode.transport.delivery(physical,SEEDS["archive"]+j,p)
                samples.extend((item,d,receipt) for item,(_,_,receipt,_,_,_,d) in zip(tape,rows,strict=True))
            results[name][label]=compare(episode.paired(samples),fits,thresholds,previous)
    return results


def evaluate(metrics,previous):
    train=episode.panels((5,6),700,2,SEEDS["train"])
    development=episode.panels((6,),600,3,SEEDS["validation"])
    heldout=episode.panels((7,8),550,3,SEEDS["heldout"])
    fits=learn(train)
    trials={name:validate(development,fits,robust) for name,robust in
            (("mean_critic",False),("worst_group_critic",True))}
    thresholds={name:value[0] for name,value in trials.items()}
    return {"scope":"The shared actor gets no world label or fault regime. Its critics encode team returns learned on four synthetic training groups.",
            "seeds":SEEDS,"critics":{"/".join(k):{**v,"weights":v["weights"].tolist()} for k,v in fits.items()},
            "validation":{k:{"selected":v[0],"trials":v[1]} for k,v in trials.items()},
            "heldout":{k:compare(rows,fits,thresholds,previous) for k,rows in heldout.items()},
            "archive":archived(metrics,fits,thresholds,previous)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    p.add_argument("prior",type=Path)
    args=p.parse_args()
    root=HERE.parents[1]
    load=base.study.mali.load
    digest=base.objective.digest
    hashes=dict(load(HERE/"evidence/delayed-reply/launch.json")["sha256"])
    assert all(digest(root/k)==v for k,v in hashes.items())
    for file in (Path(__file__),args.metrics,args.prior):
        hashes[str(file.resolve().relative_to(root))]=digest(file)
    source=load(args.metrics)
    prior=load(args.prior)["rules"]
    launch=args.directory/"launch.json"
    result=args.directory/"results.json"
    if args.mode=="replay":
        record=load(launch)
        assert record["sha256"]==hashes and record["numpy"]==np.__version__
        assert json.loads(json.dumps(evaluate(source,prior)))==load(result)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    meta={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],"numpy":np.__version__,
          "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
          "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(meta,indent=2)+"\n")
    data=evaluate(source,prior)
    result.write_text(json.dumps(data,indent=2)+"\n")
    print({k:v["selected"] for k,v in data["validation"].items()},flush=True)


if __name__=="__main__":
    main()
