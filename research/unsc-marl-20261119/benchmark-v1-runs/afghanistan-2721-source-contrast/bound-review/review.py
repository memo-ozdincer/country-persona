"""Collect paired native judgments of source-bound authority comparisons."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
RUNS=PARENT.parent


def load(name,path):
    spec=spec_from_file_location(name,path)
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prior=load("afghanistan_bounded_text_runtime",PARENT/"text-decoder/decode_2721.py")
runtime=prior.runtime
fixture=prior.fixture
SYSTEM=(
    "Decide whether the candidate comparison is fully supported by the supplied evidence. "
    "Treat the received national statement and the adopted clause as separate sources. "
    "Check who made each claim, the difference between a condition for a delegation's "
    "support and the legal terms of appointment, and the difference between an "
    "expectation and an event that already happened. A true statement from somewhere "
    "else is unsupported here. Every part of the candidate must be established by the "
    "displayed receipts. Missing evidence, changed attribution, or speculation means "
    "unsupported. Controls may omit receipts. Return only the letter of the decision."
)
LABELS={"ab":{"A":"supported","B":"unsupported"},"ba":{"A":"unsupported","B":"supported"}}


def probes():
    return json.loads((HERE/"probes.json").read_text())


def requests():
    result=[]
    for row,(order,labels) in product(probes(),LABELS.items()):
        early,late=(None if x is None else fixture.OPTIONS[i][x] for i,x in enumerate(row["receipts"]))
        text=row.get("claim")
        if text is None:
            text=fixture.RELATIONS[row["registered"]]["text"]
        payload={
            "national_statement":None if early is None else fixture.BLOCKS[early]["text"],
            "adopted_clause":None if late is None else fixture.BLOCKS[late]["text"],
            "candidate_comparison":text,
            "responses":labels,
        }
        result.append({"id":row["id"]+"/"+order,"max_output_tokens":2,"messages":[
            {"role":"system","content":SYSTEM},
            {"role":"user","content":json.dumps(payload,ensure_ascii=False)},
        ]})
    return result


def plan():
    files=(Path(__file__),HERE/"protocol.md",HERE/"probes.json",PARENT/"case.json",PARENT/"results.json",
           PARENT/"native-comparison/scores.json",PARENT/"text-decoder/lexical-contrast/scores.json",
           Path(prior.__file__),Path(runtime.__file__),Path(runtime.base.__file__),runtime.prior.RELEASE/"release.json")
    return {"requests":requests(),"checkpoint_index_sha256":fixture.pin(runtime.base.MODEL/"model.safetensors.index.json"),
            "sha256":{str(p.relative_to(RUNS.parent)):fixture.pin(p) for p in files}}


def locked():
    data=plan()
    assert data==json.loads((HERE/"plan.json").read_text())
    return data


def act(mode):
    data=locked()
    with patch.object(runtime,"plan",return_value=data),patch.object(runtime,"HERE",HERE),patch.object(
        runtime,"OUT",HERE/"evidence"),patch.object(runtime,"CASE",fixture.CASE):
        if mode=="run":
            runtime.run()
        else:
            verified=runtime.verify()
            launch=json.loads((HERE/"evidence/launch.json").read_text())
            assert launch["checkpoint_index_sha256"]==data["checkpoint_index_sha256"]
            assert launch["gpu_name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
            print(json.dumps(verified,ensure_ascii=False,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","verify"))
    mode=parser.parse_args().mode
    if mode=="plan":
        print(json.dumps(plan(),ensure_ascii=False,indent=2))
    else:
        act(mode)
