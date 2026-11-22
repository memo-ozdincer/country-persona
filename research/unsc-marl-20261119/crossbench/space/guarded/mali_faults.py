"""Replay every single-site continuation fault on the recorded Mali package signs."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path

import robust_bundle as guarded
from ledger_replay import read

HERE = Path(__file__).resolve().parent
MALI = HERE.parents[1] / "mali"
MENUS = {"france-overlap":"AEG","france-impasse":"AG","russia":"CE"}


def evaluate(include_retry=False):
    data = read(MALI/"evidence/metrics.json")
    case = read(MALI/"case.json")
    evidence = HERE/"evidence/results.json"
    previous = HERE.parent/"evidence/bundle-policy/results.json"

    def policy(path):
        return {(tuple(key[0]),*key[1:]):move for key,move in read(path)["policy"]}

    labels = [p["id"] for p in case["options"]]
    width = len(labels)
    inputs = {"case":MALI/"case.json","archived_pred":MALI/"evidence/metrics.json",
              "new_policy":evidence,"old_policy":previous}
    scopes = data["published_scope_candidates"]["whole_set"]
    totals, paired = Counter(), Counter()

    def mask(items):
        return sum(1<<labels.index(k) for k in items)

    arms = (("bundle_selective",{},False),("bundle_atomic",{},True),
            ("old_fit",policy(previous),False),("guard_fit",policy(evidence),False))
    recovery = ()
    if include_retry:
        import retry
        path = HERE / "evidence/retry/results.json"
        inputs["retry_policy"] = path
        recovered = {tuple(key): value for key,value in read(path)["policy"]}
        recovery = (("terminal_retry",retry.BASE,{}),("always_retry","always_retry",{}),
                    ("retry_fit",retry.BASE,recovered))
    for layout in ("original","reversed"):
        for variant in ("france-overlap","france-impasse"):
            cards = (variant,"russia") if layout=="original" else ("russia",variant)
            truth = tuple(mask(MENUS[c]) for c in cards)
            known = []
            for i,card in enumerate(cards):
                statuses = data["package_predictions"][card]
                signs = tuple(mask(k for k in labels if statuses[k]["sign"] is v)
                              for v in (True,False))
                assert not signs[0] & ~truth[i] and not signs[1] & truth[i]
                known.append(signs)
            checks = tuple(mask(p["id"] for p in case["options"] if p["scope"] in scopes[c]) for c in cards)
            for a,b in product(*(MENUS[k] for k in cards)):
                row = width,truth,tuple(known),(mask(a),0,mask(b),0),checks
                sites = [(r,t) for r in range(2) for t in range(width+1)]
                clean = dict.fromkeys(sites,(0,0))
                for error,(actor,slot),label in product(("drop","flip"),sites,labels):
                    tape = dict(clean)
                    bit = mask([label])
                    tape[actor,slot] = (bit,0) if error=="drop" else (0,bit)
                    outcomes = {}
                    for arm,table,atomic in arms:
                        solved,turns,_,_,rejected,dropped = guarded.rollout((row,tape),guarded.START,table,atomic)
                        outcomes[arm] = solved
                        key=layout,variant,error,arm
                        for name,value in (("presentations",1),("solved",solved),("slots",turns),
                                           ("fault_reached",bool(rejected or dropped))):
                            totals[*key,name] += value
                    for arm,mode,table in recovery:
                        solved,turns,_,attempts = retry.play((row,tape),mode,table)
                        outcomes[arm] = solved
                        key = layout,variant,error,arm
                        for name,value in (("presentations",1),("solved",solved),("slots",turns),
                                           ("resends",attempts)):
                            totals[*key,name] += value
                    for arm,value in outcomes.items():
                        paired[layout,variant,error,arm,str(outcomes["bundle_selective"]),str(value)] += 1
    return {"scope":"Exactly one drop or inversion per presentation, including unused sites. Saved Qwen signs and exact scope returns. No new model calls.",
            "inputs":{k:guarded.sha256(p.read_bytes()).hexdigest() for k,p in inputs.items()},
            "counts":guarded.sp.flatten(totals),"paired":guarded.sp.flatten(paired)}


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--retry", action="store_true")
    print(json.dumps(evaluate(p.parse_args().retry),indent=2))
