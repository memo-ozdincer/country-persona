"""Stress-test the frozen check-or-defer policy with unreturned checks."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random

from deferral import fresh, options, restore, step, opened, terminal, label, flatten

SEED = 624037
RETURN_PROBABILITY = 0.8


def replay(row, policy, delivered):
    n, truth, own, first = row
    full = (1 << n)-1
    state, role, credit=opened(first,own),1,1
    tried=missed=0
    for turn in range(n+1):
        if terminal(state,full):
            return True,turn,tried,missed
        key,allowed,default=options(state,own,role,turn,n,credit)
        selected=policy.get(key,default) if True in allowed else False
        if selected:
            tried+=1
            bit=allowed[True][0]
            if not delivered[role]&bit:
                missed+=1
                credit=0
                continue
        state,own,role,credit=step(allowed[selected],truth,own,role,credit,selected)
    return terminal(state,full),n+1,tried,missed


def evaluate(policy):
    rng=random.Random(SEED)
    metrics,paired=Counter(),Counter()
    for row in fresh():
        n=row[0]
        status=tuple(sum(1<<bit for bit in range(n) if rng.random()<RETURN_PROBABILITY) for _ in (0,1))
        label_=label(row)
        trials={name:replay(row,p,status) for name,p in (("script",{}),("learned",policy))}
        for arm,(cert,slots,checks,missed) in trials.items():
            for k,v in (("presentations",1),("certificates",cert),("slots",slots),
                        ("checks",checks),("unreturned",missed)):
                metrics[arm,label_,k]+=v
        paired[label_,str(trials["script"][0]),str(trials["learned"][0])]+=1
    return {"seed":SEED,"return_probability":RETURN_PROBABILITY,
            "metrics":flatten(metrics),"paired":flatten(paired)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("policy",type=Path)
    a=p.parse_args()
    print(json.dumps(evaluate(restore(json.loads(a.policy.read_text()))),indent=2))
