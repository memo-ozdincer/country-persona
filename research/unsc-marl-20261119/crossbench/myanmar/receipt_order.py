"""Replay the two individually scored answer layouts without a second read."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import joint_receipt
import joint_reply
import target_transfer


def assess(predictions):
    rows={r["id"]:r for r in map(json.loads,predictions.read_text().splitlines())}
    layouts={}
    for layout in range(2):
        plan_rows={}
        for plan in joint_receipt.suite():
            role,_=plan["id"].split("/")
            source=rows[f"{role}/{layout}"]
            by_profile=dict(zip(map(tuple,source["profiles"]),source["label_logits"],strict=True))
            plan_rows[plan["id"]]={"label_logits":[by_profile[p] for p in plan["profiles"]]}
        result=joint_receipt.score(plan_rows)
        with TemporaryDirectory() as staging:
            file=Path(staging)/"projection.json"
            file.write_text(json.dumps(result)+"\n")
            paths=target_transfer.evaluate(file,bundle=True,joint=(joint_reply.enabled,{}))
        layouts[layout]={"field_summary":{k:v for k,v in result["totals"].items() if k.count("/")==1},
                         "readings":result["joint_readings"],
                         "package":result["package"],
                         "routing":paths["totals"],
                         "raw_inputs":[{"id":r["id"],"tokens":len(r["input_ids"]),"legal_mass":r["legal_mass"]}
                                       for r in rows.values() if r["id"].endswith(f"/{layout}")]}
    return {"input_sha256":sha256(predictions.read_bytes()).hexdigest(),"layouts":layouts,
            "scope":"Retrospective control. Each layout uses its three recorded calls only and retains the authored menu gate. Never choose the layout by outcome."}


def pooled(predictions):
    rows={r["id"]:r for r in map(json.loads,predictions.read_text().splitlines())}
    summed={}
    for plan in joint_receipt.suite():
        role,_=plan["id"].split("/")
        reading=[rows[f"{role}/{i}"] for i in range(2)]
        merged=[dict(zip(map(tuple,r["profiles"]),r["label_logits"],strict=True)) for r in reading]
        marginal={}
        for i,choices in enumerate(joint_receipt.FIELDS.values()):
            for choice in choices:
                total=0.0
                for order in merged:
                    peak=max(order.values())
                    total+=math.log(math.fsum(math.exp(logit-peak)
                                              for profile,logit in order.items() if profile[i]==choice))
                marginal[i,choice]=total
        summed[plan["id"]]={"label_logits":[sum(marginal[i,v] for i,v in enumerate(p))
                                           for p in plan["profiles"]]}
    result=joint_receipt.score(summed)
    with TemporaryDirectory() as staging:
        file=Path(staging)/"projection.json"
        file.write_text(json.dumps(result)+"\n")
        paths=target_transfer.evaluate(file,bundle=True,joint=(joint_reply.enabled,{}))
    return {"input_sha256":sha256(predictions.read_bytes()).hexdigest(),
            "field_summary":{k:v for k,v in result["totals"].items() if k.count("/")==1},
            "readings":result["joint_readings"],"package":result["package"],"routing":paths["totals"],
            "scope":"Retrospective. Marginalize each field within each layout, then sum across layout log scores with equal weights. This discards per-layout disagreement as an abstention criterion."}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("predictions",type=Path)
    p.add_argument("--pool",action="store_true")
    args=p.parse_args()
    check=pooled if args.pool else assess
    print(json.dumps(check(args.predictions),indent=2))
