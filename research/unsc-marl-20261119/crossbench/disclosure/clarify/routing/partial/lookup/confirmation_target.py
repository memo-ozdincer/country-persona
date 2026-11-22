"""Rank local check targets with recorded model scores on a declared confirmation task."""
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

from lookup import CHECK, choices, terminal, record
from workshop_lookup import inputs, judge, masks, project, readout, sources

SOURCE = Path(__file__).resolve().parents[6]/"judge/entailment/package-evidence/predictions.jsonl"


def margins(path):
    chunks=defaultdict(list)
    for row in map(json.loads,path.read_text().splitlines()):
        a,b=row["label_logits"]
        key=row["id"].rsplit("/",1)[0]
        chunks[key].append(a-b if row["support_code"]=="A" else b-a)
    assert all(len(items)==2 for items in chunks.values())
    return {k:sum(v)/len(v) for k,v in chunks.items()}


def rollout(case, opening, start, alternate, truth, scores,
            target_mode, max_checks=1, forced=None):
    labels=[p["id"] for p in case["options"]]
    roles=case["roles"]
    n=len(labels)
    full=(1<<n)-1
    public,known,credit,role=(0,0,0,0),list(start),max_checks,1
    log, claims=[],[]
    first_targets=None

    def send(speaker, bit, t):
        nonlocal public
        yes,no=known[speaker]
        opt=labels[bit.bit_length()-1]
        if not bit & (yes|no):
            log.append({"turn":t,"role":speaker,"option":opt,"status":"unknown"})
            return False
        raw=json.dumps({"option":opt,"stance":"accept" if yes&bit else "exclude"})
        status,evid=judge(raw,roles[speaker],opt,bool(truth[speaker]&bit),f"claim-{len(claims)+1}")
        log.append({"turn":t,"role":speaker,"option":opt,"status":status})
        if evid is None:
            known[speaker]=(yes&~bit,no&~bit)
            return False
        claims.append(evid)
        public=record(public,speaker,bit,bool(yes&bit))
        return True

    for i,name in enumerate(opening):
        send(i,1<<labels.index(name),i-2)
    for t in range(n+1):
        if terminal(public,full):
            break
        yes,no=known[role]
        unknown=full & ~(yes|no|public[1]|public[3])
        peer=unknown & public[2*(1-role)]
        _, actions, default=choices(public,known,role,t,n,credit,not peer)
        # All arms use the same confirmation-oriented disclosure ordering.
        chosen=next((key for key in ((0,False),(2,False),(CHECK,True),(3,False),(1,False))
                     if key in actions), default)
        bit,_,who=actions[chosen]
        if chosen[0]==CHECK:
            candidates=[i for i in range(n) if unknown & (1<<i)]
            if first_targets is None:
                first_targets=[labels[i] for i in candidates]
            if forced is not None:
                assert forced in first_targets and max_checks==1
                bit=1<<labels.index(forced)
            elif target_mode=="score":
                strongest=max(candidates,key=lambda i:(scores[role][i],bool(peer&(1<<i)),-i))
                bit=1<<strongest
            no_look, yes_look=alternate[role][1],alternate[role][0]
            result=True if bit&yes_look else False if bit&no_look else None
            if result is not None:
                known[role]=(yes|bit,no) if result else (yes,no|bit)
            picked=bit.bit_length()-1
            log.append({"turn":t,"role":role,"checked":labels[picked],
                        "score":scores[role][picked],"status":"resolved" if result is not None else "unknown"})
            credit-=1
            role=who
        elif bit:
            role=who if send(role,bit,t) else 1-role
        else:
            log.append({"turn":t,"role":role,"status":"pass"})
            role=1-role
    return {"public":readout(labels,roles,claims),"claims":claims,"events":log,
            "first_check_shortlist":first_targets or []}


def evaluate():
    files, hash_ = sources()
    observed=json.loads(files["direct_package"].read_text())
    checked=json.loads(files["field_invariants"].read_text())
    values=margins(SOURCE)
    counts, traces, controls=Counter(),{},{}
    for family,case,task in inputs():
        truth=tuple(project(case["options"],row["expected"]) for row in task["cards"])
        local=masks(family,case,observed)
        alternate=masks(family,case,checked)
        names=[o["id"] for o in case["options"]]
        scores=[[values[f"{family}/{who}/{name}"] for name in names] for who in (0,1)]
        required="AGREEMENT_POSSIBLE" if task["outcome"]=="agreement" else "IMPASSE"
        openings=product(*([name for i,name in enumerate(names) if sign&(1<<i)] for sign in truth))
        for opening in openings:
            base=None
            code=family+"/"+ "".join(opening)
            for arm,mode,capacity in (("peer_one","peer",1),("score_one","score",1),("peer_two","peer",2)):
                row=rollout(case,opening,local,alternate,truth,scores,mode,capacity)
                ok=row["public"]["state"]==required
                counts[family,arm,"correct"]+=ok
                counts[family,arm,"slots"]+=sum(event["turn"]>=0 for event in row["events"])
                counts[family,arm,"checks"]+=sum("checked" in event for event in row["events"])
                traces[code+"/"+arm]=row
                if arm=="peer_one":
                    base=row
            options=base["first_check_shortlist"]
            alternatives={}
            for option in options:
                row=rollout(case,opening,local,alternate,truth,scores,"peer",forced=option)
                alternatives[option]=row["public"]["state"]==required
            controls[code]={"all_first_targets":alternatives,
                             "chance_uniform":sum(alternatives.values())/len(alternatives)
                             if alternatives else float(base["public"]["state"]==required)}
    return {"inputs":{**hash_,"judge_predictions":sha256(SOURCE.read_bytes()).hexdigest()},
            "metrics":{"/".join(k):v for k,v in counts.items()},"traces":traces,"target_controls":controls}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
