"""Use relative entailment to resolve only disputed role-package choices."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import run as base

HERE=Path(__file__).resolve().parent
PROSE=HERE.parents[1]/"crossbench/disclosure/clarify/routing/live/prose"
sys.path.insert(0,str(PROSE))
import study
from reconcile import INPUTS,candidates
from transfer import CONTRAST


def serialize(x):
    return json.dumps(x,ensure_ascii=False,separators=(",",":"))


def suite():
    originals,_=study.suite()
    for role,menus in candidates().items():
        left,right=map(set,menus)
        payload=json.loads(originals[role]["messages"][1]["content"])
        private=payload["private_instruction"]
        for option in sorted(left^right):
            quote=f"Private mandate: {private}\nOffered package {option}: {payload['packages'][option]}"
            eligible = "This package meets all explicit requirements of the private mandate."
            ineligible = "This package fails at least one explicit requirement of the private mandate."
            for invert in (False,True):
                claims = (ineligible,eligible) if invert else (eligible,ineligible)
                body = {"source":quote,"highlighted_quote":quote,
                        "candidate_claims":dict(zip(("A","B"),claims,strict=True))}
                yield {"id":f"{role}/{option}/{int(invert)}","support_code":"B" if invert else "A",
                       "messages":[{"role":"system","content":CONTRAST},
                                   {"role":"user","content":serialize(body)}]}


def score(rows):
    grouped={}
    for plan in suite():
        k=plan["id"].rsplit("/",1)[0]
        a,b=rows[plan["id"]]["label_logits"]
        grouped.setdefault(k,[]).append(a-b if plan["support_code"]=="A" else b-a)
    judgments,assembled={},{}
    for role,menus in candidates().items():
        left,right=map(set,menus)
        predicted=left&right
        for option in sorted(left^right):
            key=f"{role}/{option}"
            margins=grouped[key]
            flags=[True if v>0 else False if v<0 else None for v in margins]
            verdict=flags[0] if flags[0]==flags[1] else None
            judgments[key]={"signed_eligibility_margins":margins,"accept":verdict}
            if verdict:
                predicted.add(option)
        if any(row["accept"] is None for k,row in judgments.items() if k.startswith(f"{role}/")):
            assembled[role]={"output":"{}"}
        else:
            assembled[role]={"output":serialize({"accepts":sorted(predicted)})}
    metrics=study.score(assembled)
    return {"eligibility_judgments":judgments,"assembled_model_outputs":assembled,**metrics,
            "totals":{"atomic_disagreements":len(judgments),"model_calls":len(rows),
                      "exact_menus":sum(r["exact"] for r in metrics["menus"].values())}}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    base.suite=suite
    base.score=score
    base.main(args.model,args.output)
    dependencies=[Path(__file__).resolve(),PROSE/"study.py",PROSE/"mandates.json",
                  PROSE/"reconcile.py",HERE/"transfer.py",*INPUTS,*study.source_paths().values()]
    (args.output/"application-lock.json").write_text(serialize(
        {str(path):sha256(path.read_bytes()).hexdigest() for path in dependencies})+"\n")
