"""Replay combined messages using recorded Mali model evidence and an independent ledger."""
from collections import Counter
from itertools import product
import json
from pathlib import Path

import bundle_policy as bundle
from offer_transfer import bits, load, readout, truthful_disclosure

HERE = Path(__file__).resolve().parent
MALI = HERE.parent / "mali"


def evaluate():
    case = load(MALI / "case.json")
    initial = MALI / "evidence/metrics.json"
    scale = HERE / "evidence/bundle-policy/results.json"
    data, fitted = load(initial), load(scale)
    policy = {(tuple(key[0]), *key[1:]): value for key, value in fitted["policy"]}
    labels = [p["id"] for p in case["options"]]
    menus = {"france-overlap": "AEG", "france-impasse": "AG", "russia": "CE"}
    scopes = data["published_scope_candidates"]["whole_set"]
    counts, paths = Counter(), {}
    for flipped in (False, True):
        order = "reversed" if flipped else "original"
        roles = case["roles"][::-1] if flipped else case["roles"]
        for variant in ("france-overlap", "france-impasse"):
            cards = ("russia", variant) if flipped else (variant, "russia")
            known, truth, masks = [], [], []
            for card in cards:
                tree = data["package_predictions"][card]
                known.append(tuple(bits(labels, [k for k in labels if tree[k]["sign"] is sign])
                                   for sign in (True, False)))
                truth.append(bits(labels, menus[card]))
                masks.append(bits(labels,[p["id"] for p in case["options"] if p["scope"] in scopes[card]]))
            expected = "AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
            for a,b in product(*(menus[card] for card in cards)):
                opening = (bits(labels,a),0,bits(labels,b),0)
                row = len(labels),tuple(truth),tuple(known),opening,tuple(masks)
                admitted = bundle.sp.opened(opening,known)
                for arm,script,table,cost in (
                    ("verify_first","verify_first",{},1),("offer_first","offer_first",{},1),
                    ("bundle_first","bundle_first",{},1),("bundle_open","bundle_open",{},1),
                    ("two_slots","bundle_first",{},2),("learned",bundle.START,policy,1),
                ):
                    outcome = []
                    solved,length,checks,bundles = bundle.rollout(row,script,table,cost,events=outcome)
                    turns = [{"role":r,"slot":r-2,"action":"opening","accepted":admitted[2*r],"excluded":0}
                             for r in range(2)] + outcome
                    claims = []
                    for turn in turns:
                        role = turn["role"]
                        accepts, excludes = ([p for i,p in enumerate(labels) if turn[side] & (1<<i)]
                                             for side in ("accepted","excluded"))
                        if accepts or excludes:
                            claim = {"id":f"claim-{len(claims)+1}","role":roles[role],"accepts":accepts,"excludes":excludes}
                            assert truthful_disclosure(claim,menus[cards[role]])
                            if turn["action"] == bundle.BUNDLE:
                                assert len(accepts) == len(excludes) == 1
                            claims.append(claim)
                            turn["claim_id"] = claim["id"]
                    ledger = readout(labels,roles,claims)
                    assert solved == (ledger["state"] == expected)
                    name = order,variant,arm
                    for key,value in (("certificates",solved),("slots",length),("checks",checks),("bundles",bundles)):
                        counts[*name,key] += value
                    paths["/".join((*name,a+b))] = {"ledger":ledger,"turns":turns,"claims":claims,"slots":length}
    return {"scope":"One previously evaluated model-evidence family, two speaker orders. Bundles are typed disclosures.",
            "inputs":{p.name:bundle.sha256(p.read_bytes()).hexdigest() for p in (initial,scale)},
            "metrics":bundle.sp.flatten(counts),"paths":paths}


if __name__ == "__main__":
    print(json.dumps(evaluate(),indent=2))
