"""Compare local policy updates proposed from complete synthetic team trajectories."""
import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import defer_scope as defer

study,group,policy=defer.study,defer.group,defer.policy
sp=group.SP
TRAIN,VALID,TEST=732793,919493,22841
CLASSES=("agreement","impasse")
BASE=group.BASE
HERE=Path(__file__).resolve().parent


def panels(widths,seed,per_class,missing):
    rows=sp.panels(widths,seed,per_class,missing)
    wrap=policy.guard.messages
    noisy=policy.routing.refit.drop_returns(rows,seed+1)
    return {"reliable":wrap(rows,seed+2,0,0),"faults":wrap(noisy,seed+2,.22,.09)}


def utility(solved,slots,checks):
    # Same reward as the earlier fitted table, in units of 0.005.
    assert (sp.COST,sp.CHECK_COST)==(.015,.005)
    return 200*solved-3*slots-checks


def quality(counts):
    return sum(utility(counts[k,"solved"],counts[k,"slots"],counts[k,"checks"]) for k in CLASSES)


def plan(item):
    width,_,local,opening,_=item[0]
    full=(1<<width)-1

    @lru_cache(maxsize=None)
    def solve(state):
        public,_,slot,_=state
        terminal=sp.terminal(public,full)
        if terminal or slot>=width+1:
            return utility(terminal,slot,0),terminal,()
        obs,moves,normal=policy.available(item,state)
        default=policy.default(obs,BASE)
        best=None
        for action in (default,*(a for a in moves if a!=default)):
            after,checked,_=policy.transition(item,state,action,moves,normal)
            remaining,success,path=solve(after)
            candidate=remaining-int(checked),success,((obs,action),*path)
            if best is None or candidate[0]>best[0]:
                best=candidate
        return best

    try:
        return solve((sp.opened(opening,local),1,0,7))
    finally:
        solve.cache_clear()


class Table(dict):
    def __init__(self,weights):
        super().__init__(weights)
        self.actions=Counter()

    def get(self,key,default=None):
        action=super().get(key,default)
        self.actions[action]+=1
        return action


def candidates(training,plans,model,bundled):
    values=Counter()
    for rows,guides in zip(training,plans,strict=True):
        for item,(bound,solved,path) in zip(rows,guides,strict=True):
            if not solved:
                continue
            actual=utility(*policy.play(item,BASE,model)[:3])
            if actual>=bound:
                continue
            choices=dict(path)
            if any(choices[k]!=a for k,a in path):
                continue
            edits=tuple(sorted((k,a) for k,a in choices.items()
                               if a!=model.get(k,policy.default(k,BASE))))
            if not edits:
                continue
            patches=(edits,) if bundled else tuple((edit,) for edit in edits)
            for proposed in patches:
                values[proposed]+=bound-actual
    return values


def measure(rows,weights,mode=BASE):
    table=Table(weights)
    outcomes,counts=policy.measure(rows,mode,table)
    return outcomes,counts,table.actions


def fit(training,validation,plans,bundled):
    weights={}
    anchor_train=[measure(rows,weights)[1] for rows in training]
    anchor_val=[measure(rows,weights)[1] for rows in validation]
    start=sum(map(quality,anchor_train))
    start_val=sum(map(quality,anchor_val))
    accepted=[]
    tested=[]
    for _ in range(6):
        options=candidates(training,plans,weights,bundled)
        ranks=sorted(options,key=lambda patch:(-options[patch],patch))
        # Reserve half of the search for candidates that actually exercise the new action.
        search=list(dict.fromkeys([p for p in ranks if any(a==defer.DEFER for _,a in p)][:16]+ranks[:16]))
        best=None
        for edits in search:
            proposal={**weights,**dict(edits)}
            train_summary=[measure(rows,proposal)[1] for rows in training]
            score=sum(map(quality,train_summary))
            if score<=start or any(new[k,"solved"]<old[k,"solved"]
                                   for old,new in zip(anchor_train,train_summary,strict=True) for k in CLASSES):
                tested.append({"edits":edits,"gain":score-start,"accepted_for_validation":False})
                continue
            val_summary=[measure(rows,proposal)[1] for rows in validation]
            val_score=sum(map(quality,val_summary))
            passed=val_score>=start_val and all(
                new[k,"solved"]>=old[k,"solved"]
                for old,new in zip(anchor_val,val_summary,strict=True) for k in CLASSES
            )
            tested.append({"edits":edits,"gain":score-start,"validation_gain":val_score-start_val,
                           "accepted_for_validation":True,"passes_validation":passed})
            if passed and (best is None or score>best[0]):
                best=score,val_score,proposal,edits,train_summary,val_summary
        if best is None:
            break
        start,start_val,weights,edits,train_summary,val_summary=best
        accepted.append({"edits":edits,"teacher_gain":options[edits],
                         "train":[sp.flatten(d) for d in train_summary],
                         "validation":[sp.flatten(d) for d in val_summary]})
    return weights,{"accepted":accepted,"tested":tested}


