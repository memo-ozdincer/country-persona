"""Replay frozen joint policies on a fourth UN-linked case family."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

import joint_deferral_fit as deferral
import joint_repair_fit as repair

fit=repair.fit
SPACE=Path(__file__).resolve().parent/"crossbench/space"
FILES=(SPACE/"case.json",SPACE/"evidence/metrics.json",SPACE/"evidence/scope-sets/metrics.json")
HOLDBACK={"japan":"DF","china-overlap":"FG","china-impasse":"FG"}
ARCHIVE_SEED=895153


def rows(condition):
    case, reader, scope = (json.loads(p.read_text()) for p in FILES)
    options=case["options"]
    labels=[opt["id"] for opt in options]
    bits={p:1<<i for i,p in enumerate(labels)}
    width=len(labels)
    public=fit.transfer.canonical.descriptions(case,tuple(labels))
    answers={}
    for role in case["cards"]:
        outcomes={p:reader["decisions"][f"{role}/{p}"] for p in labels}
        truth="".join(p for p,row in outcomes.items() if row["expected"])
        if condition=="authored":
            signs={bits[p]:v["expected"] for p,v in outcomes.items()}
            blocked=scope["reference_exclusions"][f"original/{role}"]
        else:
            signs={bits[p]:v["sign"] if v["sign"]==v["expected"] else None for p,v in outcomes.items()}
            blocked=scope["projections"][f"original/{role}"]["rejected_scopes"]
        accepted={p for p in truth}
        exclusions=sum(bits[o["id"]] for o in options if o["scope"] in blocked and o["id"] not in accepted)
        local=tuple(sum(bits[p] for p in labels if p not in HOLDBACK[role] and signs[bits[p]] is value)
                    for value in (True,False))
        answers[role]=truth,local,exclusions,signs
    assert [answers[k][0] for k in ("japan","china-overlap","china-impasse")]==["ADF","BFG","BG"]
    silent={(r,t):(0,0) for r in range(2) for t in range(width+1)}
    for order, variant in product(("original","reversed"),("china-overlap","china-impasse")):
        roles=("japan",variant) if order=="original" else (variant,"japan")
        menus,local,scope,receipts=zip(*(answers[r] for r in roles),strict=True)
        truth=tuple(sum(bits[p] for p in menu) for menu in menus)
        for a,b in product(*menus):
            yield (order,variant,a+b),((width,truth,local,(bits[a],0,bits[b],0),scope),silent),receipts,None,public


def evaluate(repair_result,deferral_result):
    rule_sets={name:{k:v for k,v in obj["fit"].items() if k=="joint"}
               for name,obj in (("repair_and_handoff",repair_result),("deferral_and_handoff",deferral_result))}
    result={}
    for mode in ("authored","recorded_qwen"):
        with patch.object(fit,"SEEDS",new={**fit.SEEDS,"archive":ARCHIVE_SEED}):
            archived=fit.archived(list(rows(mode)))
        tracks={k:list(repair.cases(v)) for k,v in archived.items()}
        delayed=deferral.prepare(archived)
        result[mode]={
            "repair_and_handoff":repair.report(tracks,rule_sets["repair_and_handoff"]),
            "deferral_and_handoff":repair.report(delayed,rule_sets["deferral_and_handoff"]),
        }
        for item in result[mode]["deferral_and_handoff"].values():
            item["arms"]["always_defer"]=item["arms"].pop("always_packet")
    return {"scope":"The outer-space workshop is new to these policy fits. Cards and model outputs already exist. Source-contradicting signs and exclusions are withheld under the authored guard. Both training runs remain frozen.",
            "seed":ARCHIVE_SEED,"inputs":{str(p.relative_to(SPACE)):sha256(p.read_bytes()).hexdigest() for p in FILES},
            "holdback":HOLDBACK,"results":result}


if __name__=="__main__":
    states=[json.loads(Path(p).read_text()) for p in sys.argv[1:]]
    print(json.dumps(evaluate(*states),indent=2))
