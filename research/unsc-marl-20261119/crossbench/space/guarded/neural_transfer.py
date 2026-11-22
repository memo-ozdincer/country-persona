"""Transfer the shared actor to the recorded Mali signs and verify its public ledger."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys

import neural_router as actor

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from decision_ledger import readout, truthful_disclosure

MALI = HERE.parents[1] / "mali"
MENUS = {"france-overlap":"AEG","france-impasse":"AG","russia":"CE"}


def read(path):
    return json.loads(path.read_text())


def evaluate(checkpoint=None):
    evidence = MALI/"evidence/metrics.json"
    checkpoint = checkpoint or HERE/"evidence/neural/results.json"
    case = read(MALI/"case.json")
    archive = read(evidence)
    weights = [actor.np.asarray(w) for w in read(checkpoint)["weights"]]
    labels = tuple(opt["id"] for opt in case["options"])
    source = archive["package_predictions"]
    fields = archive["published_scope_candidates"]["whole_set"]
    metrics, pairs = Counter(), Counter()
    records = {}

    def mask(names):
        return sum(1 << labels.index(k) for k in names)

    def names(value):
        return [k for i,k in enumerate(labels) if value & (1<<i)]

    for order in ("original","reversed"):
        for variant in ("france-overlap","france-impasse"):
            cards = (variant,"russia") if order=="original" else ("russia",variant)
            roles = case["roles"] if order=="original" else case["roles"][::-1]
            truth = tuple(mask(MENUS[k]) for k in cards)
            local = tuple(tuple(mask(k for k in labels if source[card][k]["sign"] is sign) for sign in (True,False))
                          for card in cards)
            assert all(not (yes & ~t or no & t) for (yes,no),t in zip(local,truth,strict=True))
            scopes = tuple(mask(o["id"] for o in case["options"] if o["scope"] in fields[card]) for card in cards)
            for left,right in product(*(MENUS[k] for k in cards)):
                row = len(labels),truth,local,(mask(left),0,mask(right),0),scopes
                tape = {(role,t):(0,0) for role in range(2) for t in range(len(labels)+1)}
                targets = "AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
                values = {}
                for schedule,script,parameters in (
                    ("neural",actor.BASE,weights),
                    *((name,name,None) for name in actor.routing.SCRIPTS),
                ):
                    votes = []
                    out = actor.play((row,tape),script,parameters,events=votes)
                    starting = actor.sp.opened(row[3],local)
                    turns = [{"actor":i,"slot":i-2,"action":"opening","accept":starting[2*i],"exclude":0}
                             for i in range(2)] + votes
                    log=[]
                    for turn in turns:
                        if not (turn["accept"] or turn["exclude"]):
                            continue
                        i=turn["actor"]
                        claim={"id":f"claim-{len(log)+1}","role":roles[i],
                               "accepts":names(turn["accept"]),"excludes":names(turn["exclude"])}
                        assert truthful_disclosure(claim,MENUS[cards[i]])
                        log.append(claim)
                    decision=readout(labels,roles,log)
                    assert out[0] == (decision["state"]==targets)
                    name=order,variant,schedule
                    for field,value in zip(("solved","slots","checks","overrides"),out,strict=True):
                        metrics[*name,field]+=value
                    records["/".join((*name,left+right))]={"decision":decision,"claims":log,"steps":turns}
                    values[schedule]=out
                for schedule,val in values.items():
                    pairs[order,variant,schedule,str(val[0]),str(values["neural"][0])] += 1
    return {"scope":"Previously exposed family, archived model signs and exact recorded scope receipt.",
            "inputs":{p.name:actor.sha256(p.read_bytes()).hexdigest() for p in (evidence,checkpoint)},
            "metrics":actor.sp.flatten(metrics),"pairs":actor.sp.flatten(pairs),"paths":records}


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint",type=Path)
    print(json.dumps(evaluate(p.parse_args().checkpoint),indent=2))
