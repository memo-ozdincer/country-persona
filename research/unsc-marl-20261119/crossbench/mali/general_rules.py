"""Fit observation predicates over the same synthetic traces as the exact table."""
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import trajectory_fit as prior

HERE=Path(__file__).resolve().parent
study,group,policy,sp=prior.study,prior.group,prior.policy,prior.sp
DEFER=prior.defer.DEFER
BASE=prior.BASE
CLASSES=prior.CLASSES


@lru_cache(maxsize=None)
def predicates(obs):
    # Conditions refer to features of the current actor's local observation.
    values=tuple(enumerate(obs[1:],start=1))
    return ((),*((x,) for x in values),
            *((a,b) for i,a in enumerate(values) for b in values[i+1:]))


class Rules:
    def __init__(self,rules=()):
        self.rules=rules
        self.calls=Counter()

    def get(self,obs,default=None):
        for action,conditions in reversed(self.rules):
            if action in obs[0] and all(obs[index]==expected for index,expected in conditions):
                self.calls[action]+=1
                return action
        self.calls[default]+=1
        return default


def count(rows,rules,mode=BASE):
    action_rule=Rules(rules)
    outcomes,score=policy.measure(rows,mode,action_rule)
    return outcomes,score,action_rule.calls


def rank(cohorts,teacher,rules):
    guide=defaultdict(Counter)
    for rows,plans in zip(cohorts,teacher,strict=True):
        for item,(bound,solved,sequence) in zip(rows,plans,strict=True):
            if not solved:
                continue
            deployed=Rules(rules)
            actual=prior.utility(*policy.play(item,BASE,deployed)[:3])
            if actual>=bound:
                continue
            # Keep at most one instance of each target action per observation and path.
            for obs,desired in set(sequence):
                if len(obs[0])>1:
                    guide[obs][desired]+=min(bound-actual,200)
    counts=Counter()
    for obs,desired in guide.items():
        fallback=Rules(rules).get(obs,policy.default(obs,BASE))
        for action in obs[0]:
            if action==fallback:
                continue
            delta=desired[action]-desired[fallback]
            for condition in predicates(obs):
                counts[action,condition]+=delta
    return sorted((rule for rule,d in counts.items() if d>0),key=lambda r:(-counts[r],len(r[1]),r)),counts


def learn(training,development,teacher):
    rules=()
    anchors=[tuple(count(rows,rules)[1] for rows in split) for split in (training,development)]
    reward,validation=(sum(map(prior.quality,split)) for split in anchors)
    journal=[]
    for _ in range(6):
        ranked,potential=rank(training,teacher,rules)
        pool=tuple(dict.fromkeys(ranked[:18]+[r for r in ranked if r[0]==DEFER][:18]))
        trials=[]
        best=None
        for rule in pool:
            update=(*rules,rule)
            metrics=tuple(count(rows,update)[1] for rows in training)
            score=sum(map(prior.quality,metrics))
            allowed=score>reward and all(
                new[k,"solved"]>=start[k,"solved"]
                for start,new in zip(anchors[0],metrics,strict=True) for k in CLASSES)
            info={"rule":rule,"potential":potential[rule],"train_gain":score-reward}
            if allowed:
                dev=tuple(count(rows,update)[1] for rows in development)
                held=sum(map(prior.quality,dev))
                passed=held>=validation and all(
                    new[k,"solved"]>=start[k,"solved"]
                    for start,new in zip(anchors[1],dev,strict=True) for k in CLASSES)
                info.update(validation_gain=held-validation,guard=passed)
                rank_=(score,held)
                if passed and (best is None or rank_>best[0]):
                    best=rank_,update,metrics,dev
            trials.append(info)
        turn={"candidates":trials}
        journal.append(turn)
        if best is None:
            break
        (reward,validation),rules,metrics,dev=best
        turn.update(accepted=rules[-1],train=[sp.flatten(t) for t in metrics],
                    validation=[sp.flatten(t) for t in dev])
    return rules,journal


def test(metrics,archive):
    training=tuple(prior.panels((4,5),prior.TRAIN,130,2).values())
    validation=tuple(prior.panels((5,),prior.VALID,125,2).values())
    heldout=prior.panels((6,7),prior.TEST,350,3)
    with prior.defer.enabled():
        teacher=[[prior.plan(item) for item in rows] for rows in training]
        rules,journal=learn(training,validation,teacher)
        simple={k:values for k,values in archive["heldout"].items()}
        measured={}
        for name,rows in heldout.items():
            _,counts,calls=count(rows,rules)
            measured[name]={"generalized":{"metrics":sp.flatten(counts),"actions":calls},
                            **simple[name]}

    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    replay={}
    with patch.object(study.reply,"enabled",new=prior.defer.enabled):
        for label in ("pooled","authored"):
            source=metrics["conditions"][label]
            shared=Rules(rules)
            result=study.certify(case,menus,source["package"],source["scope"],shared)
            replay[label]={**result,"actual_actions":shared.calls}
    return {"protocol":"Synthetic team reward and the same train, validation and test episodes as the exact table. Rules choose actions from local features; no Mali receipts enter fitting.",
            "rules":rules,"journal":journal,"heldout":measured,"mali":replay}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    known=HERE/"evidence/trajectory-fit"
    archive=known/"results.json"
    hashes={**study.hashes(),"deferral":prior.digest(Path(prior.defer.__file__)),
            "trajectory":prior.digest(Path(prior.__file__)),"mali_receipts":prior.digest(args.metrics),
            "stepwise":prior.digest(HERE/"evidence/joint-transfer/defer-fit.json")}
    assert hashes==study.mali.load(known/"launch.json")["sha256"]
    hashes.update(rules=prior.digest(Path(__file__)),prior_results=prior.digest(archive))
    launch=args.directory/"launch.json"
    results=args.directory/"results.json"
    metrics=study.mali.load(args.metrics)
    if args.mode=="replay":
        assert study.mali.load(launch)["sha256"]==hashes
        assert json.loads(json.dumps(test(metrics,study.mali.load(archive))))==study.mali.load(results)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    identity={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
              "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
              "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(identity,indent=2)+"\n")
    data=test(metrics,study.mali.load(archive))
    results.write_text(json.dumps(data,indent=2)+"\n")
    print({"accepted_rules":len(data["rules"])},flush=True)


if __name__=="__main__":
    main()
