"""Carry exact documentary evidence through the original release scorer."""
import json
from itertools import product
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
RUNS=HERE.parent
PRIOR=RUNS/"tribunals-source-action-bank"
sys.path.insert(0,str(PRIOR))
import bank

e=bank.e
CASE="tribunals"
REQUIRES={
    "disposition":("vote",),"capacity":("vote","srb-release"),"action":("action",),"review":("action",),
    "per-cooperation":("per-cooperation",),"per-unity":("per-unity",),"rus-staffing":("rus-staffing",),
    "rus-medical":("rus-medical",),"srb-release":("srb-release",),"srb-cooperation":("srb-cooperation",),
    "contrast":("per-unity","rus-staffing"),
}


def render(case,order,a,b):
    sources={r["id"]:r["text"] for r in e.evidence(case)}
    limits=sources["limits"].split(". ",1)[0]+"."
    first,second=(a,b) if order==0 else (b,a)
    text="\n\n".join((sources["vote"],sources["action"],limits,sources[first],sources[second]))
    reply={"text":text,"termination":"complete"}
    packet=e.final_packet(case,[None,None,reply])
    visible={"vote","action",a,b}
    units=[]
    for row in case["rubric"]:
        name=row["id"]
        needed=REQUIRES[name]
        enough=set(needed)<=visible
        if enough:
            start=min(text.index(sources[key]) for key in needed)
            stop=max(text.index(sources[key])+len(sources[key]) for key in needed)
            span=text[start:stop]
        units.append({"id":name,"status":"met" if enough else "unmet","response":span if enough else "",
                      "source":[{"block":key,"quote":sources[key]} for key in needed] if enough else [],
                      "reason":"The protected record contains the full required source statements." if enough
                      else "The required source statement is outside the delivered packets."})
    mark={"id":packet["id"],"units":units,"guard":{"status":"clear","source":[],"response":"",
                                                   "reason":"All material assertions are verbatim sourced statements."}}
    scores=e.final_score(case,[None,None,reply],mark)
    assert scores["release"] and scores["released_70"]>0
    return {"packet":packet,"verdict":mark,"score":scores}


def run():
    case=e.cases()[CASE]
    rows={}
    for order,a,b in product((0,1),*[[v["id"] for v in deck] for deck in case["owned"]]):
        rows[f"{order}/{a}/{b}"]=render(case,order,a,b)
    return rows


if __name__=="__main__":
    e.emit(run())
