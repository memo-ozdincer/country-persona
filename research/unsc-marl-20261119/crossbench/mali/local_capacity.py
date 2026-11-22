"""Exact capacity of a single deterministic local table on recorded workshop openings."""
import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
from unittest.mock import patch

import defer_scope as defer

study,policy=defer.study,defer.policy
BASE=defer.group.BASE


def episodes(metrics, conditions):
    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    labels=[p["id"] for p in case["options"]]
    width=len(labels)
    bit={p:1<<i for i,p in enumerate(labels)}
    tape={(r,t):(0,0) for r in range(2) for t in range(width+1)}
    for name in conditions:
        receipt=metrics["conditions"][name]
        for order,variant in product(("original","reversed"),("france-overlap","france-impasse")):
            cards=(variant,"russia") if order=="original" else ("russia",variant)
            truth=tuple(sum(bit[p] for p in menus[k]) for k in cards)
            local=tuple(tuple(sum(bit[p] for p in labels if p not in study.WITHHELD[k]
                                  and receipt["package"][k][p] is yes) for yes in (True,False)) for k in cards)
            scope=tuple(sum(bit[p] for p in receipt["scope"][k]) for k in cards)
            later=[{bit[p]:receipt["package"][k][p] for p in labels} for k in cards]
            for left,right in product(*(sorted(menus[k]) for k in cards)):
                opening=bit[left],0,bit[right],0
                key=(name,order,variant,left+right)
                yield key,((width,truth,local,opening,scope),tape),later


def routes(item,later):
    width,_,local,opening,_=item[0]
    root=policy.sp.opened(opening,local),1,0,7
    full=(1<<width)-1

    @lru_cache(maxsize=None)
    def traverse(state):
        ledger,_,slot,_=state
        if policy.sp.terminal(ledger,full):
            return {frozenset()}
        if slot>=width+1:
            return set()
        obs,moves,normal=policy.available(item,state)
        found=set()
        for action in moves:
            after,_,_=policy.transition(item,state,action,moves,normal,later)
            for tail in traverse(after):
                if any(key==obs and picked!=action for key,picked in tail):
                    continue
                found.add(tail|{(obs,action)} if len(moves)>1 else tail)
        return found

    try:
        alternatives=sorted(traverse(root),key=lambda p:(len(p),sorted(p)))
        # A smaller set of assignments that suffices makes each strict superset redundant.
        minimal=[]
        for path in alternatives:
            if not any(prior<=path for prior in minimal):
                minimal.append(path)
        return [dict(sorted(p)) for p in minimal]
    finally:
        traverse.cache_clear()


def consistent(required, alternatives):
    visited=0

    def search(todo,table):
        nonlocal visited
        visited+=1
        if not todo:
            return table
        candidates={}
        for case in todo:
            matches=[p for p in alternatives[case] if all(table.get(k,a)==a for k,a in p.items())]
            if not matches:
                return None
            candidates[case]=matches
        key=min(todo,key=lambda r:(len(candidates[r]),r))
        residue=tuple(k for k in todo if k!=key)
        for patch_ in candidates[key]:
            chosen=search(residue,{**table,**patch_})
            if chosen is not None:
                return chosen
        return None

    return search(required,{}),visited


def solve(cases, alternative_routes):
    agreements=tuple(k for k in cases if k[2]=="france-overlap")
    impasses=tuple(k for k in cases if k[2]=="france-impasse")
    needed,visited=consistent(impasses,alternative_routes)
    assert needed is not None, "This endpoint requires retaining all impasses"
    for lost in range(len(agreements)+1):
        for omissions in combinations(agreements,lost):
            needed=impasses+tuple(r for r in agreements if r not in omissions)
            table,steps=consistent(needed,alternative_routes)
            visited+=steps
            if table is not None:
                executed={}
                for key in cases:
                    item,later=cases[key]
                    result=policy.play(item,BASE,table,recorded=later)
                    assert key not in needed or result[0]
                    executed["/".join(key)]={"certified":result[0],"slots":result[1],"checks":result[2]}
                return {"max_agreements_with_all_impasses":len(agreements)-lost,
                        "impasses":len(impasses),"agreement_cases":len(agreements),
                        "omissions":omissions,"search_nodes":visited,"replay":executed,
                        "witness":[[k,a] for k,a in sorted(table.items())],
                        "terminal_local_routes":{"/".join(r):len(alternative_routes[r]) for r in cases}}
    raise AssertionError("Even the feasible impasse subset failed")


def audit(metrics):
    cases={k:(item,later) for k,item,later in episodes(metrics,("pooled","authored"))}
    with defer.enabled():
        original=policy.available
        original_default=policy.default

        def clock(item,state):
            obs,moves,normal=original(item,state)
            return (*obs,state[2]),moves,normal

        result={}
        for key,available,default in (
            ("frozen",original,original_default),
            ("exact_clock",clock,lambda k,m:original_default(k[:-1],m)),
        ):
            with patch.object(policy,"available",new=available),patch.object(policy,"default",new=default):
                all_routes={k:routes(item,later) for k,(item,later) in cases.items()}
                result[key]={name:solve({k:v for k,v in cases.items() if name=="joint" or k[0]==name},all_routes)
                             for name in ("pooled","authored","joint")}
    return {"scope":"Exact in-sample expressivity check. Outcome labels, future receipts and all episode routes are used to find the table. Each execution reads only the declared observation. No fitted policy uses these witness tables.",
            "views":result}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    out=audit(study.mali.load(args.metrics))
    out["input_sha256"]=sha256(args.metrics.read_bytes()).hexdigest()
    print(json.dumps(out,indent=2))
