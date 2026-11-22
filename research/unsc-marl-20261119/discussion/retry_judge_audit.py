"""Inspect which judgments change under each paired fixture edit."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path

import retry_judge as judge
import retry_process_score as mechanics


def pooled_field_maps(raw,plans):
    values={}
    for row in plans:
        case,_=row["id"].split("/")
        scores=values.setdefault(case,[Counter() for _ in judge.FIELDS])
        logits=raw[row["id"]]["label_logits"]
        peak=max(logits)
        for i,field in enumerate(judge.FIELDS):
            for value in judge.FIELDS[field]:
                scores[i][value]+=math.log(math.fsum(math.exp(z-peak)
                                                    for p,z in zip(row["profiles"],logits,strict=True)
                                                    if p[i]==value))
    result={}
    for case,fields in values.items():
        result[case]={}
        for name,score in zip(judge.FIELDS,fields,strict=True):
            tied=[v for v,n in score.items() if n==max(score.values())]
            result[case][name]=tied[0] if len(tied)==1 else None
    return result


def compare(predicted):
    totals=Counter()
    views={}
    for case,a in predicted.items():
        expected=dict(zip(judge.FIELDS,judge.EXPECTED[case],strict=True))
        grades={}
        for name,want in expected.items():
            v=a[name]
            grades[name]="uncertain" if v is None else "correct" if v==want else "wrong"
            totals[name,grades[name]]+=1
        views[case]=grades
    base="recovered"
    deltas={}
    for case in predicted:
        if case==base:
            continue
        reference=dict(zip(judge.FIELDS,judge.EXPECTED[case],strict=True))
        anchors=dict(zip(judge.FIELDS,judge.EXPECTED[base],strict=True))
        changed=[f for f in judge.FIELDS if anchors[f]!=reference[f]]
        kept=[f for f in judge.FIELDS if f not in changed]
        deltas[case]={"expected_to_change":changed,
                      "changed_to_reference":[k for k in changed if
                                              predicted[base][k]==anchors[k] and
                                              predicted[case][k]==reference[k]],
                      "both_correct_on_unchanged":[k for k in kept if
                                                   predicted[base][k]==predicted[case][k]==anchors[k]]}
    return {"counts":{"/".join(k):v for k,v in sorted(totals.items())},"grades":views,"contrasts":deltas}


def audit(path):
    rows={r["id"]:r for r in map(json.loads,path.read_text().splitlines())}
    plans=list(judge.suite())
    stable=judge.score(rows)
    inferred={case:{k:v["value"] for k,v in e["stable"].items()} for case,e in stable["cases"].items()}
    pooled=pooled_field_maps(rows,plans)
    checked={}
    for case,payload in judge.case_forms():
        trace=payload["trace"]
        actual=mechanics.proof(trace)
        removed=mechanics.proof([row for row in trace if row["event"]!="resend"])
        checked[case]={
            "new_idea":"new" if mechanics.owner_counts(trace)["new_in_resend"] else "same",
            "public_acceptance":"received" if "UNITED KINGDOM" in actual["delivered_B"] else "none",
            "causal_delivery":"changed" if actual["agreement"] and not removed["agreement"] else "unchanged",
            "authority":inferred[case]["authority"],
        }
    return {"official_two_order":compare(inferred),"exploratory_pool":compare(pooled),
            "typed_checks_with_model_authority":compare(checked),
            "raw_profile_order":{k:v["orders"] for k,v in stable["cases"].items()},
            "input_tokens":sum(len(r["input_ids"]) for r in rows.values()),
            "choice_mass_range":[min(r["legal_mass"] for r in rows.values()),
                                 max(r["legal_mass"] for r in rows.values())]}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("predictions",type=Path)
    args=p.parse_args()
    print(json.dumps(audit(args.predictions),indent=2))
