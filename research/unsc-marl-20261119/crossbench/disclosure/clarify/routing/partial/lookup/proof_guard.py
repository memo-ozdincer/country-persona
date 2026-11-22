"""Test whether reserving proof slots prevents lookup-policy regressions."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random

from lookup import TEST, CHECK, choices, transition, examples, label, opened, terminal, flatten, restore

FRESH = 66317
PER_CLASS = 3000


def run(row, policy, guard):
    n, private, own, first=row
    state,role,credit=opened(first,own),1,1
    full=(1<<n)-1
    checks=0
    for t in range(n+1):
        if terminal(state,full):
            return True,t,checks
        key,possible,baseline=choices(state,own,role,t,n,credit)
        move=policy.get(key,baseline)
        unexcluded=full & ~(state[1]|state[3])
        if guard and move[0]==2 and baseline[0] in (1,3,CHECK):
            impossible_remains=unexcluded & state[2*(1-role)] & ~own[role][1]
            confirmed_positive=impossible_remains & own[role][0]
            missing=impossible_remains & ~own[role][0]
            no_possible_impasse=bool(confirmed_positive) or missing.bit_count()>credit
            if n+1-t<=unexcluded.bit_count()+credit and not no_possible_impasse:
                move=baseline
        if guard and move[0] in (1,3) and move[1]:
            _,after,_=possible[move]
            if not (own[role][1] & ~(after[1]|after[3])):
                move=move[0],False
        checks+=move[0]==CHECK
        state,own,role,credit=transition(possible[move],private,own,role,credit,move)
    return terminal(state,full),n+1,checks


def sample():
    generator=random.Random(FRESH)
    groups={"agreement":[],"impasse":[]}
    seen=Counter()
    for row in examples((7,),FRESH,stress=True):
        name=label(row)
        seen[name]+=1
        bucket=groups[name]
        if len(bucket)<PER_CLASS:
            bucket.append(row)
        else:
            index=generator.randrange(seen[name])
            if index<PER_CLASS:
                bucket[index]=row
    return groups["agreement"]+groups["impasse"]


def evaluate(rows,policy):
    metrics,paired=Counter(),Counter()
    for row in rows:
        cls=label(row)
        baseline=run(row,{},False)
        for arm, actual in [("script",baseline),("learned",run(row,policy,False)),
                             ("guarded",run(row,policy,True))]:
            for key,value in (("counts",1),("certificates",actual[0]),("slots",actual[1]),("checks",actual[2])):
                metrics[arm,cls,key]+=value
            paired[arm,cls,str(baseline[0]),str(actual[0])]+=1
    return {"metrics":flatten(metrics),"paired":flatten(paired)}


def audit(policy):
    return {name:evaluate(rows,policy) for name,rows in [
        ("exposed-5",list(examples((5,),TEST+5))),
        ("exposed-6",list(examples((6,),TEST+6,stress=True))),
        ("fresh-7",sample()),
    ]}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("policy",type=Path)
    args=p.parse_args()
    print(json.dumps(audit(restore(json.loads(args.policy.read_text()))),indent=2))
