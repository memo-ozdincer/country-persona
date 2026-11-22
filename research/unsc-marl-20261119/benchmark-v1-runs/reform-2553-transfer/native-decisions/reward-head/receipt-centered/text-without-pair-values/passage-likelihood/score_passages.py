"""Evaluate sum, mean and centered phrase scores against unchanged rewards."""
from itertools import product
import json
from statistics import mean

import numpy as np

import collect_passages as study

HERE=study.HERE
PARENT=study.PARENT
head,held=study.old.head,study.old.held
ORDERS=("ab","ba")
METHODS=("sum","mean","centered_sum","centered_mean")


def margin(candidates):
    first,second=(candidates[key] for key in ("1","2"))
    return (first["sum"]-second["sum"],
            first["sum"]/len(first["tokens"])-second["sum"]/len(second["tokens"]))


def decisions(log,fallback):
    results={}
    for key,item in log.items():
        share,rate,view,order=key.split("/")
        empty=log[f"{share}/{rate}/none/{order}"]["scores"]
        full=margin(item["scores"])
        baseline=margin(empty)
        combined=(*full,*(a-b for a,b in zip(full,baseline,strict=True)))
        results[key]={name:{"margin":v,"action":int(v<0.) if v else fallback}
                      for name,v in zip(METHODS,combined,strict=True)}
    return results


def run():
    study.lock()
    archive=json.loads((HERE/"verified.json").read_text())
    log=archive["rows"]
    earlier=json.loads((PARENT/"scores.json").read_text())
    inputs=held.READ(head.HERE/"verified.json")["outputs"]
    _,_,raw,edges,true=held.setup()
    typed=[np.asarray(row) for row in raw]
    default,third=(int(np.argmax(raw[i])) for i in (0,2))
    action=decisions(log,default)
    prior={(r["case"],r["observation"],r["order"]):r for r in earlier["scenes"]}
    rows=[]
    for share,rate in product(held.SHARES,held.RATES):
        prefix=f"{share}/{rate}"
        expected=head.sample(typed,edges,rate,share,true,inputs,prefix)
        for mode,info in expected.items():
            for order in ORDERS:
                matched=prior[prefix,mode,order]
                values={}
                upper=matched["known_checklist_ceiling"]
                prob=info["p"]
                view=info["obs"]
                for name in METHODS:
                    a=[action[f"{prefix}/{v}/{order}"][name]["action"] for v in head.VIEWS[mode]]
                    score=sum(prob[b,m]*true[a[view[b,m]],b,third][m] for b,m in product(range(2),range(8)))
                    check=head.forecast.replay.expected(info["returns"],prob,view,np.asarray(a),third)+true[0,0,0][0]
                    assert abs(score-check)<1e-9 and score<=upper+1e-9
                    values[name]={"release":float(score),"actions":a}
                values.update({name:matched["outcomes"][name] for name in
                               ("standalone","lexical","raw_label","paired_mean","centered_fitted","paired_centered_fitted")})
                rows.append({"case":prefix,"mode":mode,"order":order,"outcomes":values,"ceiling":upper})
    summary={}
    for mode,order in product(head.MODES,(*ORDERS,"both")):
        group=[r for r in rows if r["mode"]==mode and (order=="both" or r["order"]==order)]
        summary[f"{mode}/{order}"]={m:mean(r["outcomes"][m]["release"] for r in group)
                                   for m in group[0]["outcomes"]}
        summary[f"{mode}/{order}"]["known_checklist_ceiling"]=mean(r["ceiling"] for r in group)
    keys=[k for k in action if k.endswith("/ab")]
    agreement={name:sum(action[key][name]["action"]==action[key[:-2]+"ba"][name]["action"] for key in keys)
               for name in METHODS}
    content=[r for r in rows if r["mode"]=="content"]
    counterfactual={}
    for name in METHODS:
        differences=[row["outcomes"][name]["release"]-row["outcomes"]["standalone"]["release"]
                     for row in content]
        counterfactual[name]={"wins":sum(d>1e-9 for d in differences),
                             "losses":sum(d < -1e-9 for d in differences),
                             "ties":sum(abs(d)<=1e-9 for d in differences)}
    return {"summary":summary,"agreement_counts_out_of_20":agreement,
            "content_vs_standalone":counterfactual,"choices":action,"scenes":rows,
            "sequence_evaluations":sum(len(row["scores"]) for row in log.values()),
            "tokens_scored":sum(len(x["tokens"]) for r in log.values() for x in r["scores"].values()),
            "prefix_tokens_across_sequence_evaluations":sum(r["input_tokens"]*len(r["scores"]) for r in log.values()),
            "source_sha256":head.prior.digest(HERE/"verified.json")}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
