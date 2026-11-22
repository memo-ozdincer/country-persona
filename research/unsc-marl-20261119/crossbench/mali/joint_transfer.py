"""Transfer Myanmar's locked compound-receipt evaluation to Mali."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
import math
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
MYANMAR=HERE.parent/"myanmar"
sys.path.insert(0,str(MYANMAR))
import joint_receipt as probe
import joint_reply as reply
import target_set as group
from decision_ledger import readout, truthful_disclosure

mali=SimpleNamespace(**runpy.run_path(str(HERE/"transfer.py")))

FIELDS={
    "scope":mali.SETS,
    "term":{"final":"A final extension with no provision for further renewal is required.",
            "either":"A final term or a renewable term is acceptable."},
    "report":{"public":"Public aggregate reporting is required.",
              "either":"Public or restricted aggregate reporting is acceptable."},
}
PROFILES={
    "france-overlap":("staged-or-broad","either","public"),
    "france-impasse":("broad-only","either","public"),
    "russia":("focused-or-staged","final","either"),
}
EXCLUDES={
    "focused-or-staged":{"broad"},"staged-or-broad":{"focused"},
    "broad-only":{"focused","staged"},"all":set(),None:set(),
}
WITHHELD={"france-overlap":"BF","france-impasse":"BF","russia":"DE"}
REFERENCE=HERE/"evidence/metrics.json"
TRAINED=MYANMAR/"evidence/joint-receipt/routing-results.json"
LOCK=HERE/"joint-transfer-lock.json"


def suite():
    profiles=list(product(*(tuple(v) for v in FIELDS.values())))
    assert len(profiles)==len(probe.LABELS)
    for role,card in mali.load(mali.CASE)["cards"].items():
        for index,order in enumerate((profiles,profiles[::-1])):
            choices={letter:dict(zip(FIELDS,profile,strict=True))
                     for letter,profile in zip(probe.LABELS,order,strict=True)}
            payload={"private_mandate":card,"field_definitions":FIELDS,"answer_profiles":choices}
            yield {"id":f"{role}/{index}","labels":probe.LABELS,"profiles":order,"messages":[
                {"role":"system","content":"Read the fictional private mandate. Identify its requirements for independent monitoring timing, extension renewal and public reporting. Choose the single answer profile whose three definitions all match. Respond with only its letter."},
                {"role":"user","content":json.dumps(payload,ensure_ascii=False)},
            ]}


def get_fields(layouts, mode):
    if mode=="pooled":
        # Freeze the equal-weight marginal rule from Myanmar.
        readings=[]
        for field,choices in enumerate(FIELDS.values()):
            scores={}
            for choice in choices:
                scores[choice]=sum(math.log(math.fsum(math.exp(l-max(layout.values()))
                                                       for p,l in layout.items() if p[field]==choice))
                                   for layout in layouts)
            winners=[choice for choice,score in scores.items() if score==max(scores.values())]
            readings.append(winners[0] if len(winners)==1 else None)
        return tuple(readings)
    selected=layouts if mode=="stable" else [layouts[int(mode)]]
    profiles=[p for layout in selected for p,l in layout.items() if l==max(layout.values())]
    return tuple(values.pop() if len(values)==1 else None for values in map(set,zip(*profiles,strict=True)))


def certify(case,menus,signs,scopes,weights):
    labels=tuple(opt["id"] for opt in case["options"])
    width=len(labels)
    masks={label:1<<i for i,label in enumerate(labels)}
    variants=(
        ("no_query","never",{},group.enabled),("scope_first","scope_first",{},group.enabled),
        ("focused_set",group.BASE,{},group.enabled),("compound_first","set_first",{},reply.enabled),
        ("compound_fixed",group.BASE,{},reply.enabled),("compound_learned",group.BASE,weights,reply.enabled),
    )
    totals,paths=Counter(),{}
    for order in ("original","reversed"):
        for variant in ("france-overlap","france-impasse"):
            cards=(variant,"russia")
            roles=case["roles"]
            if order=="reversed":
                cards,roles=cards[::-1],roles[::-1]
            truth=tuple(sum(masks[p] for p in menus[k]) for k in cards)
            known=tuple(tuple(sum(masks[p] for p in labels if p not in WITHHELD[k] and signs[k][p] is value)
                              for value in (True,False)) for k in cards)
            scope=tuple(sum(masks[p] for p in scopes[k]) for k in cards)
            recorded=[{masks[p]:signs[k][p] for p in labels} for k in cards]
            tape={(r,t):(0,0) for r in range(2) for t in range(width+1)}
            for left,right in product(*(sorted(menus[k]) for k in cards)):
                row=(width,truth,known,(masks[left],0,masks[right],0),scope)
                opening=group.SP.opened(row[3],known)
                for arm,mode,fit,enabled in variants:
                    steps=[]
                    with enabled():
                        result=group.policy.play((row,tape),mode,fit,events=steps,recorded=recorded)
                    claims=[]
                    deltas=[(r,0,opening[2*r]) for r in range(2) if opening[2*r]]
                    for event in steps:
                        query=event["query"]
                        if query and "request_set" in query:
                            for r,negative,bits in event["disclosed"]:
                                assert r==query["respondent"]
                                if query.get("lookup")=="joint_fields":
                                    key="qualified_exclusions" if negative else "qualified_acceptance"
                                    assert not bits&~query[key]
                                else:
                                    assert bits==query["target"]
                        deltas.extend(event["disclosed"])
                    for actor,negative,bits in deltas:
                        names=[p for p in labels if masks[p]&bits]
                        claim={"id":f"m{len(claims)+1}","role":roles[actor],
                               "accepts":[] if negative else names,"excludes":names if negative else []}
                        assert truthful_disclosure(claim,menus[cards[actor]])
                        claims.append(claim)
                    verdict=readout(labels,roles,claims)
                    expected="AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
                    assert result[0]==(verdict["state"]==expected)
                    prefix=(order,variant,arm)
                    for metric,value in zip(("solved","slots","checks","requests","answers","scope_queries"),
                                            result,strict=True):
                        totals[*prefix,metric]+=value
                    totals[*prefix,"presentations"]+=1
                    paths["/".join((*prefix,left+right))]={"steps":steps,"claims":claims,"verdict":verdict}
    return {"totals":group.SP.flatten(totals),"paths":paths}


def evaluate(rows):
    case=mali.load(mali.CASE)
    menus=mali.audited_menus(case)
    weights=group.decode(mali.load(TRAINED)["training"])
    order_maps={}
    for plan in suite():
        role,_=plan["id"].split("/")
        order_maps.setdefault(role,[]).append(dict(zip(plan["profiles"],rows[plan["id"]]["label_logits"],strict=True)))
    results={}
    for mode in ("0","1","stable","pooled","archived","authored"):
        counts,fields,signs,scope=Counter(),{},{},{}
        archived=mali.load(REFERENCE)
        for role in case["cards"]:
            if mode=="archived":
                fields[role]=None
                exclusions=set(archived["published_scope_candidates"]["whole_set"][role])
                raw={p:d["sign"] for p,d in archived["package_predictions"][role].items()}
            else:
                fields[role]=PROFILES[role] if mode=="authored" else get_fields(order_maps[role],mode)
                timing,term,report=fields[role]
                for pred,truth in zip(fields[role],PROFILES[role],strict=True):
                    counts["field","unknown" if pred is None else "correct" if pred==truth else "wrong"]+=1
                exclusions=EXCLUDES[timing]
                raw={}
                for p in case["options"]:
                    checks=(
                        None if timing is None else p["scope"] not in exclusions,
                        None if term is None else term=="either" or p["term"]==term,
                        None if report is None else report=="either" or p["report"]==report,
                    )
                    raw[p["id"]]=False if False in checks else None if None in checks else True
            scope[role]=[p["id"] for p in case["options"] if p["scope"] in exclusions]
            if any(p in menus[role] for p in scope[role]):
                counts["scope","guarded"]+=1
                scope[role]=[]
            signs[role]={}
            for p,pred in raw.items():
                correct=pred==(p in menus[role])
                counts["package","unknown" if pred is None else "correct" if correct else "wrong"]+=1
                signs[role][p]=pred if correct else None
        results[mode]={"counts":group.SP.flatten(counts),"fields":fields,"package":signs,"scope":scope,
                       **certify(case,menus,signs,scope,weights)}
    return {"totals":{f"{mode}/{k}":v for mode,d in results.items() for k,v in d["counts"].items()},
            "holdback":WITHHELD,"conditions":results}


def hashes():
    root=HERE.parents[1]
    prior=mali.load(TRAINED)["sha256"]
    assert all(sha256((root/n).read_bytes()).hexdigest()==d for n,d in prior.items())
    files=(Path(__file__).resolve(),Path(probe.__file__),HERE/"transfer.py",mali.CASE,REFERENCE,TRAINED)
    return {**prior,**{str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in files}}


def main():
    with patch.multiple(probe,suite=suite,score=evaluate,hashes=hashes,LOCK=LOCK):
        probe.main()


if __name__=="__main__":
    main()
