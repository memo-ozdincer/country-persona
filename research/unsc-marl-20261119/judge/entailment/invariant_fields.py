"""Compile only package signs common to all observed mandate readings."""
import argparse
from collections import defaultdict
from itertools import product
import json
from pathlib import Path

from field_panel import suite, SCHEMAS
from package_panel import inputs
from partial_dispatch import evaluate


def compile_signs(rows, handoff_on_accept=False):
    variants = defaultdict(set)
    for plan in suite():
        row = rows[plan["id"]]
        key = plan["id"].rsplit("/",1)[0]
        logits = row["label_logits"]
        best = max(logits)
        variants[key].update(v for v,m in zip(plan["values"],logits,strict=True) if m==best)

    roles, signs = {}, {}
    for family,case,_ in inputs():
        for index, _ in enumerate(case["roles"]):
            name=f"{family}/{index}"
            fields=tuple(SCHEMAS[family])
            readings=[dict(zip(fields,tuple_,strict=True))
                      for tuple_ in product(*(sorted(variants[f"{name}/{f}"],key=lambda x:(x is not None,x or ""))
                                             for f in fields))]
            roles[name] = readings
            for option in case["options"]:
                fits={all(value is None or option[k]==value for k,value in r.items()) for r in readings}
                signs[f"{name}/{option['id']}"]={"accept":next(iter(fits)) if len(fits)==1 else None}
    return {"readings":roles,"decisions":signs,**evaluate({"decisions":signs},handoff_on_accept)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("predictions",type=Path)
    p.add_argument("--handoff-on-accept",action="store_true")
    args=p.parse_args()
    rows={r["id"]:r for r in map(json.loads,args.predictions.read_text().splitlines())}
    print(json.dumps(compile_signs(rows,args.handoff_on_accept),indent=2))
