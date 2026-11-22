"""Train a shared decentralized actor from terminal team returns with receipt reuse."""
import argparse
from collections import Counter
from contextlib import ExitStack
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import numpy as np

import reuse_receipt as reuse
import trajectory_fit as reference

HERE=Path(__file__).resolve().parent
study,group,policy=reference.study,reference.group,reference.policy
sp=group.SP
BASE=group.BASE
ACTIONS=(-4,-3,0,1,2,3,4)
INDEX={a:i for i,a in enumerate(ACTIONS)}
EPOCHS,BATCH=14,64
SCRIPT_BIAS=1.5
SEED=277513


def local_view(obs,default):
    _,slots,unblocked,offers,peer_offer,peer_credit,routine,early,viable,opening,pending,cached=obs
    return np.asarray([
        1.,slots/4,unblocked/3,offers/2,peer_offer,peer_credit,early,viable/4,opening,pending,cached,
        *(routine==i for i in (-1,0,1,2,3)),
        *(a in obs[0] for a in ACTIONS),*(a==default for a in ACTIONS),
    ],dtype=np.float64)


def enabled():
    stack=ExitStack()
    stack.enter_context(reuse.singleton_enabled())
    base_available,base_default=policy.available,policy.default

    def available(item,state):
        obs,moves,ordinary=base_available(item,state)
        prior_check=bool(state[3]&(reuse.CACHE<<(1-state[1])))
        return (*obs,prior_check),moves,ordinary

    stack.enter_context(patch.object(policy,"available",new=available))
    stack.enter_context(patch.object(policy,"default",new=lambda obs,mode:base_default(obs[:-1],mode)))
    return stack


class Actor:
    def __init__(self,weights,rng=None):
        self.weights=weights
        self.rng=rng
        self.trajectory=[]
        self.overrides=0

    def get(self,obs,default=None):
        if len(obs[0])==1:
            return default
        w1,b1,w2,b2=self.weights
        x=local_view(obs,default)
        h=np.tanh(x@w1+b1)
        logits=h@w2+b2
        logits[INDEX[default]]+=SCRIPT_BIAS
        legal=[INDEX[a] for a in obs[0]]
        if self.rng is None:
            chosen=max(legal,key=lambda i:(logits[i],ACTIONS[i]==default,-i))
        else:
            scores=logits[legal]
            prob=np.exp(scores-max(scores))
            prob/=prob.sum()
            chosen=int(self.rng.choice(legal,p=prob))
            error=np.zeros(len(ACTIONS))
            error[legal]=prob
            error[chosen]-=1
            self.trajectory.append((x,h,error))
        action=ACTIONS[chosen]
        self.overrides+=action!=default
        return action


def adam(weights,gradients,moments,squares,step):
    for w,g,m,v in zip(weights,gradients,moments,squares,strict=True):
        m*=.9
        m+=.1*g
        v*=.999
        v+=.001*g*g
        w-=.007*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8)


def outcome_score(items,weights,mode=BASE):
    actor=Actor(weights) if weights is not None else {}
    trace,counts=policy.measure(items,mode,actor)
    return trace,counts,actor.overrides if weights is not None else 0


