"""Compute the proof ceiling with the locked compound-reply actions and receipts."""
import argparse
from collections import Counter
from functools import lru_cache
from itertools import product
import json
from pathlib import Path

import joint_transfer as study


def measure(metrics):
    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    labels=[opt["id"] for opt in case["options"]]
    width=len(labels)
    bits={name:1<<i for i,name in enumerate(labels)}
    full=(1<<width)-1
    policy=study.group.policy
    tape={(role,t):(0,0) for role in range(2) for t in range(width+1)}
    results={}
    for condition in ("authored","archived","stable","pooled"):
        evidence=metrics["conditions"][condition]
        counts,paths=Counter(),{}
        with study.reply.enabled():
            for order in ("original","reversed"):
                for variant in ("france-overlap","france-impasse"):
                    kind="agreement" if variant.endswith("overlap") else "impasse"
                    cards=(variant,"russia") if order=="original" else ("russia",variant)
                    possible=tuple(sum(bits[p] for p in menus[role]) for role in cards)
                    scope=tuple(sum(bits[p] for p in evidence["scope"][role]) for role in cards)
                    receipts=[{bits[p]:sign for p,sign in evidence["package"][role].items()} for role in cards]
                    local=tuple(tuple(sum(bits[p] for p in labels if p not in study.WITHHELD[k]
                                          and evidence["package"][k][p] is stance)
                                      for stance in (True,False)) for k in cards)
                    for left,right in product(*(sorted(menus[k]) for k in cards)):
                        opening=(bits[left],0,bits[right],0)
                        row=(width,possible,local,opening,scope)

                        @lru_cache(maxsize=None)
                        def solve(state):
                            if policy.sp.terminal(state[0],full):
                                return state[2],()
                            if state[2]>=width+1:
                                return None
                            _,actions,routine=policy.available((row,tape),state)
                            children=[]
                            for action in actions:
                                after,_,event=policy.transition((row,tape),state,action,actions,routine,receipts)
                                child=solve(after)
                                if child is not None:
                                    children.append((child[0],((action,event),*child[1])))
                            return min(children,key=lambda v:v[0],default=None)

                        root=(policy.sp.opened(opening,local),1,0,7)
                        solution=solve(root)
                        states=solve.cache_info().currsize
                        solve.cache_clear()
                        key="/".join((order,variant,left+right))
                        statuses={name:evidence["paths"]["/".join((order,variant,name,left+right))]["verdict"]["state"]
                                  for name in ("compound_first","compound_fixed","compound_learned")}
                        terminal=any(s in ("AGREEMENT_POSSIBLE","IMPASSE") for s in statuses.values())
                        assert not terminal or solution is not None
                        counts[kind,"presentations"]+=1
                        counts[kind,"reachable"]+=solution is not None
                        paths[key]={"earliest_slot":None if solution is None else solution[0],
                                    "witness":None if solution is None else solution[1],
                                    "states":states,"matched_policies":statuses}
        results[condition]={"totals":policy.sp.flatten(counts),"paths":paths}
    return {"scope":"Clairvoyant search of the same legal actions and eight continuation slots. The oracle observes both delegates' evidence and the resulting receipts.",
            "conditions":results}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics",type=Path)
    args=parser.parse_args()
    print(json.dumps(measure(study.mali.load(args.metrics)),indent=2))
