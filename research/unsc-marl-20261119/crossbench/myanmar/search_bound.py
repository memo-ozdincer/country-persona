"""Find the shortest valid route in the actual one-source action space."""
import argparse
from functools import lru_cache
from itertools import product
import json
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent


def evaluate(metrics, allow_new_targets=False):
    metrics=metrics.get("replay",metrics)
    research=runpy.run_path(str(HERE/"run.py"))
    router=research["router"]
    menus=research["MENUS"]
    case=research["load"](HERE/"case.json")
    labels=[v["id"] for v in case["options"]]
    width=len(labels)
    full=(1<<width)-1
    proof={}
    for ordering in ("original","reversed"):
        for variant in ("uk-overlap","uk-impasse"):
            cards=("india",variant) if ordering=="original" else (variant,"india")

            def mask(names):
                return sum(1<<labels.index(k) for k in names)

            local=tuple(tuple(mask(k for k in labels if k not in case["later_only"][name]
                                   and metrics["package"][name][k]["admitted"] is value)
                              for value in (True,False)) for name in cards)
            truth=tuple(mask(menus[card]) for card in cards)
            verified=[{1<<i:metrics["package"][name][key]["admitted"] for i,key in enumerate(labels)}
                      for name in cards]
            scope=tuple(mask(metrics["scope"][card]["admitted_exclusions"]) for card in cards)
            tape={(actor,t):(0,0) for actor in range(2) for t in range(width+1)}
            for a,b in product(*(menus[card] for card in cards)):
                opening=mask(a),0,mask(b),0
                row=(width,truth,local,opening,scope)
                root=(router.sp.opened(opening,local),1,0,7)

                @lru_cache(maxsize=None)
                def solve(state):
                    if router.sp.terminal(state[0],full):
                        return state[2],()
                    if state[2]>=width+1:
                        return None
                    observation,options,normal=router.available((row,tape),state)
                    possible=[]
                    actions=[(move,move,options) for move in options]
                    public,actor,turn,credit=state
                    if allow_new_targets and credit&router.policy.CREDIT and turn+2<=width+1 and observation[6]!=0:
                        peer=1-actor
                        pending=local[actor][0]&~(public[1]|public[3]|public[2*peer]|public[2*actor])
                        actions.extend((f"request/{label}",router.policy.MATCH,{router.policy.MATCH:1<<i})
                                       for i,label in enumerate(labels) if pending&(1<<i))
                    for label,move,targets in actions:
                        after,_,_=router.transition((row,tape),state,move,targets,normal,verified)
                        result=solve(after)
                        if result is not None:
                            possible.append((result[0],(label,*result[1])))
                    return min(possible,key=lambda result:result[0],default=None)

                result=solve(root)
                count=solve.cache_info().currsize
                solve.cache_clear()
                key="/".join((ordering,variant,a+b))
                proof[key]={"min_continuation_slots":None if result is None else result[0],
                            "action_witness":None if result is None else result[1],"states":count}
                for arm in ("never","direct","scope","late_scope","learned"):
                    routed=metrics["paths"][f"{ordering}/{variant}/{arm}/{a+b}"]
                    actual=routed["ledger"]["state"]
                    if actual in ("AGREEMENT_POSSIBLE","IMPASSE"):
                        assert result is not None
    description=("Full-information shortest path with one additional query target type. A delegate can ask about a package it knows is eligible but has not offered. It still has to issue its own verified acceptance."
                 if allow_new_targets else
                 "Full-information shortest path under the same legal actions, evidence restrictions and budget. It uses future receipts and both local states.")
    return {"scope":description,"paths":proof}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    p.add_argument("--unannounced-targets",action="store_true")
    args=p.parse_args()
    print(json.dumps(evaluate(json.loads(args.metrics.read_text()),args.unannounced_targets),indent=2))