def train(training,validation):
    rng=np.random.default_rng(SEED)
    # A zero output head makes the untrained greedy actor equal the script.
    example=((0,1),4,3,1,True,True,1,True,2,True,False,False)
    width=len(local_view(example,0))
    weights=[rng.normal(0,.17,(width,24)),np.zeros(24),
             np.zeros((24,len(ACTIONS))),np.zeros(len(ACTIONS))]
    m=[np.zeros_like(w) for w in weights]
    v=[np.zeros_like(w) for w in weights]
    baseline=np.asarray([reference.utility(*r[:3])/200 for r in outcome_score(training,None)[0]])
    anchors=[outcome_score(rows,None)[1] for rows in validation]
    assert all(outcome_score(rows,weights)[1]==anchor for rows,anchor in zip(validation,anchors,strict=True))
    best=sum(map(reference.quality,anchors))
    protected=[w.copy() for w in weights]
    selected=steps=0
    history=[]
    for epoch in range(1,EPOCHS+1):
        outcomes,actions,overrides=0.,0,0
        order=rng.permutation(len(training))
        for start in range(0,len(order),BATCH):
            batch=order[start:start+BATCH]
            x,h,e=[],[],[]
            for i in batch:
                actor=Actor(weights,rng)
                result=policy.play(training[i],BASE,actor)
                score=reference.utility(*result[:3])/200
                advantage=score-baseline[i]
                outcomes+=score
                overrides+=actor.overrides
                for x_i,h_i,error in actor.trajectory:
                    x.append(x_i)
                    h.append(h_i)
                    e.append(error*advantage)
            if not x:
                continue
            a,b,c=np.asarray(x),np.asarray(h),np.asarray(e)/len(batch)
            d=(c@weights[2].T)*(1-b*b)
            gradients=(a.T@d,d.sum(axis=0),b.T@c,c.sum(axis=0))
            steps+=1
            actions+=len(x)
            adam(weights,gradients,m,v,steps)
        judged=[outcome_score(rows,weights) for rows in validation]
        actual=[value for _,value,_ in judged]
        score=sum(map(reference.quality,actual))
        gate=all(new[k,"solved"]>=old[k,"solved"]
                 for old,new in zip(anchors,actual,strict=True) for k in ("agreement","impasse"))
        if gate and score>best:
            best,selected=score,epoch
            protected=[w.copy() for w in weights]
        history.append({"epoch":epoch,"explored_actions":actions,"sample_overrides":overrides,
                        "sample_reward":outcomes/len(training),"dev_guard":gate,
                        "dev":[sp.flatten(row) for row in actual],
                        "deploy_overrides":[calls for _,_,calls in judged]})
    return {"selected":selected,"steps":steps,"history":history,"train_presentations_per_epoch":len(training),
            "dev_baseline":[sp.flatten(x) for x in anchors]},protected,weights


def evaluate(metrics):
    training=reference.panels((4,5),reference.TRAIN,130,2)
    training=[item for panel in training.values() for item in panel]
    dev=tuple(reference.panels((5,),reference.VALID,125,2).values())
    heldout=reference.panels((6,7),reference.TEST,350,3)
    with enabled():
        fit,protected,last=train(training,dev)
        tests={}
        for condition,items in heldout.items():
            base=outcome_score(items,None)
            scores={}
            for name,weights,mode in (("fixed_after",None,BASE),("fixed_early",None,"set_first"),
                                      ("no_query",None,"never"),("selected",protected,BASE),("last",last,BASE)):
                paths,counts,actions=outcome_score(items,weights,mode)
                paired=Counter()
                for item,before,after in zip(items,base[0],paths,strict=True):
                    left,right=item[0][1]
                    kind="agreement" if left&right else "impasse"
                    paired[kind,str(before[0]),str(after[0])]+=1
                scores[name]={"metrics":sp.flatten(counts),"overrides":actions,"paired_vs_fixed":sp.flatten(paired)}
            tests[condition]=scores

    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    transfer={}
    with patch.object(study.reply,"enabled",new=enabled):
        for label in ("pooled","authored"):
            source=metrics["conditions"][label]
            transfer[label]={}
            for name,w in (("selected",protected),("last",last)):
                actor=Actor(w)
                traces=study.certify(case,menus,source["package"],source["scope"],actor)
                transfer[label][name]={**traces,"overrides":actor.overrides}
    return {"training":fit,"parameters":{name:[w.tolist() for w in weights]
                                         for name,weights in (("selected",protected),("last",last))},
            "heldout":tests,"transfer":transfer}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    root=HERE.parents[1]
    hashes=study.hashes()
    paths=(Path(__file__),Path(reuse.__file__),Path(reference.__file__),Path(reference.defer.__file__),
           Path(reuse.singleton_control.__file__),args.metrics)
    hashes.update({str(f.resolve().relative_to(root)):reference.digest(f) for f in paths})
    launch=args.directory/"launch.json"
    result=args.directory/"results.json"
    metrics=study.mali.load(args.metrics)
    if args.mode=="replay":
        record=study.mali.load(launch)
        assert record["sha256"]==hashes and record["numpy"]==np.__version__
        assert json.loads(json.dumps(evaluate(metrics)))==study.mali.load(result)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    meta={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],"numpy":np.__version__,
          "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
          "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(meta,indent=2)+"\n")
    result_data=evaluate(metrics)
    result.write_text(json.dumps(result_data,indent=2)+"\n")
    print({k:result_data["training"][k] for k in ("selected","steps")},flush=True)


if __name__=="__main__":
    main()
