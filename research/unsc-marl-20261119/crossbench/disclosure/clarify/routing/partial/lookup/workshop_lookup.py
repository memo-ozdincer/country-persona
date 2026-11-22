"""Exercise the query policy on recorded UN role outputs and a scoped provider."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

from lookup import CHECK, ROOT, choices, restore, terminal, record
from task_replay import sources
from package_panel import inputs, project
from episode import judge, readout


def transcript(case, first, observed, alternate, private, policy, provider, confirmation=False):
    roles=case["roles"]
    options=[p["id"] for p in case["options"]]
    n=len(options)
    state=(0,0,0,0)
    known=observed
    role,credit=1,2 if confirmation else 1
    claims,events=[],[]

    def disclose(actor,bit,turn):
        nonlocal state,known
        yes,no=known[actor]
        option=options[bit.bit_length()-1]
        if not (bit & (yes|no)):
            events.append({"turn":turn,"role":actor,"option":option,"status":"unknown"})
            return False
        stance="accept" if bit&yes else "exclude"
        raw=json.dumps({"option":option,"stance":stance})
        status,claim=judge(raw,roles[actor],option,bool(private[actor]&bit),f"claim-{len(claims)+1}")
        events.append({"turn":turn,"role":actor,"option":option,"status":status})
        if claim is None:
            updated=list(known)
            updated[actor]=(yes&~bit,no&~bit)
            known=tuple(updated)
            return False
        claims.append(claim)
        state=record(state,actor,bit,stance=="accept")
        return True

    for actor, option in enumerate(first):
        disclose(actor,1<<options.index(option),actor-2)
    for turn in range(n+1):
        if terminal(state,(1<<n)-1):
            break
        offered_unknown = state[2*(1-role)] & ~(known[role][0]|known[role][1]|state[1]|state[3])
        disable=provider=="off" or (confirmation and not offered_unknown)
        key, action_space, default=choices(state,known,role,turn,n,credit,disable)
        if confirmation:
            branch=next((a for a in ((0,False),(2,False),(CHECK,True),(3,False),(1,False))
                         if a in action_space),default)
        else:
            branch=policy.get(key,default)
        bit,_,recipient=action_space[branch]
        if branch[0]==CHECK:
            if provider=="authored":
                value=bool(private[role]&bit)
            else:
                alt_yes,alt_no=alternate[role]
                value=True if bit&alt_yes else False if bit&alt_no else None
            # The verification is private. The public ledger is changed only
            # when an actor subsequently publishes a verified sign.
            status="no_result"
            if value is not None:
                yes,no=known[role]
                updated=list(known)
                updated[role]=(yes|bit,no) if value else (yes,no|bit)
                known=tuple(updated)
                status="resolved"
            events.append({"turn":turn,"role":role,"check":options[bit.bit_length()-1],"status":status})
            credit-=1
            role=recipient
        elif bit:
            role=recipient if disclose(role,bit,turn) else 1-role
        else:
            events.append({"turn":turn,"role":role,"status":"pass"})
            role=1-role
    return {"public":readout(options,roles,claims),"claims":claims,"events":events}


def masks(family, case, manifest):
    compiled=[]
    for actor in (0,1):
        labels=[manifest["decisions"][f"{family}/{actor}/{option['id']}"]["accept"] for option in case["options"]]
        compiled.append(tuple(sum(1<<k for k,v in enumerate(labels) if v is s) for s in (True,False)))
    return tuple(compiled)


def compare(policy, raw, fields, confirmation=False):
    counts, results = Counter(), {}
    for family,case,task in inputs():
        observed=masks(family,case,raw)
        alternate=masks(family,case,fields)
        actual=tuple(project(case["options"],card["expected"]) for card in task["cards"])
        letters=[p["id"] for p in case["options"]]
        openings=product(*([letter for k,letter in enumerate(letters) if mask&(1<<k)] for mask in actual))
        expected="AGREEMENT_POSSIBLE" if task["outcome"]=="agreement" else "IMPASSE"
        for start in openings:
            arms=[
                ("no_lookup",{},"off"),("scripted_authored",{},"authored"),
                ("learned_authored",policy,"authored"),("scripted_model",{},"model"),
                ("learned_model",policy,"model")]
            if confirmation:
                arms.append(("confirmation_model",{},"model"))
            for arm,select,channel in arms:
                details=transcript(case,start,observed,alternate,actual,select,channel,
                                   arm=="confirmation_model")
                counts[(family,arm,"presentations")]+=1
                counts[(family,arm,"certificates")]+=details["public"]["state"]==expected
                counts[(family,arm,"checks")]+=sum("check" in event for event in details["events"])
                counts[(family,arm,"slots")]+=sum(event["turn"]>=0 for event in details["events"])
                results["/".join((family,arm,"".join(start)))]=details
    return {"metrics":{"/".join(k):v for k,v in counts.items()},"paths":results}


def transfer(policy_path, confirmation=False):
    paths,locks=sources()
    policy=restore(json.loads(policy_path.read_text()))
    recorded={k:json.loads(p.read_text()) for k,p in paths.items()}
    return {"input_sha256":locks,"policy_sha256":sha256(policy_path.read_bytes()).hexdigest(),
            **compare(policy,recorded["direct_package"],recorded["field_invariants"],confirmation)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("policy",type=Path)
    p.add_argument("--confirmation",action="store_true")
    a=p.parse_args()
    print(json.dumps(transfer(a.policy,a.confirmation),indent=2))
