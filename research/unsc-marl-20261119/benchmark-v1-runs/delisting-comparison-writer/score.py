"""Assemble source-bound records and replay identical policies under each writer."""
import json
import runpy
import sys
from unittest.mock import patch

import numpy as np

from collect_relation import CASE, HERE, WHOLE, plan, read

sys.path.insert(0,str(CASE))
earlier=runpy.run_path(str(CASE/"fit_delisting.py"))
sys.path.remove(str(CASE))
team=earlier["team"]
evaluate=earlier["learner"].fit.compare


def proposal(reply, fixed_length):
    candidate=reply["text"].strip()
    if reply["termination"]!="complete":
        return "",reply["termination"]
    if candidate=="NONE":
        return "","none"
    words=len(candidate.split())
    if not 0<words<=40 or words+fixed_length>160:
        return "","length"
    return candidate,None


def run():
    spec=plan()
    assert spec==read(HERE/"plan.json")
    response=read(HERE/"verified.json")["outputs"]
    marks=read(HERE/"marks.json")
    assert response.keys()==marks.keys()==spec["requests"].keys()
    original=read(CASE/"results.json")
    case=read(CASE/"case.json")
    base=earlier["bank"](case,read(CASE/"verified.json")["outputs"])[1]
    variants={mode:[item.copy() for item in base] for mode in ("standalone","ungated","admitted")}
    compiled={}
    for v, (early, early_row) in enumerate(case["early"].items()):
        for r, (late, late_row) in enumerate(case["late"].items()):
            key=f"{early}/{late}"
            source=json.loads(spec["requests"][key]["messages"][1]["content"])
            prefix=" ".join([*(s["text"] for s in case["public"]),*source.values()])
            text, fallback=proposal(response[key],len(prefix.split()))
            mark=marks[key]
            assert mark["quote"]==text and mark["reason"]
            status=mark["status"]
            assert status in {"omitted","relation","supported","unsupported","uncertain"}
            assert bool(text)==(status!="omitted")
            assert set(mark["sources"])<=source.keys()
            if status in {"relation","unsupported","uncertain"}:
                assert set(mark["sources"])==source.keys()
            key_relation=original["records"][key]["expected"]
            if status=="relation":
                assert key_relation
            admitted=original["records"][key]["native"] is not None
            standalone=30+early_row["weight"]+late_row["weight"]
            release=0 if status in {"unsupported","uncertain"} else standalone + (18 if status=="relation" else 0)
            scores={"standalone":standalone,"ungated":release,"admitted":release if admitted else standalone}
            compiled[key]={"prefix":prefix,"candidate":text,"fallback":fallback,"admitted":admitted,
                           "ungated_record":" ".join([prefix,*([text] if text else [])]),
                           "admitted_record":" ".join([prefix,*([text] if text and admitted else [])]),
                           "scores":scores}
            for mode, value in scores.items():
                variants[mode][3][1,v,r]=value
    policies=[tuple(np.array(original[history][-1][name]) for name in ("sender","receiver"))
              for history in ("history","sampled_history")]
    compare={}
    with patch.object(team,"PRIVATE",{"2664":("full","diversion","request-only"),"2744":tuple(case["early"])}):
        for mode,bank in variants.items():
            result=evaluate(bank,*policies)
            compare[mode]={"summary":result["mean_utility"]["2744"],"rows":[
                row for row in result["held"] if row["family"]=="2744"]}
    return {"compiled":compiled,"policy":compare,"typed":original["native"]["mean_utility"]["2744"],
            "whole":read(WHOLE/"results.json")["native_writer"]["released"]["summary"]}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
