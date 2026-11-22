"""Replay one-source query choices with independently assembled model receipts."""
from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys

import exclusive_query as engine
from receipt_sources import load, MENUS

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from decision_ledger import readout, truthful_disclosure


def evaluate():
    receipt_path=HERE/"evidence/exclusive-query/source-audit.json"
    checkpoint=HERE/"evidence/exclusive-query/results.json"
    receipts=load(receipt_path)["sources_by_role"]
    weights={(tuple(k[0]),*k[1:]):v for k,v in load(checkpoint)["policy"]}
    policies=(("never",{}),("focused_first",{}),("scope_first",{}),("scope_late",{}),("learned",weights))
    totals,paths=Counter(),{}
    for method,root,variants,peer in (
        ("mali-whole",HERE.parents[1]/"mali",("france-overlap","france-impasse"),"russia"),
        ("space-direct-scope",HERE.parent,("china-overlap","china-impasse"),"japan"),
        ("scope-sets/original",HERE.parent,("china-overlap","china-impasse"),"japan"),
    ):
        case=load(root/"case.json")
        labels=tuple(o["id"] for o in case["options"])
        width=len(labels)

        def mask(picks):
            return sum(1<<labels.index(x) for x in picks)

        def show(bits):
            return [x for i,x in enumerate(labels) if bits&(1<<i)]

        for order in ("original","reversed"):
            for variant in variants:
                cards=(variant,peer) if method=="mali-whole" else (peer,variant)
                if order=="reversed":
                    cards=cards[::-1]
                roles=case["roles"] if order=="original" else case["roles"][::-1]
                entries=[receipts[f"{method}/{card}"] for card in cards]
                private=tuple(mask(MENUS[c]) for c in cards)
                known=tuple(tuple(mask(x for x,v in r["direct"].items() if v is sign
                                       and x not in r["positive_scope_conflicts"]) for sign in (True,False))
                            for r in entries)
                fields=tuple(mask(r["active_scope_exclusions"]) for r in entries)
                direct=[{1<<i:r["direct"][x] for i,x in enumerate(labels)
                         if x not in r["positive_scope_conflicts"]} for r in entries]
                for l,r in product(*(MENUS[c] for c in cards)):
                    opening=(mask(l),0,mask(r),0)
                    row=width,private,known,opening,fields
                    tape={(actor,t):(0,0) for actor in range(2) for t in range(width+1)}
                    start=engine.sp.opened(opening,known)
                    for arm,table in policies:
                        steps=[]
                        schedule=engine.BASE if table else arm
                        run=engine.play((row,tape),schedule,table,events=steps,recorded=direct)
                        signs=[(role,0,start[role*2]) for role in range(2) if start[role*2]]
                        for tick in steps:
                            if tick["query"]:
                                assert all(role==tick["query"]["respondent"] for role,_,_ in tick["disclosed"])
                            signs.extend(tick["disclosed"])
                        ledger=[]
                        for owner,negative,bits in signs:
                            claim={"id":f"claim-{len(ledger)+1}","role":roles[owner],
                                   "accepts":show(bits) if not negative else [],
                                   "excludes":show(bits) if negative else []}
                            assert truthful_disclosure(claim,MENUS[cards[owner]])
                            ledger.append(claim)
                        proof=readout(labels,roles,ledger)
                        expected="AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
                        assert run[0]==(proof["state"]==expected)
                        prefix=method,order,variant,arm
                        for k,v in zip(("solved","slots","checks","questions","answers","scope_queries"),run,strict=True):
                            totals[*prefix,k]+=v
                        totals[*prefix,"paths"]+=1
                        paths["/".join((*prefix,l+r))]={"decision":proof,"claims":ledger,"events":steps}
    return {"scope":"Only archived package and scope projections. A conflicting scope and its disputed positives are withheld without using the reference menu. Author checks each admitted sign after selection.",
            "inputs":{p.name:engine.sha256(p.read_bytes()).hexdigest() for p in (receipt_path,checkpoint)},
            "totals":engine.sp.flatten(totals),"paths":paths}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
