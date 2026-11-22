"""Compare judge decisions to locked source keys and verify rendering separately."""
from itertools import product
import json

import review

fixture=review.fixture
HERE=review.HERE
TOL=1e-9


def assess(probe, outputs):
    margins, choices={},{}
    for order,mapping in review.LABELS.items():
        row=outputs[f"{probe['id']}/{order}"]
        positive,negative=[next(letter for letter,meaning in mapping.items() if meaning==target)
                           for target in ("supported","unsupported")]
        margins[order]=row["logits"][positive]-row["logits"][negative]
        choices[order]=mapping[row["label"]]
    consensus=choices["ab"] if choices["ab"]==choices["ba"] else "abstain"
    mean_margin=sum(margins.values())/2
    averaged="supported" if mean_margin > 0 else "unsupported" if mean_margin < 0 else "abstain"
    return {"raw":choices,"margins":margins,"consensus":consensus,"mean":averaged,
            "supported":probe["supported"]}


def relation_is_registered(rule_index, cards, candidate):
    relation=fixture.RELATIONS[rule_index]
    if candidate!=relation["text"] or len(cards)!=len(relation["requires"]):
        return False
    return all(cards.get(key)==fixture.BLOCKS[key]["text"] for key in relation["requires"])


def compile_record(early, late, allow):
    fixture.validate_slots(early,late)
    records={key:fixture.BLOCKS[key]["text"] for key in (early,late) if key is not None}
    lead=[row["text"] for row in fixture.PUBLIC]+list(records.values())
    parts=lead.copy()
    score=sum(row["weight"] for row in fixture.PUBLIC)+sum(fixture.BLOCKS[key]["weight"] for key in records)
    admitted=[]
    mutations=0
    for index,rule in enumerate(fixture.RELATIONS):
        anchor=rule["text"]
        ok=relation_is_registered(index,records,anchor)
        if ok:
            assert not relation_is_registered(index,records,anchor+" Added words.")
            for key in records:
                changed=records|{key:records[key]+" Altered."}
                assert not relation_is_registered(index,changed,anchor)
            foreign={key+"-foreign":value for key,value in records.items()}
            assert not relation_is_registered(index,foreign,anchor)
            mutations+=len(records)+2
            if allow[index]:
                parts.append(anchor)
                admitted.append(rule["id"])
                score+=rule["weight"]
    final="\n\n".join(parts)
    assert final.split("\n\n")[:len(lead)]==lead
    assert len(final.split())<=fixture.CASE["word_cap"]
    if admitted:
        assert fixture.verify(early,late,final)["released_70"]==score
    else:
        assert len(parts)==len(lead)
    return {"released_70":score,"rendered_relations":admitted,"text":final,"tamper_checks":mutations}


def deployment(judgments):
    bank={}
    for name in ("rule_only","mean","consensus"):
        allow=[True,True] if name=="rule_only" else [
            judgments[k][name]=="supported" for k in ("ru-canonical","a3-canonical")]
        bank[name]={f"{i}/{j}":compile_record(
                None if i is None else fixture.OPTIONS[0][i],
                None if j is None else fixture.OPTIONS[1][j],allow)
            for i,j in product((0,1,None),repeat=2)}
    exact,_=fixture.cases()
    for key,row in exact.items():
        assert row["grade"]["released_70"]==bank["rule_only"][key]["released_70"]
    # Use the archived canonical editor's choices, which were the same in both stress forms.
    text_archive=json.loads((HERE.parent/"text-decoder/lexical-contrast/scores.json").read_text())
    editors=[{int(t):v["orders"][0]["raw"] for t,v in row["observations"].items()}
             for row in text_archive.values()]
    assert all(choice=={0:0,1:1} for choice in editors)
    rows=[]
    for q,prior in product(fixture.RATES,fixture.PRIORS):
        result={}
        for name,records in bank.items():
            ready={key:{"grade":item} for key,item in records.items()}
            arrival=max(fixture.receipt_value(ready,q,prior,{None:a,0:b,1:b})
                        for a,b in product((0,1),repeat=2))
            value=fixture.receipt_value(ready,q,prior,{None:0,**editors[0]})
            result[name]={"best_arrival":float(arrival),"read_content":float(value),"gain":float(value-arrival),
                          "verifier_calls":0. if name=="rule_only" else 2*float(q*q)}
            assert value<=fixture.evaluate(exact,q,prior)["content_ceiling"]+TOL
        rows.append({"delivery":float(q),"first_prior":float(prior),"scores":result})
    return {"records":bank,"settings":rows}


def run():
    review.locked()
    outputs=json.loads((HERE/"verified.json").read_text())["outputs"]
    checks={row["id"]:assess(row,outputs) for row in review.probes()}
    cases={name:{key:(row[name] if name in ("mean","consensus") else row["raw"][name])
                 for key,row in checks.items()} for name in ("ab","ba","mean","consensus")}
    counts={}
    for name,decision in cases.items():
        counts[name]={"exact":0,"abstentions":0,"supported_admitted":0,"unsupported_admitted":0}
        for key,label in decision.items():
            truth=checks[key]["supported"]
            counts[name]["exact"]+=label==("supported" if truth else "unsupported")
            counts[name]["abstentions"]+=label=="abstain"
            counts[name]["supported_admitted"]+=label=="supported" and truth
            counts[name]["unsupported_admitted"]+=label=="supported" and not truth
    return {"judge":counts,"observations":checks,"deployment":deployment(checks),
            "verified_sha256":fixture.pin(HERE/"verified.json")}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
