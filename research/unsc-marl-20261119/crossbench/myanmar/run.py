"""Frozen package and scope verification for a new UNBench family."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
SPACE=HERE.parent/"space"
GUARD=SPACE/"guarded"
sys.path[:0]=[str(GUARD),str(SPACE),str(HERE.parent)]
import scope_sets
import exclusive_query as router
from decision_ledger import readout, truthful_disclosure

CASE=HERE/"case.json"
LOCK=HERE/"lock.json"
TRAINED=GUARD/"evidence/exclusive-query/results.json"
MENUS={"india":"ABG","uk-overlap":"BCD","uk-impasse":"CD"}
GROUPS={"focused-or-staged":{"broad"},"staged-or-broad":{"focused"},
        "broad-only":{"focused","staged"},"all":set()}
REFERENCE={"india":"focused-or-staged","uk-overlap":"staged-or-broad","uk-impasse":"broad-only"}
TEXT={"focused":"Both reporting cycles use confidential briefings only.",
      "staged":"The first cycle is confidential. Publication of an aggregate report in the second cycle is guaranteed.",
      "broad":"An aggregate report is published in the first cycle."}
SET_TEXT={"focused-or-staged":"Confidential briefings in the first cycle are required. Publication in the second cycle is optional.",
          "staged-or-broad":"An aggregate report must be published in one cycle. Publication in the first or second cycle meets the scope condition.",
          "broad-only":"Publication of an aggregate report in the first cycle is required.",
          "all":"Each of the three schedules is acceptable, including no publication."}


def load(path):
    return json.loads(path.read_text())


def suite():
    case=load(CASE)
    for role,mandate in case["cards"].items():
        forms=[("scope","all",SET_TEXT,{"private_mandate":mandate,"schedules":TEXT},
                "Select the exact timing restriction on publication. Assess this field only and ignore the other requirements. Respond with the answer letter.")]
        for opt in case["options"]:
            process=("ASEAN leads consultations and the United Nations provides support."
                     if opt["lead"]=="asean" else "ASEAN and the United Nations jointly chair the consultations.")
            shield=("The text explicitly protects the confidentiality of individual case information."
                    if opt["safeguard"] else "The text does not include an explicit confidentiality safeguard for individual case information.")
            package=" ".join((TEXT[opt["scope"]],process,shield))
            forms.append(("package",opt["id"],{"accept":"The package meets every requirement.","reject":"The package fails at least one requirement."},
                          {"private_mandate":mandate,"package":package},
                          "Apply all the private mandate's requirements jointly. Respond with the answer letter."))
        for kind,key_ ,answers,body,prompt in forms:
            for order,values in enumerate((list(answers),list(reversed(answers)))):
                labels="ABCD"[:len(values)]
                payload={**body,"choices":dict(zip(labels,(answers[k] for k in values),strict=True))}
                yield {"id":f"{role}/{kind}/{key_}/{order}","labels":labels,"values":values,
                       "messages":[{"role":"system","content":prompt},
                                    {"role":"user","content":json.dumps(payload,ensure_ascii=False)}]}


def audited(case):
    for role,expected in MENUS.items():
        actual={x["id"] for x in case["options"]
                if x["scope"] not in GROUPS[REFERENCE[role]] and
                (x["lead"]=="asean" if role=="india" else x["safeguard"])}
        assert actual==set(expected)


def score(rows):
    case=load(CASE)
    audited(case)
    labels=tuple(o["id"] for o in case["options"])
    plans={x["id"]:x for x in suite()}
    rubric,fields,counts={}, {}, Counter()

    def mask(names):
        return sum(1<<labels.index(k) for k in names)

    def names(bits):
        return [k for i,k in enumerate(labels) if bits&(1<<i)]

    def stable(prefix):
        order=[]
        for i in range(2):
            key=f"{prefix}/{i}"
            logits=rows[key]["label_logits"]
            top=max(logits)
            winners=[k for k,m in zip(plans[key]["values"],logits,strict=True) if m==top]
            order.append(winners[0] if len(winners)==1 else None)
        return order[0] if order[0]==order[1] else None,order

    for role in case["cards"]:
        verified={}
        for k in labels:
            vote,order=stable(f"{role}/package/{k}")
            sign=None if vote is None else vote=="accept"
            expected=k in MENUS[role]
            admitted=sign if sign is None or sign==expected else None
            counts["package","unknown" if sign is None else "correct" if sign==expected else "wrong"]+=1
            verified[k]={"raw":sign,"admitted":admitted,"orders":order,"expected":expected}
        winner,order=stable(f"{role}/scope/all")
        excluded=[o["id"] for o in case["options"] if winner and o["scope"] in GROUPS[winner]]
        approved=all(p not in MENUS[role] for p in excluded)
        fields[role]={"winner":winner,"orders":order,"exact":winner==REFERENCE[role],
                      "raw_exclusions":excluded,"admitted_exclusions":excluded if approved else []}
        counts["scope","unknown" if winner is None else "correct" if winner==REFERENCE[role] else "wrong"]+=1
        rubric[role]=verified
    table={(tuple(key[0]),*key[1:]):v for key,v in load(TRAINED)["policy"]}
    routes={}
    for order in ("original","reversed"):
        for variant in ("uk-overlap","uk-impasse"):
            cards=("india",variant) if order=="original" else (variant,"india")
            roles=case["roles"] if order=="original" else case["roles"][::-1]
            reference=tuple(mask(MENUS[k]) for k in cards)
            lookup=[{1<<i:rubric[k][label]["admitted"] for i,label in enumerate(labels)} for k in cards]
            observed=tuple(tuple(mask(label for label in labels if label not in case["later_only"][k]
                                       and rubric[k][label]["admitted"] is stance)
                                 for stance in (True,False)) for k in cards)
            scoped=tuple(mask(fields[k]["admitted_exclusions"]) for k in cards)
            for a,b in product(*(MENUS[k] for k in cards)):
                row=len(labels),reference,observed,(mask(a),0,mask(b),0),scoped
                tape={(role,t):(0,0) for role in range(2) for t in range(len(labels)+1)}
                first=router.sp.opened(row[3],observed)
                for arm,script,weights in (
                    ("never","never",{}),("direct","focused_first",{}),("scope","scope_first",{}),
                    ("late_scope",router.BASE,{}),("learned",router.BASE,table),
                ):
                    steps=[]
                    out=router.play((row,tape),script,weights,events=steps,recorded=lookup)
                    signs=[(i,0,first[2*i]) for i in range(2) if first[2*i]]
                    for turn in steps:
                        signs.extend(turn["disclosed"])
                    records=[]
                    for actor,negative,bits in signs:
                        claim={"id":f"claim-{len(records)+1}","role":roles[actor],
                               "accepts":names(bits) if not negative else [],
                               "excludes":names(bits) if negative else []}
                        assert truthful_disclosure(claim,MENUS[cards[actor]])
                        records.append(claim)
                    proof=readout(labels,roles,records)
                    expected="AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
                    assert out[0]==(proof["state"]==expected)
                    prefix=order,variant,arm
                    for key,value in zip(("correct","slots","checks","queries","answers","scope_queries"),out,strict=True):
                        counts[*prefix,key]+=value
                    counts[*prefix,"paths"]+=1
                    routes["/".join((*prefix,a+b))]={"ledger":proof,"messages":records,"trace":steps}
    return {"totals":{"/".join(k):v for k,v in counts.items()},"package":rubric,"scope":fields,"paths":routes}


def digests():
    root=HERE.parents[1]
    files=(Path(__file__),CASE,TRAINED,Path(router.__file__),Path(router.focus.__file__),
           Path(router.policy.__file__),Path(router.guard.__file__),HERE.parent/"decision_ledger.py",
           scope_sets.ENTAILMENT/"field_panel.py")
    return {str(p.resolve().relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in files}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("lock","run","replay"))
    p.add_argument("output",type=Path,nargs="?")
    p.add_argument("--model",type=Path)
    a=p.parse_args()
    if a.mode=="lock":
        audited(load(CASE))
        assert len(list(suite()))==48
        with LOCK.open("x") as f:
            json.dump({"hashes":digests(),"calls":48,"scope":"New assessment family. Verified-sender task guard. Held-back direct signs only available on lookup."},f,indent=2)
            f.write("\n")
        return
    assert load(LOCK)["hashes"]==digests()
    if a.mode=="run":
        scope_sets.field_panel.suite,scope_sets.field_panel.score=suite,score
        scope_sets.field_panel.main(a.model,a.output)
        return
    src=a.output/"predictions.jsonl"
    assert load(a.output/"complete.json")=={"records":48,"sha256":sha256(src.read_bytes()).hexdigest()}
    records=list(map(json.loads,src.read_text().splitlines()))
    for required,recorded in zip(suite(),records,strict=True):
        assert all(recorded[k]==v for k,v in required.items())
    result=score({x["id"]:x for x in records})
    assert json.loads(json.dumps(result))==load(a.output/"metrics.json")
    print(json.dumps({"records":len(records),"paths":len(result["paths"]),"hashes":len(digests()),"exact":True}))


if __name__=="__main__":
    main()
