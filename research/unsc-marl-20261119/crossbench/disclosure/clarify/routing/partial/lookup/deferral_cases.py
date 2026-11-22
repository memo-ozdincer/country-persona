"""Transfer fixed check-or-defer decisions to recorded UN case evidence."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path

from deferral import options, restore
from workshop_lookup import inputs, judge, masks, project, readout, record, sources, terminal


def replay(case, opening, observed, alternate, truth, fitted, provider):
    names = case["roles"]
    packages = [p["id"] for p in case["options"]]
    width = len(packages)
    full = (1 << width)-1
    state, known, role, credit = (0,0,0,0), list(observed), 1, 1
    claims, events = [], []

    def send(speaker, bit, t):
        nonlocal state
        option=packages[bit.bit_length()-1]
        yes,no=known[speaker]
        if not bit & (yes|no):
            events.append({"slot":t,"role":speaker,"option":option,"status":"unknown"})
            return False
        sign="accept" if yes&bit else "exclude"
        raw=json.dumps({"stance":sign,"option":option})
        outcome,claim=judge(raw,names[speaker],option,bool(truth[speaker]&bit),f"claim-{len(claims)+1}")
        events.append({"slot":t,"role":speaker,"option":option,"status":outcome})
        if claim is None:
            known[speaker]=(yes&~bit,no&~bit)
            return False
        claims.append(claim)
        state=record(state,speaker,bit,sign=="accept")
        return True

    for i,opt in enumerate(opening):
        send(i,1<<packages.index(opt),i-2)
    for t in range(width+1):
        if terminal(state,full):
            break
        key,allowed,default = options(state,known,role,t,width,credit)
        chose=fitted.get(key,default) if True in allowed else False
        bit,_,next_role=allowed[chose]
        if chose:
            y,n=alternate[role]
            answer = bool(truth[role]&bit) if provider=="authored" else (
                True if y&bit else False if n&bit else None)
            status="unknown"
            if answer is not None:
                y,n=known[role]
                known[role]=(y|bit,n) if answer else (y,n|bit)
                status="resolved"
            events.append({"slot":t,"role":role,"checked":packages[bit.bit_length()-1],"status":status})
            credit=0
            role=next_role
        elif bit:
            role=next_role if send(role,bit,t) else 1-role
        else:
            events.append({"slot":t,"role":role,"status":"pass"})
            role=1-role
    return {"readout":readout(packages,names,claims),"claims":claims,"events":events}


def evaluate(policy):
    files,hashes=sources()
    direct=json.loads(files["direct_package"].read_text())
    field=json.loads(files["field_invariants"].read_text())
    counts,records=Counter(),{}
    for family,case,task in inputs():
        observed=masks(family,case,direct)
        alternate=masks(family,case,field)
        truth=tuple(project(case["options"],c["expected"]) for c in task["cards"])
        letters=[o["id"] for o in case["options"]]
        starts=product(*([a for i,a in enumerate(letters) if mask&(1<<i)] for mask in truth))
        required="AGREEMENT_POSSIBLE" if task["outcome"]=="agreement" else "IMPASSE"
        for first in starts:
            for provider in ("model","authored"):
                for arm,rules in (("script",{}),("learned",policy)):
                    row=replay(case,first,observed,alternate,truth,rules,provider)
                    key=family,provider,arm
                    records["/".join((*key,"".join(first)))]=row
                    counts[*key,"certified"]+=row["readout"]["state"]==required
                    counts[*key,"paths"]+=1
                    counts[*key,"slots"]+=sum(x["slot"]>=0 for x in row["events"])
                    counts[*key,"checks"]+=sum("checked" in x for x in row["events"])
    return {"input_sha256":hashes,"metrics":{"/".join(k):v for k,v in counts.items()},"paths":records}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("policy",type=Path)
    a=p.parse_args()
    print(json.dumps(evaluate(restore(json.loads(a.policy.read_text()))),indent=2))
