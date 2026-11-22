"""Replay the expanded query-target policy with the same source receipts."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import runpy

import new_targets as extra

HERE=Path(__file__).resolve().parent


def evaluate(path, offset=0, bundle=False, scope_minimum=None, joint=None):
    plug=runpy.run_path(str(HERE/"run.py"))
    router,menus,load=plug["router"],plug["MENUS"],plug["load"]
    reports=load(path)
    reports=reports.get("replay",reports)
    trained=HERE/"evidence/target-policy/results.json"
    actor=extra.decode(load(trained))
    context=extra.enable
    schedules=(("none","never",{}),("late_scope","scope_late",{}),
               ("first",extra.START,{}),("last","unannounced_last",{}),
               ("learned",extra.START,actor))
    if bundle:
        import target_set
        trained=HERE/"evidence/set-policy/results.json"
        actor=target_set.decode(load(trained))
        context=target_set.enabled
        schedules=(("none","never",{}),("direct","focused_first",{}),("scope","scope_first",{}),
                   ("set_first","set_first",{}),("set_after",target_set.BASE,{}),
                   ("set_three","set_three",{}),("learned",target_set.BASE,actor))
        if scope_minimum is not None:
            import target_sources
            context=lambda: target_sources.enabled(scope_minimum)
        if joint is not None:
            context, fitted = joint
            schedules=(*schedules,("joint_fit",target_set.BASE,fitted))
    case=load(HERE/"case.json")
    labels=tuple(p["id"] for p in case["options"])
    width=len(labels)
    labels=labels[offset:]+labels[:offset]
    counts,paths=Counter(),{}
    for ordering in ("original","reversed"):
        roles=case["roles"] if ordering=="original" else case["roles"][::-1]
        for variant in ("uk-overlap","uk-impasse"):
            cards=("india",variant) if ordering=="original" else (variant,"india")

            def mask(items):
                return sum(1<<labels.index(i) for i in items)

            def names(value):
                return [k for i,k in enumerate(labels) if value&(1<<i)]

            known=tuple(tuple(mask(k for k in labels if k not in case["later_only"][side]
                                   and reports["package"][side][k]["admitted"] is v)
                              for v in (True,False)) for side in cards)
            truth=tuple(mask(menus[k]) for k in cards)
            fields=tuple(mask(reports["scope"][k]["admitted_exclusions"]) for k in cards)
            later=[{1<<i:reports["package"][side][k]["admitted"] for i,k in enumerate(labels)} for side in cards]
            for a,b in product(*(menus[k] for k in cards)):
                row=(width,truth,known,(mask(a),0,mask(b),0),fields)
                tape={(r,t):(0,0) for r in range(2) for t in range(width+1)}
                start=router.sp.opened(row[3],known)
                with context():
                    for arm,mode,weights in schedules:
                        steps=[]
                        outcome=router.play((row,tape),mode,weights,events=steps,recorded=later)
                        for tick in steps:
                            query=tick["query"]
                            if query is None or "request_set" not in query:
                                continue
                            assert 2<=query["request_set"].bit_count()<=3
                            for role,negative,bits in tick["disclosed"]:
                                assert role==query["respondent"]
                                if query.get("lookup")=="scope_only":
                                    assert negative and not bits&~query["published"]
                                elif query.get("lookup")=="joint_fields":
                                    eligible=query["qualified_exclusions"] if negative else query["qualified_acceptance"]
                                    assert not bits&~eligible
                                else:
                                    assert bits==query["target"]
                        claims=[]
                        initial=[(r,0,start[r*2]) for r in range(2) if start[r*2]]
                        for role,negative,bits in initial+[entry for t in steps for entry in t["disclosed"]]:
                            message={"id":f"m{len(claims)+1}","role":roles[role],
                                     "accepts":names(bits) if not negative else [],
                                     "excludes":names(bits) if negative else []}
                            assert plug["truthful_disclosure"](message,menus[cards[role]])
                            claims.append(message)
                        readout=plug["readout"](labels,roles,claims)
                        expected="AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
                        assert outcome[0]==(readout["state"]==expected)
                        prefix=ordering,variant,arm
                        for k,v in zip(("solved","slots","checks","questions","answers","scope"),outcome,strict=True):
                            if k=="scope" and scope_minimum is not None:
                                v=sum(t["query"] is not None and t["query"].get("lookup")=="scope_only"
                                      for t in steps)
                            counts[*prefix,k]+=v
                        counts[*prefix,"paths"]+=1
                        paths["/".join((*prefix,a+b))]={"claims":claims,"steps":steps,"decision":readout}
    return {"scope":"Bounded replay on exact or archived language-model evidence. An unannounced question never admits a requester sign.",
            "inputs":{x.name:extra.sha256(x.read_bytes()).hexdigest() for x in (path,trained)},
            "totals":router.sp.flatten(counts),"paths":paths}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    p.add_argument("--rotate",action="store_true")
    p.add_argument("--set",action="store_true")
    args=p.parse_args()
    if args.rotate:
        panels={}
        for slot in range(7):
            replay=evaluate(args.metrics,slot,args.set)
            panels[str(slot)]=replay["totals"]
        print(json.dumps({"scope":"Seven cyclic permutations of package order, dispositions unchanged.",
                          "tables":panels},indent=2))
    else:
        print(json.dumps(evaluate(args.metrics,bundle=args.set),indent=2))
