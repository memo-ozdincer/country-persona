"""Check manual quote bindings and calculate policies on the recorded native outputs."""
import json
import runpy
import sys
from unittest.mock import patch

import numpy as np

from collect_chair import BASE, HERE, plan, read

sys.path.insert(0, str(BASE))
previous = runpy.run_path(str(BASE/"fit_delisting.py"))
sys.path.remove(str(BASE))
team=previous["team"]
analyze=previous["learner"].fit.compare


def evaluate(outputs, marks, spec):
    scores={}
    max_points=read(HERE/"rubric.json")
    for key, output in outputs.items():
        early, late = key.split("/")
        info=json.loads(spec["requests"][key]["messages"][1]["content"])
        sources={f"public-{i+1}":t for i,t in enumerate(info["public_record"])}
        sources.update({k:v for k,v in info.items() if k in ("delegate_statement","adopted_document")})
        allowed={"vote","scope"}
        if early!="None":
            allowed.add("delegate")
        if late!="None":
            allowed.add("document")
        if (early,late) in {("malta","authority"),("a3plus","review")}:
            allowed.add("relation")
        source_keys={"vote":{"public-1"},"scope":{"public-2"},"delegate":{"delegate_statement"},
                     "document":{"adopted_document"},"relation":{"delegate_statement","adopted_document"}}
        grade=marks[key]
        assert set(grade["criteria"]) == allowed
        for name,item in grade["criteria"].items():
            assert item["status"] in {"met","unmet","uncertain"} and item["reason"]
            if item["status"] == "met":
                assert item["quote"] and item["quote"] in output["text"]
                assert set(item["evidence"]) == source_keys[name]
                assert set(item["evidence"]) <= set(sources)
        guard=grade["guard"]
        assert guard["status"] in {"clear","uncertain","failed"} and guard["reason"]
        if guard["status"]!="clear":
            assert guard["quote"] and guard["quote"] in output["text"]
            assert set(guard["evidence"]) <= set(sources)
        met=[name for name,item in grade["criteria"].items() if item["status"]=="met"]
        raw=sum(max_points[name]["weight"] for name in met)
        blockers=[]
        w=len(output["text"].split())
        if w>160 or not w:
            blockers.append("word_cap")
        if output["termination"]!="complete":
            blockers.append(output["termination"])
        if guard["status"]!="clear":
            blockers.append("guard_"+guard["status"])
        scores[key]={"raw":raw,"released":0 if blockers else raw,"blockers":blockers,
                     "words":w,"met":met}
    return scores


def run():
    spec=plan()
    assert spec==read(HERE/"plan.json")
    out=read(HERE/"verified.json")["outputs"]
    marks=read(HERE/"marks.json")
    assert out.keys()==marks.keys()==spec["requests"].keys()
    grades=evaluate(out,marks,spec)
    case=read(BASE/"case.json")
    prior=read(BASE/"results.json")
    bank=previous["bank"](case,read(BASE/"verified.json")["outputs"])[1]
    weights=[tuple(np.array(prior[history][-1][param]) for param in ("sender","receiver"))
             for history in ("history","sampled_history")]
    variants={}
    for field in ("released","raw"):
        table=[a.copy() for a in bank]
        table[0][1]=grades["None/None"][field]
        for v,early in enumerate(case["early"]):
            table[1][1,v]=grades[f"{early}/None"][field]
            for j,late in enumerate(case["late"]):
                table[2][1,j]=grades[f"None/{late}"][field]
                table[3][1,v,j]=grades[f"{early}/{late}"][field]
        with patch.object(team,"PRIVATE",{"2664":("full","diversion","request-only"),"2744":tuple(case["early"])}):
            report=analyze(table,*weights)
        variants[field]={"summary":report["mean_utility"]["2744"],"settings":[
            k for k in report["held"] if k["family"]=="2744"]}
    return {"scores":grades,"native_writer":variants,"typed_reference":prior["native"]["mean_utility"]["2744"]}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
