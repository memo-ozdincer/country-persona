"""Compose the held case and run matched-budget joint fits."""
import json
import runpy
import sys
from unittest.mock import patch

import numpy as np

from collect_delisting import HERE, BRIDGE, plan, read

sys.path.insert(0, str(BRIDGE))
bridge=runpy.run_path(str(BRIDGE/"fit.py"))
sys.path.remove(str(BRIDGE))
team=bridge["team"]
learner=bridge["learner"]
margin=bridge["margin"]


def bank(case, outputs):
    bridge_plan=read(BRIDGE/"plan.json")
    base=bridge["bank"](bridge_plan["cases"],read(BRIDGE/"verified.json")["outputs"])
    trained, audited = ([part.copy() for part in table] for table in base[:2])
    public,first,last,both,observed = trained
    public[1]=sum(s["weight"] for s in case["public"])
    authored=both[1].copy()
    judgements={}
    records={}
    for i, (view,v) in enumerate(case["early"].items()):
        first[1,i]=public[1]+v["weight"]
        x={t:margin(outputs,f"early/{view}/{t}") for t in case["relations"]}
        observed[1,i]=1+int(x["review"]>0)
        for j, (reply,r) in enumerate(case["late"].items()):
            y={t:margin(outputs,f"late/{reply}/{t}") for t in case["relations"]}
            last[1,j]=public[1]+r["weight"]
            seen=[t for t in x if x[t]>0 and y[t]>0]
            active=seen[0] if len(seen)==1 else None
            target=next((k for k,s in case["relations"].items() if s["early"]==view and s["late"]==reply),None)
            core=int(public[1])+v["weight"]+r["weight"]
            text=[s["text"] for s in [*case["public"],v,r]]
            if active:
                text.append(case["relations"][active]["text"])
            answer=" ".join(text)
            assert len(answer.split())<=case["word_cap"]
            both[1,i,j]=core+(case["relations"][active]["weight"] if active else 0)
            audited[3][1,i,j]=both[1,i,j] if not active or active==target else 0
            authored[i,j]=core+(case["relations"][target]["weight"] if target else 0)
            records[f"{view}/{reply}"]={"answer":answer,"native":active,"expected":target,
                                       "training":int(both[1,i,j]),"audited":int(audited[3][1,i,j]),
                                       "ideal":int(authored[i,j])}
            judgements[f"early/{view}"]=x
            judgements[f"late/{reply}"]=y
    for ix in (0,1,2,4):
        audited[ix][1]=trained[ix][1]
    return trained,audited,authored,records,judgements


def run():
    config=plan()
    assert config==read(HERE/"plan.json")
    case=config["case"]
    outputs=read(HERE/"verified.json")["outputs"]
    assert set(outputs)=={r["id"] for r in config["requests"]}
    trained,audited,authored,records,judgements=bank(case,outputs)
    all_truth=audited.copy()
    all_truth[3]=audited[3].copy()
    all_truth[3][1]=authored
    # The authored receive class is the same binary observation as the native reader, when correct.
    controls={k:margin(outputs,f'{row["side"]}/{k}/{row["type"]}') for k,row in case["controls"].items()}
    with patch.object(team,"PRIVATE",{"2664":("full","diversion","request-only"),"2744":tuple(case["early"])}):
        value=learner.train(trained)
        with patch.object(team,"BATCH",2*team.BATCH):
            sampled=team.train(trained)
        live=learner.fit.compare(audited,value[:2],sampled[:2])
        ceiling=learner.fit.compare(all_truth,value[:2],sampled[:2])
        regret=learner.send_audit(audited,live["held"])
    return {"records":records,"marks":judgements,"reject_if_negative":controls,"history":value[2],
            "sampled_history":sampled[2],"native":live,"authored":ceiling,"sender_misses":regret}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
