"""Collect native comparison sentences from only the two delivered 2744 facts."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
CASE = RUNS / "delisting-2744"
WHOLE = RUNS / "delisting-native-chair"
sys.path.insert(0, str(WHOLE))
import collect_chair as chair

BUDGET = 128
read = chair.read
pin = chair.pin
SYSTEM = (
    "Write only a specific comparison for a Council decision brief, at most 40 words. "
    "The source facts will appear separately in the brief. Explain exactly how the delegate's "
    "statement and the adopted provision relate. State who gives advice or information and who "
    "decides if the relationship concerns procedure. For a timing relationship, state the "
    "delegate's preference and the actual timing and force of the adopted text. Keep the "
    "speaker's own stance separate from what the Council adopted. Do not infer endorsement, "
    "agreement or legal authority from a shared topic. Return exactly NONE when there is no "
    "specific supported link. Use only the two fields below. Return only the comparison."
)


def plan():
    case=read(CASE/"case.json")
    earlier=read(WHOLE/"plan.json")
    requests={}
    for early, late in product(case["early"],case["late"]):
        key=f"{early}/{late}"
        delivered=json.loads(earlier["requests"][key]["messages"][1]["content"])
        packet={field:delivered[field] for field in ("delegate_statement","adopted_document")}
        assert "hoped for full implementation" in packet["delegate_statement"] or early!="a3plus"
        requests[key]={"id":key,"max_output_tokens":BUDGET,"messages":[
            {"role":"system","content":SYSTEM},
            {"role":"user","content":json.dumps(packet,ensure_ascii=False)},
        ]}
    files=(Path(__file__),HERE/"protocol.md",HERE/"score.py",CASE/"case.json",CASE/"results.json",
           CASE/"verified.json",WHOLE/"plan.json",WHOLE/"results.json",Path(chair.__file__),
           chair.RELEASE/"release.json")
    return {"requests":requests,"checkpoint_index_sha256":pin(chair.MODEL/"model.safetensors.index.json"),
            "pins":{str(f.relative_to(RUNS.parent)):pin(f) for f in files}}


def act(mode):
    spec=plan()
    if mode=="plan":
        return spec
    assert spec==read(HERE/"plan.json")
    with patch.object(chair,"HERE",HERE),patch.object(chair,"OUT",HERE/"evidence"),patch.object(
            chair,"BUDGET",BUDGET),patch.object(chair,"locked",return_value=spec):
        return {"run":chair.run,"verify":chair.verify}[mode]()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","verify"))
    mode=p.parse_args().mode
    result=act(mode)
    if mode!="run":
        print(json.dumps(result,ensure_ascii=False,indent=2))
