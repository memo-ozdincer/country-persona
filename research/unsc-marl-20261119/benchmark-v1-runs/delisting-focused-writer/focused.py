"""Evaluate native comparison text guided by a cached source verifier's topic."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "delisting-comparison-writer"
sys.path.insert(0, str(PREVIOUS))
import collect_relation as old
import score as scoring

read = old.read
BUDGET=old.BUDGET
QUESTIONS = {
    "authority": ("Compare the procedural roles. Which body provides what information, and which body "
                  "decides? Explicitly link the speaker's description with the adopted division of "
                  "roles. If either role is missing from the adopted passage, return NONE."),
    "review": ("Compare the review timing and legal force. Make clear what the delegate would prefer "
               "and exactly what the adopted text expresses. Retain the adopted text's operative verb "
               "or its precise equivalent. If the adopted passage gives no review terms, return NONE."),
}


def plan():
    inherited=old.plan()
    baseline=read(old.CASE/"results.json")
    requests={}
    for key,row in inherited["requests"].items():
        view,_=key.split("/")
        passing=[kind for kind,margin in baseline["marks"][f"early/{view}"].items() if margin>0]
        changed=deepcopy(row)
        if len(passing)==1:
            payload=json.loads(row["messages"][1]["content"])
            payload["comparison_question"]=QUESTIONS[passing[0]]
            changed["messages"][1]["content"]=json.dumps(payload,ensure_ascii=False)
        requests[key]=changed
    paths=(Path(__file__),HERE/"protocol.md",PREVIOUS/"plan.json",PREVIOUS/"collect_relation.py")
    return inherited | {"requests":requests,"pins":inherited["pins"] | {
        str(x.relative_to(HERE.parents[1])):old.pin(x) for x in paths}}


def act(mode):
    spec=plan()
    if mode=="plan":
        return spec
    assert spec==read(HERE/"plan.json")
    if mode=="score":
        def read_for_score(path):
            if path == HERE/"plan.json":
                return projection
            return read(path)

        projection=deepcopy(spec)
        for row in projection["requests"].values():
            payload=json.loads(row["messages"][1]["content"])
            payload.pop("comparison_question",None)
            row["messages"][1]["content"]=json.dumps(payload,ensure_ascii=False)
        with patch.object(scoring,"HERE",HERE),patch.object(scoring,"plan",return_value=projection),patch.object(
                scoring,"read",side_effect=read_for_score):
            result=scoring.run()
        for record in result["compiled"].values():
            # Comparison questions are guidance and must never render as evidence.
            assert "Compare the procedural roles." not in record["prefix"]
            assert "Compare the review timing" not in record["prefix"]
        return result
    with patch.object(old.chair,"HERE",HERE),patch.object(old.chair,"OUT",HERE/"evidence"),patch.object(
            old.chair,"BUDGET",BUDGET),patch.object(old.chair,"locked",return_value=spec):
        return {"run":old.chair.run,"verify":old.chair.verify}[mode]()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","verify","score"))
    mode=p.parse_args().mode
    result=act(mode)
    if mode!="run":
        print(json.dumps(result,ensure_ascii=False,indent=2))
