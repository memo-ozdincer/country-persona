"""Run and score the positive-only comparison-writer intervention."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
MIX=HERE.parent/"comparison-adapter-transfer"
sys.path.insert(0,str(MIX))
import train_writer as base
import audit_fit
import score_transfer

read=base.read
EPOCHS=4


def plan():
    original=base.plan()
    assert original==read(MIX/"plan.json")
    positives=[row for row in original["training"] if row["target"]!="NONE"]
    assert len(positives)*EPOCHS==24
    assert len(positives)==6
    paths=(Path(__file__),HERE/"protocol.md",MIX/"plan.json",MIX/"train_writer.py",
           MIX/"audit_fit.py",MIX/"score_transfer.py",MIX/"results.json")
    return original | {"training":positives,"epochs":EPOCHS, "pins":original["pins"] | {
        str(x.relative_to(HERE.parents[1])):base.pin(x) for x in paths}}


def act(mode):
    spec=plan()
    if mode=="plan":
        return spec
    assert spec==read(HERE/"plan.json")
    if mode=="score":
        with patch.object(score_transfer,"HERE",HERE),patch.object(score_transfer,"plan",return_value=spec):
            return score_transfer.run()
    if mode=="audit":
        with patch.object(audit_fit,"HERE",HERE),patch.object(audit_fit,"EPOCHS",EPOCHS):
            return audit_fit.run()
    with patch.object(base,"HERE",HERE),patch.object(base,"OUT",HERE/"evidence"),patch.object(
            base,"plan",return_value=spec),patch.object(base,"EPOCHS",EPOCHS):
        return {"run":base.run,"verify":base.verify}[mode]()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","verify","audit","score"))
    mode=p.parse_args().mode
    result=act(mode)
    if mode!="run":
        print(json.dumps(result,ensure_ascii=False,indent=2))
