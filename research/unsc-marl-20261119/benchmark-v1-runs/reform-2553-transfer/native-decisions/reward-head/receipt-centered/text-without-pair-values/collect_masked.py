"""Collect frozen text decisions with inter-clause bonuses omitted."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
import centered as prior

head,held=prior.head,prior.held
runtime=held.native
SYSTEM=(
    "Choose one available Peru passage for a source-faithful Council decision record. "
    "The numbers describe standalone documentary coverage if your passage is delivered. "
    "When another note is visible, consider which of your passages enables the most useful "
    "grounded comparison, while preserving the two speakers' actual positions. The passage "
    "you choose may never arrive. With no receipt text, use the available standalone evidence "
    "and do not invent the other desk's statement. Return only one answer letter."
)


def plan():
    inputs=held.plan()["requests"]
    rows=[]
    for request in inputs:
        if "/independent/" in request["id"]:
            continue
        data=json.loads(request["messages"][1]["content"])
        del data["joint_requirements"]
        rows.append({**request,"messages":[{"role":"system","content":SYSTEM},
                                           {"role":"user","content":json.dumps(data,ensure_ascii=False)}]})
    assert len(rows)==40
    files=(Path(__file__),HERE/"protocol.md",PARENT/"results.json",PARENT/"plan.json",
           head.HERE/"plan.json",Path(runtime.__file__),Path(held.__file__),Path(runtime.base.__file__),
           runtime.prior.RELEASE/"release.json")
    return {"requests":rows,"checkpoint_index_sha256":head.prior.digest(runtime.base.MODEL/"model.safetensors.index.json"),
            "sha256":{str(path.relative_to(head.RUNS.parent)):head.prior.digest(path) for path in files}}


def locked():
    lock=plan()
    assert lock==json.loads((HERE/"plan.json").read_text())
    return lock


def act(mode):
    lock=locked()
    with patch.object(runtime,"plan",return_value=lock),patch.object(runtime,"HERE",HERE),patch.object(
        runtime,"OUT",HERE/"evidence"),patch.object(runtime,"CASE",held.CASE):
        if mode=="run":
            runtime.run()
            return
        verified=runtime.verify()
    launch=json.loads((HERE/"evidence/launch.json").read_text())
    assert launch["checkpoint_index_sha256"]==lock["checkpoint_index_sha256"]
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
