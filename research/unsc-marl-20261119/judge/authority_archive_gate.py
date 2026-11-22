"""Keep a binary fabrication guard separate from its three-way diagnosis."""
import argparse
from collections import Counter
import json
from pathlib import Path

import authority_archive as archive


def guard_for(labels):
    if not labels:
        return "uncertain"
    choices={"clear" if x=="supported" else "failed" for x in labels}
    return next(iter(choices)) if len(choices)==1 else "uncertain"


def evaluate(path):
    rows={r["id"]:r for r in map(json.loads,path.read_text().splitlines())}
    result=archive.score(rows)
    metrics=Counter()
    letter_orders={}
    comparison={}
    for case,decision in result["cases"].items():
        expected=guard_for([decision["reference"]])
        projected=guard_for({v for order in decision["orders"] for v in order})
        status="uncertain" if projected=="uncertain" else "correct" if projected==expected else "wrong"
        metrics[status]+=1
        table={}
        for i,layout in enumerate(decision["orders"]):
            raw=rows[f"{case}/{i}"]
            letters=[k for k,name in zip(raw["labels"],raw["profiles"],strict=True) if name in layout]
            by_order=letter_orders.setdefault(i,Counter())
            for label in letters:
                by_order[label]+=1
            table[i]={"labels":layout,"codes":letters,"guard":guard_for(layout)}
        comparison[case]={"reference_guard":expected,"stable_guard":projected,
                          "status":status,"orders":table}
    return {"scope":"Three-way labels remain available for diagnosis. The binary authority guard treats either contrary evidence or an unestablished material official attribution as a failure.",
            "counts":dict(metrics),"cases":comparison,
            "input_tokens":sum(len(x["input_ids"]) for x in rows.values()),
            "letter_winners_by_order":letter_orders}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("predictions",type=Path)
    a=p.parse_args()
    print(json.dumps(evaluate(a.predictions),indent=2))
