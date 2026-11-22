"""Check the workshop with exact interpretation and the locked initial evidence mask."""
import json
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent


def evaluate():
    engine=runpy.run_path(str(HERE/"run.py"))
    probes={}
    for item in engine["suite"]():
        role,kind,name,_=item["id"].split("/")
        answer=engine["REFERENCE"][role] if kind=="scope" else (
            "accept" if name in engine["MENUS"][role] else "reject")
        probes[item["id"]]={"label_logits":[float(value==answer) for value in item["values"]]}
    result=engine["score"](probes)
    return {"scope":"Authored exact source decoder under the same frozen initial availability and two-source exclusion.",
            "replay":result}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
