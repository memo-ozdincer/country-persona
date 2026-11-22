"""Learn a shared ordering policy for proposals using complete team outcomes."""
import argparse
from collections import Counter, defaultdict
from itertools import product
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

import canonical_menu as ordering
import trajectory_fit as reference

HERE=Path(__file__).resolve().parent
study,router,sp=ordering.study,ordering.router,reference.sp
FEATURES=("opening","peer_offer","own_offer","peer_offer_unjudged","peer_offer_rejected",
          "peer_checked","own_checked","few_active_packages","one_local_acceptance")
MODES=("peer_near","own_near")
SEEDS={"train":716641,"dev":379103,"test":772637}


def worlds(widths,n,missing,seed):
    rng=random.Random(seed)
    public=tuple(product(range(3),range(2),range(2)))
    results=[]
    for width in widths:
        filled=Counter()
        full=(1<<width)-1
        while min(filled[True],filled[False])<n:
            fields=rng.sample(public,width)
            pools=[sum(1<<i for i,v in enumerate(fields) if v[0]==scope) for scope in range(3)]
            if not all(pools):
                continue
            limits=tuple(sum(mask for mask in pools if rng.random()<.47) for _ in range(2))
            menus=tuple((full^mask)&rng.randint(1,full) for mask in limits)
            if not all(limits) or not all(menus):
                continue
            outcome=bool(menus[0]&menus[1])
            if filled[outcome]>=n:
                continue
            show=[full^sum(1<<i for i in rng.sample(range(width),missing)) for _ in range(2)]
            local=tuple((menu&seen,(full^menu)&seen) for menu,seen in zip(menus,show,strict=True))
            row=(width,menus,local,sp.openings(width,menus,rng),limits)
            results.append((row,tuple(fields)))
            filled[outcome]+=1
    return results


def panels(widths,n,missing,seed):
    rows,fields=zip(*worlds(widths,n,missing,seed),strict=True)
    guard=router.guard
    noisy=router.routing.refit.drop_returns(rows,seed+1)
    return {
        "reliable":list(zip(guard.messages(rows,seed+2,0,0),fields,strict=True)),
        "faults":list(zip(guard.messages(noisy,seed+2,.22,.09),fields,strict=True)),
    }


class RulePolicy:
    def __init__(self,rules=()):
        self.rules=rules
        self.choices=Counter()

    def __call__(self,public,actor,known,slot,credit,menu):
        yes,no=known
        peer=1-actor
        active=((1<<len(menu))-1)&~(public[1]|public[3])
        offered=public[2*peer]&active
        view=tuple(map(bool,(
            slot==0,offered,public[2*actor]&active,offered&~(yes|no),offered&no,
            credit&(ordering.reuse.CACHE<<peer),credit&(ordering.reuse.CACHE<<actor),
            active.bit_count()<=3,(yes&active).bit_count()<=1,
        )))
        for mode,i,v in reversed(self.rules):
            if view[i]==v:
                self.choices[mode]+=1
                return mode
        self.choices["public"]+=1
        return "public"


def score(items,chooser):
    totals,paths=Counter(),[]
    # Reuse one patched context per repeated menu descriptor.
    grouped=defaultdict(list)
    for i,(item,features) in enumerate(items):
        grouped[features].append((i,item))
    for features,panel in grouped.items():
        with ordering.enabled(features,chooser):
            for i,item in panel:
                result=router.play(item,ordering.BASE,{})
                left,right=item[0][1]
                tag="agreement" if left&right else "impasse"
                paths.append((i,result))
                totals[tag,"presentations"]+=1
                for key,value in zip(("solved","slots","checks","questions","answers","scope"),result,strict=True):
                    totals[tag,key]+=value
    return [result for _,result in sorted(paths)],totals


