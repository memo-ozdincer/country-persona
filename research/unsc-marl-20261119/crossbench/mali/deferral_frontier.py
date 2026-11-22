"""Measure the minimum number of deferrals required to certify each Mali opening."""
import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import defer_scope as defer

study=defer.study
policy=defer.policy


def frontier(metrics):
    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    options=[p["id"] for p in case["options"]]
    width=len(options)
    bits={p:1<<i for i,p in enumerate(options)}
    full=(1<<width)-1
    tape={(r,t):(0,0) for r in range(2) for t in range(width+1)}
    output={}
    with defer.enabled():
        for condition in ("pooled","authored"):
            receipt=metrics["conditions"][condition]
            paths={}
            totals=Counter()
            for order,var in product(("original","reversed"),("france-overlap","france-impasse")):
                cards=(var,"russia") if order=="original" else ("russia",var)
                cls="agreement" if var.endswith("overlap") else "impasse"
                truth=tuple(sum(bits[p] for p in menus[k]) for k in cards)
                scope=tuple(sum(bits[p] for p in receipt["scope"][k]) for k in cards)
                later=[{bits[p]:receipt["package"][k][p] for p in options} for k in cards]
                local=tuple(tuple(sum(bits[p] for p in options if p not in study.WITHHELD[k]
                                      and receipt["package"][k][p] is yes) for yes in (True,False)) for k in cards)
                for left,right in product(*(sorted(menus[k]) for k in cards)):
                    opening=bits[left],0,bits[right],0
                    item=(width,truth,local,opening,scope),tape
                    root=policy.sp.opened(opening,local),1,0,7

                    @lru_cache(maxsize=None)
                    def graph(state):
                        public,_,slot,_=state
                        if policy.sp.terminal(public,full):
                            return {0:(slot,())}
                        if slot>=width+1:
                            return {}
                        _,actions,routine=policy.available(item,state)
                        best={}
                        for action in actions:
                            after,_,_=policy.transition(item,state,action,actions,routine,later)
                            for count,(end,path) in graph(after).items():
                                used=count+(action==defer.DEFER)
                                if used not in best or end<best[used][0]:
                                    best[used]=end,((slot,action),*path)
                        return best

                    solution=graph(root)
                    graph.cache_clear()
                    found=min(solution,default=None)
                    if found is not None:
                        totals[cls,str(found)]+=1
                    paths[f"{order}/{var}/{left}{right}"]={
                        "minimum_deferrals":found,"counts_to_earliest_slot":{
                            k:{"slots":end,"actions":path} for k,(end,path) in sorted(solution.items())},
                    }
            output[condition]={"minimal_deferrals":policy.sp.flatten(totals),"paths":paths}
    return output


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics",type=Path)
    args=parser.parse_args()
    print(json.dumps({"input_sha256":sha256(args.metrics.read_bytes()).hexdigest(),
                      "conditions":frontier(study.mali.load(args.metrics))},indent=2))
