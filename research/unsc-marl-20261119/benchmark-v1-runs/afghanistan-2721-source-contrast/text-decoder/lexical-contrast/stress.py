"""Run the frozen editor on paraphrases that break the declared overlap shortcut."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0,str(PARENT))
import decode_2721 as base
import score_decode as scorer

MATERIAL = (
    "The speaker would endorse naming the new official only if those currently governing Kabul agreed. "
    "It expected the appointer to hear those rulers, taking account of every member of the voting body.",
    "The group said a newly named official could assist those already running the field mission. "
    "Those assigned duties would remain with them.",
)
HEADS = ("Mandate discussion. ","Appointment discussion. ")
MODES = ("zero_overlap","wrong_overlap")


def requests():
    rows = []
    for mode in MODES:
        for truth,text in enumerate(MATERIAL):
            for mapping in base.MAPPINGS:
                source = next(r for r in base.requests() if r["id"]==f"indirect/{truth}/{mapping}")
                data = json.loads(source["messages"][1]["content"])
                data["observation"]["explanation"] = (HEADS[truth] if mode=="wrong_overlap" else "")+text
                source["messages"][1]["content"] = json.dumps(data,ensure_ascii=False)
                source["id"] = f"{mode}/{truth}/{mapping}"
                lexical, shares = scorer.lexical(source)
                if mode=="zero_overlap":
                    assert shares == [0.,0.], (truth,shares)
                else:
                    assert base.MAPPINGS[mapping][lexical] == 1-truth and max(shares)>0, (truth,shares)
                rows.append(source)
    return rows


def plan():
    parents = base.plan()
    result = {"requests":requests(), "checkpoint_index_sha256":parents["checkpoint_index_sha256"],
              "sha256":parents["sha256"]}
    for path in (Path(__file__),HERE/"protocol.md",PARENT/"plan.json",PARENT/"verified.json",PARENT/"scores.json",
                 PARENT/"score_decode.py"):
        result["sha256"][str(path.relative_to(base.RUNS.parent))] = base.fixture.pin(path)
    return result


def locked():
    result = plan()
    assert result == json.loads((HERE/"plan.json").read_text())
    return result


def act(mode):
    lock = locked()
    runtime = base.runtime
    with patch.object(runtime,"plan",return_value=lock),patch.object(runtime,"HERE",HERE),patch.object(
        runtime,"OUT",HERE/"evidence"
    ),patch.object(runtime,"CASE",base.fixture.CASE):
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
