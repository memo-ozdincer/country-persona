"""Apply exact-span marks and compute paired policy values on the native writer bank."""
from collections import Counter
from itertools import product
import json

import generate as study

fixture=study.fixture
HERE=study.HERE
PARENT=study.PARENT


def grade(row, mark, require_pair):
    ids=row["receipts"]
    response=row["reply"]
    text=response["text"]
    assert mark["span"]==text and str(mark["reason"]).strip()
    sources={key:fixture.BLOCKS[key]["text"] for key in ids if key is not None}
    assert set(mark["sources"])<=set(sources)
    assert mark["status"] in {"met","clear","unsupported","uncertain","none"}
    assert (text=="NONE")==(mark["status"]=="none")
    supported=[rule for rule in fixture.RELATIONS if all(x in sources for x in rule["requires"])]
    if mark["status"]=="met":
        assert len(supported)==1 and mark["relation"]==supported[0]["id"]
        assert set(mark["sources"])==set(supported[0]["requires"])
    else:
        assert mark["relation"] is None
    parts=[b["text"] for b in fixture.PUBLIC]+list(sources.values())
    authored_standalone=sum(b["weight"] for b in fixture.PUBLIC)+sum(fixture.BLOCKS[x]["weight"] for x in sources)
    use_native=not require_pair or len(sources)==2
    drop=mark["status"]=="none" or not use_native
    if not drop:
        parts.append(text)
    record="\n\n".join(parts)
    blockers=[]
    if use_native:
        if response["termination"]!="complete":
            blockers.append("generation_"+response["termination"])
        if not text or len(text.split())>42:
            blockers.append("comparison_length")
        if mark["status"] in {"unsupported","uncertain"}:
            blockers.append("guard_"+mark["status"])
    if len(record.split())>fixture.CASE["word_cap"]:
        blockers.append("final_word_cap")
    joint=supported[0]["weight"] if not drop and mark["status"]=="met" else 0
    raw=authored_standalone+joint
    return {"text":record,"points":raw,"released":raw if not blockers else 0,
            "joint_retention":joint if not blockers else 0,"standalone":authored_standalone,
            "blockers":blockers,"sources":[{"id":key,"quote":sources[key]} for key in mark["sources"]]}


def policy_states():
    base=json.loads((PARENT/"text-decoder/scores.json").read_text())
    stress=json.loads((PARENT/"text-decoder/lexical-contrast/scores.json").read_text())
    all_choices=[{int(truth):m["ab"]["raw_mapped"] for truth,m in v["decisions"].items()}
                 for v in base["modes"].values()]
    all_choices.extend({int(truth):v["orders"][0]["raw"] for truth,v in m["observations"].items()}
                       for m in stress.values())
    assert all(x=={0:0,1:1} for x in all_choices)
    return {0:0,1:1,None:base["absent"]["action"]}


def expected(bank,q,p,policy,metric):
    out=fixture.Q(0)
    for truth,early,late in product((0,1),repeat=3):
        observed=truth if early else None
        clause=policy[observed] if late else None
        mass=(p if not truth else 1-p)*(q if early else 1-q)*(q if late else 1-q)
        out+=bank[f"{observed}/{clause}"][metric]*mass
    return float(out)


def run():
    locked=study.locked()
    data=json.loads((HERE/"verified.json").read_text())["outputs"]
    marks=json.loads((HERE/"marks.json").read_text())
    assert set(marks)==set(data)==set(locked["requests"])
    modes={}
    for name,guard in (("verbatim_plus_native",False),("require_both_receipts",True)):
        modes[name]={key:grade(data[receipt],marks[receipt],guard) for key,receipt in locked["receipt_keys"].items()}
    reference,_=fixture.cases()
    modes["verbatim"]={key:{"released":g["grade"]["sections"]["public"]+g["grade"]["sections"]["standalone"],
                              "joint_retention":0} for key,g in reference.items()}
    modes["authored_comparison"]={key:{"released":g["grade"]["released_70"],
                                         "joint_retention":g["grade"]["sections"]["relation"]}
                                    for key,g in reference.items()}
    informed=policy_states()
    results=[]
    for q,p in product(fixture.RATES,fixture.PRIORS):
        report={}
        for key,bank in modes.items():
            blind={i:int(p<fixture.Q(1,2)) for i in (0,1,None)}
            report[key]={metric:{name:expected(bank,q,p,policy,metric)
                                 for name,policy in (("read_text",informed),("best_arrival_on_authored",blind))}
                         for metric in ("released","joint_retention")}
            report[key]["writer_aware_arrival_ceiling"]=max(
                expected(bank,q,p,{None:a,0:b,1:b},"released") for a,b in product((0,1),repeat=2))
        ceiling=fixture.evaluate(reference,q,p)["content_ceiling"]
        assert report["authored_comparison"]["released"]["read_text"]==ceiling
        results.append({"q":float(q),"prior":float(p),"policies":report})
    sensitivity=[]
    for ids in product((False,True),repeat=2):
        choices=[(key,mark) for key,mark in marks.items() if mark["status"]=="uncertain"]
        assert len(choices)==2
        alternate=dict(marks)
        cleared=[]
        for flag,(key,mark) in zip(ids,choices,strict=True):
            if flag:
                cleared.append(key)
                repl=mark["alternate"]
                alternate[key]=mark|{"status":"clear" if repl=="clear" else "met",
                                     "relation":None if repl=="clear" else repl}
        scored={key:grade(data[receipt],alternate[receipt],True)
                for key,receipt in locked["receipt_keys"].items()}
        q,p=fixture.Q(".75"),fixture.Q(".5")
        score=expected(scored,q,p,informed,"released")
        baseline=max(expected(scored,q,p,{None:a,0:b,1:b},"released") for a,b in product((0,1),repeat=2))
        sensitivity.append({"cleared":cleared,"read_text":score,"best_arrival":baseline,"paired_delta":score-baseline})
    return {"grades":modes,"scenes":results,
            "balanced_guard_sensitivity":sensitivity,
            "judgment_counts":Counter(mark["status"] for mark in marks.values()),
            "artifact_pins":{file:fixture.pin(HERE/file) for file in ("verified.json","marks.json","judge.md")}}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
