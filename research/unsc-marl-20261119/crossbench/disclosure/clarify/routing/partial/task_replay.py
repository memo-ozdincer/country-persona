"""Replay the partial-observation policy on stored model-inferred signs."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

from train import ROOT, restore, terminal
from preserve import select

JUDGE = ROOT.parents[3]/"judge/entailment"
sys.path.insert(0,str(JUDGE))
from package_panel import inputs, project, guarded, source_paths
from partial_dispatch import simulate as control
from episode import judge, readout
from environment import record
from joint import restore as full_restore


def run_policy(case, first, observations, truth, policy, mode="raw"):
    labels = tuple(o["id"] for o in case["options"])
    roles = case["roles"]
    width = len(labels)
    state, role, full = (0,0,0,0), 1, (1 << width)-1
    local = [list(o) for o in observations]
    claims, events = [], []

    def attempt(i, bit, step):
        nonlocal state
        label = labels[bit.bit_length()-1]
        yes, no = local[i]
        if not bit & (yes | no):
            events.append({"step":step,"role":i,"option":label,"status":"unknown"})
            return False
        actual = bool(truth[i] & bit)
        raw = json.dumps({"stance":"accept" if bit&yes else "exclude","option":label})
        status, claim = judge(raw,roles[i],label,actual,f"claim-{len(claims)+1}")
        events.append({"step":step,"role":i,"option":label,"status":status})
        if claim is None:
            local[i] = [yes & ~bit, no & ~bit]
            return False
        claims.append(claim)
        state=record(state,i,bit,actual)
        return True

    for i, name in enumerate(first):
        attempt(i,1<<labels.index(name),i-2)
    for k in range(width):
        if terminal(state,full):
            break
        bit, _, _, target = select(local,state,role,k,width,policy,mode)
        if bit:
            role = target if attempt(role,bit,k) else 1-role
        else:
            events.append({"step":k,"role":role,"status":"pass"})
            role=1-role
    return {"claims":claims,"events":events,"readout":readout(labels,roles,claims)}


def compare(policy, manifests, include_guards=False):
    old=guarded(full_restore(json.loads(source_paths()["policy"].read_text())))
    result={}
    for source, manifest in manifests.items():
        decisions=manifest["decisions"]
        rows, counts={},Counter()
        for family,case,item in inputs():
            labels=tuple(o["id"] for o in case["options"])
            truth=tuple(project(case["options"],card["expected"]) for card in item["cards"])
            known=[]
            for i in (0,1):
                values=[decisions[f"{family}/{i}/{label}"]["accept"] for label in labels]
                known.append(tuple(sum(1<<k for k,v in enumerate(values) if v is sign)
                                   for sign in (True,False)))
            starts=product(*([label for k,label in enumerate(labels) if mask&(1<<k)] for mask in truth))
            expected="AGREEMENT_POSSIBLE" if item["outcome"]=="agreement" else "IMPASSE"
            for first in starts:
                compare={
                    "exclusion_script":control(case,first,known,truth,"retain_exclusions",old,True),
                    "original_learned":control(case,first,known,truth,"learned",old,True),
                    "partial_learned":run_policy(case,first,known,truth,policy),
                }
                if include_guards:
                    for mode in ("local","availability","strict"):
                        compare[f"guard_{mode}"]=run_policy(case,first,known,truth,policy,mode)
                for mode, answer in compare.items():
                    rows[f"{family}/{mode}/{''.join(first)}"]=answer
                    counts[family,mode,"presentations"] += 1
                    counts[family,mode,"certificates"] += answer["readout"]["state"]==expected
                    counts[family,mode,"continuation_slots"] += sum(e["step"]>=0 for e in answer["events"])
                    counts[family,mode,"rejected_signs"] += sum(e["status"]=="untruthful" for e in answer["events"])
        result[source]={"metrics":{"/".join(k):v for k,v in counts.items()},"traces":rows}
    return result


def sources():
    base={
        "direct_package":JUDGE/"package-evidence/metrics.json",
        "field_invariants":JUDGE/"field-evidence/invariant-dispatch.json",
    }
    return base,{str(p.relative_to(ROOT.parents[3])):sha256(p.read_bytes()).hexdigest()
                 for p in base.values()}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("policy",type=Path)
    p.add_argument("--with-guards",action="store_true")
    a=p.parse_args()
    files, hashes = sources()
    evaluated=compare(restore(json.loads(a.policy.read_text())),
                    {k:json.loads(path.read_text()) for k,path in files.items()},a.with_guards)
    print(json.dumps({"input_sha256":hashes,"outcomes":evaluated},indent=2))