def fit(training,dev):
    choices=[(mode,i,expected) for mode,i,expected in product(MODES,range(len(FEATURES)),(False,True))]
    rules=()
    anchors=[[score(rows,"public")[1] for rows in sets] for sets in (training,dev)]
    reward=lambda metrics:sum(map(reference.quality,metrics))
    previous=tuple(map(reward,anchors))
    journal=[]
    for _ in range(3):
        trials=[]
        best=None
        for change in choices:
            if change in rules:
                continue
            proposal=(*rules,change)
            train=[score(rows,RulePolicy(proposal))[1] for rows in training]
            points=reward(train)
            recorded={"change":change,"train_gain":points-previous[0]}
            if points>previous[0] and protects(anchors[0],train):
                val=[score(rows,RulePolicy(proposal))[1] for rows in dev]
                hold=reward(val)
                passed=hold>=previous[1] and protects(anchors[1],val)
                recorded.update(dev_gain=hold-previous[1],passed=passed)
                if passed and (best is None or (points,hold)>best[0]):
                    best=(points,hold),proposal,train,val
            trials.append(recorded)
        journal.append({"trials":trials})
        if best is None:
            break
        previous,rules,train,val=best
        journal[-1].update(accepted=rules[-1],train=list(map(sp.flatten,train)),dev=list(map(sp.flatten,val)))
    return rules,journal


def protects(reference,after):
    return all(a[k,"solved"]<=b[k,"solved"]
               for a,b in zip(reference,after,strict=True) for k in ("agreement","impasse"))


def evaluate(metrics):
    training=panels((4,5),100,2,SEEDS["train"])
    dev=panels((6,),85,3,SEEDS["dev"])
    tests=panels((7,8),140,3,SEEDS["test"])
    rules,journal=fit(tuple(training.values()),tuple(dev.values()))
    held={}
    for tag,items in tests.items():
        policy=RulePolicy(rules)
        controls=(*((m,m) for m in ("index","public",*MODES)),("learned",policy))
        baseline=score(items,"public")[0]
        for name,chooser in controls:
            decisions,out=score(items,chooser)
            pairs=Counter()
            for (item,_),a,b in zip(items,baseline,decisions,strict=True):
                left,right=item[0][1]
                case="agreement" if left&right else "impasse"
                pairs[case,str(a[0]),str(b[0])]+=1
            held.setdefault(tag,{})[name]={"metrics":sp.flatten(out),"pairs":sp.flatten(pairs)}
        held[tag]["learned"]["ordering_calls"]=policy.choices
    cases={}
    for name,rows in (("myanmar",ordering.myanmar),("mali",lambda i:ordering.mali(metrics,i))):
        chosen=RulePolicy(rules)
        transfer=ordering.evaluate_case(rows(0),chosen)
        rotations={}
        for offset in range(7):
            current=ordering.evaluate_case(rows(offset),RulePolicy(rules))
            assert current==transfer
            rotations[offset]=current["totals"]
        cases[name]={**transfer,"rotations":rotations,"ordering_calls":chosen.choices}
    return {"protocol":{"seeds":SEEDS,"features":FEATURES,
                         "scope":"Public fixture attributes determine stable package comparisons. Both delegates share a routing rule fitted only on synthetic team outcomes. Signed actions and receipt policy are unchanged."},
            "rules":rules,"journal":journal,"heldout":held,"transfer":cases}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    root=HERE.parents[1]
    hashes=study.hashes()
    for path in (Path(__file__),Path(ordering.__file__),Path(reference.__file__),
                 Path(ordering.reuse.__file__),Path(ordering.reuse.defer.__file__),
                 Path(ordering.reuse.singleton_control.__file__),args.metrics,
                 ordering.transfer.FACTORED,ordering.transfer.MYANMAR/"case.json"):
        hashes[str(path.resolve().relative_to(root))]=reference.digest(path)
    launch=args.directory/"launch.json"
    result=args.directory/"results.json"
    metrics=study.mali.load(args.metrics)
    if args.mode=="replay":
        assert study.mali.load(launch)["sha256"]==hashes
        assert json.loads(json.dumps(evaluate(metrics)))==study.mali.load(result)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    record={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
            "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
            "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(record,indent=2)+"\n")
    data=evaluate(metrics)
    result.write_text(json.dumps(data,indent=2)+"\n")
    print({"rules":len(data["rules"])},flush=True)


if __name__=="__main__":
    main()
