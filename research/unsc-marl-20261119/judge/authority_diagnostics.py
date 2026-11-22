"""Measure threshold and matched-ranking behavior of an authority judge."""
import argparse
from collections import Counter
import json
from pathlib import Path


def summarize(path):
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    margins={}
    for r in rows:
        key,_=r["id"].rsplit("/",1)
        odds=dict(zip(r["profiles"],r["label_logits"],strict=True))
        margins.setdefault(key,[]).append(odds["failed"]-odds["clear"])
    assert all(len(v)==2 for v in margins.values())
    averages={k:sum(v)/2 for k,v in margins.items()}

    def grade(keys,threshold):
        out={}
        for k in keys:
            guess="failed" if averages[k]>threshold else "clear" if averages[k]<threshold else None
            out[k]={"verdict":guess,"reference":k.rsplit("/",1)[1],
                    "correct":guess==k.rsplit("/",1)[1]}
        return out

    keys=list(margins)
    families={k.split("/")[0] for k in keys}
    calibrated={}
    for held in sorted(families):
        dev=[k for k in keys if k.split("/")[0]!=held]
        test=[k for k in keys if k.split("/")[0]==held]
        order=sorted({averages[k] for k in dev})
        candidates=[order[0]-1,*((x+y)/2 for x,y in zip(order,order[1:])),order[-1]+1]
        # Break development ties by distance from the closest observed margin,
        # then by the lower threshold. Only development labels are consulted.
        def select(point):
            correct=sum(g["correct"] for g in grade(dev,point).values())
            separation=min(abs(averages[k]-point) for k in dev)
            return correct,separation,-point
        cutoff=max(candidates,key=select)
        calibrated[held]={"threshold":cutoff,"development":grade(dev,cutoff),"test":grade(test,cutoff)}

    edits={}
    for key in keys:
        case,status=key.rsplit("/",1)
        if status!="clear":
            continue
        foil=case+"/failed"
        change=averages[foil]-averages[key]
        forced_orders=[b>a for a,b in zip(margins[key],margins[foil],strict=True)]
        edits[case]={"matched_margin_change":change,
                     "ranks_foil_higher":change>0,"rank_correct_in_each_order":forced_orders}
    winners=Counter()
    for a,b in margins.values():
        for margin in (a,b):
            winners["failed" if margin>0 else "clear" if margin<0 else "tie"]+=1
    return {"choice_comparisons":dict(winners),"margins_by_order":margins,
            "pooled_margins":averages,"zero_threshold":grade(keys,0),"pair_ranking":edits,
            "calibrate_on_other_family":calibrated,
            "input_tokens":sum(len(row["input_ids"]) for row in rows),
            "answer_mass_range":[min(row["legal_mass"] for row in rows),max(row["legal_mass"] for row in rows)]}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("predictions",type=Path)
    args=p.parse_args()
    print(json.dumps({"scope":"Exploratory analysis of archived logits. Pair ranking assumes access to a matched foil. Each calibrated threshold is selected using the other family's labels only.",
                      **summarize(args.predictions)},indent=2))
