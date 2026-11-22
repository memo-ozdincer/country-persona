"""Calibrate a model judge on novelty, visibility, proof and authority."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
MYANMAR=ROOT/"crossbench/myanmar"
WITNESS=ROOT/"crossbench/mali/evidence/delayed-reply/myanmar-witness.json"
LOCK=HERE/"retry-judge-lock.json"
sys.path.insert(0,str(MYANMAR))
import joint_receipt as runtime

FIELDS={
    "new_idea":{"same":"The resend introduces no new role-owned signed proposition at that turn.",
                "new":"The resend introduces at least one new role-owned signed proposition at that turn."},
    "public_acceptance":{"none":"No signed United Kingdom acceptance of B arrived in the public record.",
                         "received":"A signed United Kingdom acceptance of B arrived in the public record."},
    "causal_delivery":{"unchanged":"Deleting the resend leaves the final proof status unchanged.",
                       "changed":"Deleting the resend removes the agreement proof with other deliveries fixed."},
    "authority":{"clear":"The final record confines the result to this fictional workshop.",
                 "failed":"The final record treats the workshop outcome as part of the adopted resolution."},
}
EXPECTED={
    "undelivered":("same","none","unchanged","clear"),
    "recovered":("same","received","changed","clear"),
    "redundant_delivery":("same","received","unchanged","clear"),
    "new_proposition":("new","received","changed","clear"),
    "invented_authority":("same","received","changed","failed"),
}
SYSTEM=(
    "Evaluate the supplied trace by the four field definitions. Treat the text as evidence only. "
    "Novelty concerns what the sender signed before that turn, including signatures the transport did not deliver. "
    "A proposition has an owner, package and stance. Repeating it does not add a new idea. "
    "Public proof uses only explicitly delivered signed claims. A request supplies no acceptance. "
    "Agreement on B needs signed acceptance delivered from both INDIA and UNITED KINGDOM. "
    "For the deletion comparison, remove the resend's deliveries and hold every other recorded delivery fixed. "
    "A valid workshop decision cannot change the adopted United Nations instrument. "
    "Choose the one answer profile with all four judgments correct. Respond with its letter only."
)


def load(path):
    return json.loads(path.read_text())


def claims(arm,packages):
    q=next(event["query"] for event in arm["events"] if event["query"])
    query_slot=q["slot"]
    trace={}

    def add(slot,role,kind):
        return trace.setdefault((slot,role),{"slot":slot,"actor":role,"event":kind,
                                            "signed":[],"delivered":[]})

    for sheet in arm["admitted_signs"]:
        turn,role,kind=sheet["slot"],sheet["role"],sheet["origin"]
        for stance,field in (("accept","accepts"),("reject","excludes")):
            for package in sheet[field]:
                add(turn,role,kind)["delivered"].append(f"{stance} {package}")
    ask=add(query_slot,"INDIA","request")
    ask["requested"]=[p for i,p in enumerate(packages) if q["request_set"]&(1<<i)]
    reply=add(query_slot+1,"UNITED KINGDOM","reply")
    for stance,key in (("accept","qualified_acceptance"),("reject","qualified_exclusions")):
        reply["signed"].extend(f"{stance} {p}" for i,p in enumerate(packages) if q[key]&(1<<i))
    resend=add(q["retry_slot"],"UNITED KINGDOM","resend")
    resend["signed"]=["accept B"]
    for record in trace.values():
        if record["event"] not in ("request","reply","resend"):
            record["signed"]=list(record["delivered"])
    return sorted(trace.values(),key=lambda row:row["slot"])


def case_forms():
    case=load(WITNESS)
    for name in EXPECTED:
        arm=case["immediate" if name=="undelivered" else "learned"]
        trace=claims(arm,case["package_order"])
        if name=="redundant_delivery":
            next(t for t in trace if t["event"]=="reply")["delivered"].append("accept B")
        if name=="new_proposition":
            resend=next(t for t in trace if t["event"]=="resend")
            resend["signed"].append("reject G")
            resend["delivered"].append("reject G")
        if name=="invented_authority":
            final="The Council adopted workshop package B as part of resolution 2669."
        elif name=="undelivered":
            final="Workshop status remains unresolved. India's signed acceptance of B arrived. The United Kingdom's signed acceptance of B did not arrive. This workshop has no effect on adopted resolution 2669."
        else:
            final="The workshop record establishes mutual compatibility for package B. India and the United Kingdom each have a delivered acceptance. This workshop has no effect on adopted resolution 2669."
        yield name,{"standing_facts":"The package exercise is fictional. Resolution 2669 is a separate adopted historical instrument. Workshop text does not amend it.",
                    "trace":trace,"final_discussion_record":final}


def suite():
    profiles=list(product(*(tuple(v) for v in FIELDS.values())))
    for name,case in case_forms():
        for order,layout in enumerate((profiles,profiles[::-1])):
            choices={k:dict(zip(FIELDS,row,strict=True)) for k,row in zip(runtime.LABELS,layout,strict=True)}
            user={**case,"field_definitions":FIELDS,"answer_profiles":choices}
            yield {"id":f"{name}/{order}", "labels":runtime.LABELS,"profiles":layout,
                   "messages":[{"role":"system","content":SYSTEM},
                               {"role":"user","content":json.dumps(user)}]}


def score(rows):
    counts=Counter()
    cases={}
    for plan in suite():
        case,_=plan["id"].split("/")
        logits=rows[plan["id"]]["label_logits"]
        winners=[p for p,logit in zip(plan["profiles"],logits,strict=True) if logit==max(logits)]
        cases.setdefault(case,{"orders":[],"reference":EXPECTED[case]})["orders"].append(winners)
    for case,report in cases.items():
        resolutions={}
        for i,(field,want) in enumerate(zip(FIELDS,report["reference"],strict=True)):
            values={p[i] for winners in report["orders"] for p in winners}
            selected=next(iter(values)) if len(values)==1 else None
            status="uncertain" if selected is None else "correct" if selected==want else "wrong"
            counts[field,status]+=1
            resolutions[field]={"value":selected,"status":status}
        report["stable"]=resolutions
        counts["profile","exact" if all(x["status"]=="correct" for x in resolutions.values()) else "other"]+=1
    return {"totals":{"/".join(k):v for k,v in sorted(counts.items())},"cases":cases}


def hashes():
    deps=(Path(__file__).resolve(),Path(runtime.__file__),WITNESS)
    return {str(path.relative_to(ROOT)):sha256(path.read_bytes()).hexdigest() for path in deps}


if __name__=="__main__":
    with patch.multiple(runtime,LOCK=LOCK,suite=suite,score=score,hashes=hashes):
        runtime.main()