def evaluate(metrics):
    training=tuple(panels((4,5),TRAIN,130,2).values())
    validation=tuple(panels((5,),VALID,125,2).values())
    tests=panels((6,7),TEST,350,3)
    with defer.enabled():
        plans=[[plan(item) for item in rows] for rows in training]
        studies={name:fit(training,validation,plans,name=="trajectory")
                 for name in ("singleton","trajectory")}
        previous=study.mali.load(HERE/"evidence/joint-transfer/defer-fit.json")["fit"]
        weights={name:w for name,(w,j) in studies.items()}
        weights["prior_stepwise"]=group.decode(previous)
        arms={
            "after_opening":(BASE,{}),"early":("set_first",{}),"no_query":("never",{}),
            "defer_opening":("defer_opening",{}),"defer_pending":("defer_pending",{}),
            **{key:(BASE,value) for key,value in weights.items()},
        }
        held={}
        for name,items in tests.items():
            scores={key:measure(items,weights,mode) for key,(mode,weights) in arms.items()}
            paired={}
            for control,(out,_,_) in scores.items():
                pairs=Counter()
                for item,a,b in zip(items,out,scores["trajectory"][0],strict=True):
                    left,right=item[0][1]
                    label="agreement" if left&right else "impasse"
                    pairs[label,str(a[0]),str(b[0])]+=1
                paired[control]=sp.flatten(pairs)
            held[name]={k:{"metrics":sp.flatten(m),"actions":a,"paired_vs_trajectory":paired[k]}
                        for k,(_,m,a) in scores.items()}

    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    transfers={}
    with patch.object(study.reply,"enabled",new=defer.enabled):
        for label in ("pooled","authored"):
            source=metrics["conditions"][label]
            transfers[label]={}
            for name,w in weights.items():
                meter=Table(w)
                traces=study.certify(case,menus,source["package"],source["scope"],meter)
                transfers[label][name]={**traces,"actions":meter.actions}
    return {"protocol":{
        "train":TRAIN,"validation":VALID,"test":TEST,
        "scope":"Full-information search proposes updates on synthetic training only. Each realized update is accepted on team return and class guards. Test routing uses only local observation.",
        "trajectories":len(training[0])+len(training[1]),
        "solvable":[sum(success for _,success,_ in p) for p in plans]},
        "policies":{name:{"rules":[[k,v] for k,v in sorted(w.items())],**j} for name,(w,j) in studies.items()},
        "heldout":held,"transfer":transfers}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("output",type=Path)
    p.add_argument("metrics",type=Path)
    a=p.parse_args()
    prior=HERE/"evidence/joint-transfer"
    hashes={**study.hashes(),"deferral":digest(Path(defer.__file__)),
            "trajectory":digest(Path(__file__)),"mali_receipts":digest(a.metrics),
            "stepwise":digest(prior/"defer-fit.json")}
    recorded=study.mali.load(prior/"defer-launch.json")["sha256"]
    assert all(hashes[k]==v for k,v in recorded.items())
    result=a.output/"results.json"
    launch=a.output/"launch.json"
    metrics=study.mali.load(a.metrics)
    if a.mode=="replay":
        assert study.mali.load(launch)["sha256"]==hashes
        assert json.loads(json.dumps(evaluate(metrics)))==study.mali.load(result)
        print(json.dumps({"hashes":len(hashes),"exact":True}))
        return
    a.output.mkdir()
    meta={"host":socket.gethostname(),"pid":os.getpid(),"gpu_uuids":[],"device":"CPU",
          "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
          "command":[sys.executable,*sys.argv],"run_directory":str(a.output.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(meta,indent=2)+"\n")
    outcome=evaluate(metrics)
    result.write_text(json.dumps(outcome,indent=2)+"\n")
    print({k:len(v["accepted"]) for k,v in outcome["policies"].items()},flush=True)


if __name__=="__main__":
    main()
