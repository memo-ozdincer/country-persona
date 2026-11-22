"""Stress invariant package ordering under equivalent public attribute encodings."""
import argparse
from collections import Counter
from itertools import permutations, product
import json
from pathlib import Path

import canonical_menu as order
from semantic_order_fit import RulePolicy


def alias_maps(features):
    values=[sorted({option[j] for option in features}) for j in range(len(features[0]))]
    numberings=[tuple(permutations(f)) for f in values]
    for axis in permutations(range(len(values))):
        for layout in product(*numberings):
            codes=[dict(zip(prior,sequence,strict=True)) for prior,sequence in zip(values,layout,strict=True)]
            yield axis,layout,{option:tuple(codes[j][option[j]] for j in axis) for option in features}


def analyze(items,rules):
    rows=list(items)
    features=rows[0][-1]
    assert all(r[-1]==features for r in rows)
    outputs=[]
    for axes,levels,aliases in alias_maps(features):
        transformed=[(*r[:-1],tuple(aliases[option] for option in r[-1])) for r in rows]
        results={}
        for key,mode in (("fixed_public","public"),("learned",RulePolicy(rules))):
            report=order.evaluate_case(transformed,mode)
            solved=Counter()
            for episode,path in report["paths"].items():
                kind="agreement" if episode.split("/")[1].endswith("overlap") else "impasse"
                solved[kind]+=path["cost"][0]
            results[key]=dict(solved)
        outputs.append({"axis_order":axes,
                        "levels":[[f[1] for f in sequence] for sequence in levels],"results":results})
    histogram={arm:dict(sorted(Counter(f"{d['results'][arm]['agreement']}/{d['results'][arm]['impasse']}"
                                       for d in outputs).items())) for arm in ("fixed_public","learned")}
    return {"histogram":histogram,"layouts":outputs}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    p.add_argument("trained",type=Path)
    a=p.parse_args()
    load=order.study.mali.load
    rules=load(a.trained)["rules"]
    result={"scope":"Per-family structured attribute coding permutations. Signed claims, identity, frozen model evidence and role order are preserved. This control does not rerun model text parsing.",
            "families":{"myanmar":analyze(order.myanmar(0),rules),
                        "mali":analyze(order.mali(load(a.metrics),0),rules)}}
    print(json.dumps(result,indent=2))
