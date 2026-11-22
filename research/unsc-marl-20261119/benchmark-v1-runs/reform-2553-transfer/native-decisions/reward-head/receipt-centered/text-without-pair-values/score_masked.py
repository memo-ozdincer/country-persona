"""Replay equal-information text and fixed comparators against the frozen source ruler."""
from itertools import product
import json
import re
from statistics import mean

import numpy as np

import collect_masked as test

prior,head,held=test.prior,test.head,test.held
HERE=test.HERE
STOP=set("a an and as at by for from in into is it of on or that the their to was with would".split())


def words(text):
    return set(re.findall("[a-z]+",text.lower()))-STOP


def lexical(payload):
    local=payload["standalone_points"][payload["your_desk"]]
    seen=words(payload["your_view"].get("text",""))
    scored=[]
    for index,excerpt in payload["your_menu"].items():
        terms=words(excerpt)
        scored.append((len(seen&terms)/max(1,len(seen|terms)),local[index],-int(index)))
    return -max(scored)[2]-1


def choice(margin, default):
    return int(margin<0) if margin else default


def run():
    lock=test.locked()
    selected={req["id"]:json.loads(req["messages"][1]["content"]) for req in lock["requests"]}
    assert all("joint_requirements" not in row for row in selected.values())
    outputs=json.loads((HERE/"verified.json").read_text())["outputs"]
    fit=json.loads((test.PARENT/"results.json").read_text())
    weights={k:fit["training"][k][-1]["weights"][0] for k in ("reader_raw","centered_once")}
    base=held.READ(head.HERE/"scores.json")["held"]
    reference=held.READ(head.HERE/"verified.json")["outputs"]
    _,_,raw,edges,true=held.setup()
    default,third=(int(np.argmax(raw[i])) for i in (0,2))
    diff=(raw[0][0]-raw[0][1])/7
    local=[np.asarray(x) for x in raw]
    results=[]
    for share,rate in product(held.SHARES,held.RATES):
        key=f"{share}/{rate}"
        world=head.sample(local,edges,rate,share,true,reference,key)
        for mode,old in world.items():
            expected=base[key][mode]
            for order in prior.ORDERS:
                views=head.VIEWS[mode]
                margins=[prior.native(outputs,key,v,order) for v in views]
                neutral=prior.native(outputs,key,"none",order)
                paired_centered=[mean(prior.native(outputs,key,v,o)-prior.native(outputs,key,"none",o)
                                      for o in prior.ORDERS) for v in views]
                controls={
                    "raw_label":[int(test.runtime.LABELS[order][outputs[f"{key}/{v}/{order}"]["label"]])-1 for v in views],
                    "raw_with_local_tie":[choice(value,default) for value in margins],
                    "paired_mean":[choice(mean(prior.native(outputs,key,v,o) for o in prior.ORDERS),default)
                                   for v in views],
                    "paired_centered":[choice(value,default) for value in paired_centered],
                    "paired_centered_fitted":[choice(value+weights["centered_once"]*diff,default)
                                              for value in paired_centered],
                    "centered":[choice(value-neutral,default) for value in margins],
                    "raw_fitted":[choice(value + weights["reader_raw"]*diff,default) for value in margins],
                    "centered_fitted":[choice(value-neutral+weights["centered_once"]*diff,default) for value in margins],
                    "standalone":[default for _ in views],
                    "lexical":[lexical(selected[f"{key}/{v}/{order}"]) for v in views],
                }
                prob,seen,rewards=(old[k] for k in ("p","obs","returns"))
                full_info=expected["oracle"]["released"]
                outcomes={}
                for name,actions in controls.items():
                    points=sum(prob[b,m]*true[(actions[seen[b,m]],b,third)][m]
                               for b,m in product(range(2),range(8)))
                    checked=head.forecast.replay.expected(rewards,prob,seen,np.asarray(actions),third)+true[0,0,0][0]
                    assert abs(points-checked)<1e-9 and points<=full_info+1e-9
                    outcomes[name]={"release":float(points),"actions":actions,"third":third}
                results.append({"case":key,"observation":mode,"order":order,
                                "outcomes":outcomes,"known_checklist_ceiling":full_info,
                                "no_receipt_margin":neutral})
    summary={}
    for mode,order in product(head.MODES,(*prior.ORDERS,"both")):
        rows=[r for r in results if r["observation"]==mode and (r["order"]==order or order=="both")]
        summary[f"{mode}/{order}"]={k:mean(r["outcomes"][k]["release"] for r in rows)
                                   for k in rows[0]["outcomes"]}
        summary[f"{mode}/{order}"]["known_checklist_ceiling"]=mean(r["known_checklist_ceiling"] for r in rows)
    return {"summary":summary,"scenes":results,
            "verified_sha256":head.prior.digest(HERE/"verified.json")}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
