"""Check request and response ownership on the archived Mali workshops."""
import argparse
from collections import Counter
from functools import partial
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

import focused_query as focused

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from decision_ledger import readout,truthful_disclosure

MALI=HERE.parents[1]/"mali"
MENUS={"france-overlap":"AEG","france-impasse":"AG","russia":"CE"}


def load(path):
    return json.loads(path.read_text())


def evaluate(scoped=False):
    sources={"Qwen package signs":MALI/"evidence/metrics.json","case":MALI/"case.json",
             "focused weights":HERE/"evidence/focused-query/results.json",
             "query weights":HERE/"evidence/query/results.json"}
    if scoped:
        from scope_reply import reply
        sources["scope reply"] = HERE/"evidence/scope-reply/results.json"
        additional = focused.table(load(sources["scope reply"])["training"])
    case=load(sources["case"])
    votes=load(sources["Qwen package signs"])
    fitted=focused.table(load(sources["focused weights"])["fit"])
    simple=focused.table(load(sources["query weights"]))
    labels=[r["id"] for r in case["options"]]
    width=len(labels)
    metrics,paths=Counter(),{}
    policy=focused.policy

    def mask(names):
        return sum(1<<labels.index(k) for k in names)

    def names(bits):
        return [k for i,k in enumerate(labels) if bits&(1<<i)]

    for reverse in (False,True):
        order="reversed" if reverse else "original"
        for variant in ("france-overlap","france-impasse"):
            cards=("russia",variant) if reverse else (variant,"russia")
            roles=case["roles"][::-1] if reverse else case["roles"]
            truth=tuple(mask(MENUS[card]) for card in cards)
            known=tuple(tuple(mask(k for k,v in votes["package_predictions"][card].items() if v["sign"] is sign)
                              for sign in (True,False)) for card in cards)
            scopes=tuple(mask(opt["id"] for opt in case["options"]
                              if opt["scope"] in votes["published_scope_candidates"]["whole_set"][card])
                         for card in cards)
            recorded=[{1<<i:False for i in range(width) if flag&(1<<i)} for flag in scopes]
            authored=[{1<<i:bool(t&(1<<i)) for i in range(width)} for t in truth]
            channels=(
                ("baseline",focused.ASK_ONLY_ADVANCE,"never",{}),
                ("known_learned",focused.ASK_ONLY_ADVANCE,policy.START,simple),
                ("focused_script",partial(focused.answer,recorded=recorded),policy.START,{}),
                ("focused_learned",partial(focused.answer,recorded=recorded),policy.START,fitted),
                ("focused_authored",partial(focused.answer,recorded=authored),policy.START,fitted),
            )
            if scoped:
                channels += (("scoped_reply_script",partial(reply,recorded=recorded),policy.START,{}),
                             ("scoped_reply_learned",partial(reply,recorded=recorded),policy.START,additional))
            for a,b in product(*(MENUS[k] for k in cards)):
                row=width,truth,known,(mask(a),0,mask(b),0),scopes
                tape={(r,t):(0,0) for r in range(2) for t in range(width+1)}
                for arm,channel,schedule,table in channels:
                    local_trace=[]
                    with patch.object(policy,"advance",side_effect=channel):
                        out=policy.play((row,tape),schedule,table,events=local_trace)
                    first=focused.sp.opened(row[3],known)
                    claims=[]
                    signed=[(r,0,first[2*r]) for r in range(2) if first[2*r]]
                    for e in local_trace:
                        q=e["query"]
                        if q and q["admitted"]:
                            assert len(e["new_signed_masks"])==1
                            actor,stance,bits=e["new_signed_masks"][0]
                            assert actor==q["respondent"] and actor!=q["asker"] and bool(bits&q["target"])
                            assert bits==q.get("admitted_scope_mask",q["target"])
                        signed.extend(e["new_signed_masks"])
                    for actor,stance,answer in signed:
                        claim={"id":f"claim-{len(claims)+1}","role":roles[actor],
                               "accepts":names(answer) if stance==0 else [],
                               "excludes":names(answer) if stance==1 else []}
                        assert truthful_disclosure(claim,MENUS[cards[actor]])
                        claims.append(claim)
                    decision=readout(labels,roles,claims)
                    expected="AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
                    assert out[0]==(decision["state"]==expected)
                    key=order,variant,arm
                    for tag,value in zip(("solved","slots","checks","questions","answers"),out,strict=True):
                        metrics[*key,tag]+=value
                    paths["/".join((*key,a+b))]={"public_decision":decision,"published":claims,"events":local_trace}
    return {"scope":"Recorded model scopes can verify only negatives; authored arm also has exact positive lookups.",
            "sha256":{k:focused.sha256(p.read_bytes()).hexdigest() for k,p in sources.items()},
            "metrics":focused.sp.flatten(metrics),"paths":paths}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scoped",action="store_true")
    print(json.dumps(evaluate(p.parse_args().scoped),indent=2))
