"""Extract the role constraint first, then compile its opportunities."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import study
from episode import serialize, source_paths

raw_suite, raw_score = study.suite, study.score
SCHEMAS = {
    "sanctions":{
        "convener":study.CONVENERS,
        "public_report":{"aggregate":"aggregate public reporting","case summaries":"public case summaries"},
        "interval":{"six months":"every six months","annual":"every year"},
    },
    "membership":{
        "track":study.TRACKS,
        "sequence":study.SEQUENCES,
        "product":{"chair consultations":"chair consultations","written options note":"written options note",
                   "informal dialogue":"informal dialogue"},
    },
}
TASK = ('Translate the private workshop instruction into its explicit requirements. Return exactly one JSON '
        'object {"requires":{}} with each restricted field mapped to one exact value ID from dimension_values. '
        'Omit a field when the instruction allows any value for it. Copy only restrictions from private_instruction. '
        'Do not list packages, give historical views, or add other keys.')


def suite():
    prompts, truth = raw_suite()
    planned = {}
    for key,row in prompts.items():
        family = key.split("/")[0]
        user = json.loads(row["messages"][1]["content"])
        del user["packages"]
        user["dimension_values"] = SCHEMAS[family]
        user["task"] = TASK
        planned[key] = {**row,"messages":[row["messages"][0],{"role":"user","content":serialize(user)}]}
    return planned,truth


def translate(raw,family):
    def unique(pairs):
        d=dict(pairs)
        if len(d)!=len(pairs):
            raise ValueError("duplicate key")
        return d
    try:
        result=json.loads(raw,object_pairs_hook=unique)
        if not isinstance(result,dict) or set(result)!={"requires"}:
            return None
        values=result["requires"]
        if not isinstance(values,dict) or any(
            k not in SCHEMAS[family] or not isinstance(v,str) or v not in SCHEMAS[family][k]
            for k,v in values.items()
        ):
            return None
    except (ValueError,TypeError):
        return None
    return values


def score(rows):
    paths=source_paths()
    projected, compile_input = {}, {}
    for name,row in rows.items():
        family=name.split("/")[0]
        decoder=translate(row["output"],family)
        options=json.loads(paths[family].read_text())["options"]
        accepts=[o["id"] for o in options if decoder is not None and
                 all(o[field]==value for field,value in decoder.items())]
        compact=serialize({"accepts":accepts}) if decoder is not None else "{}"
        projected[name]={"constraint":decoder,"accepted":accepts}
        compile_input[name]={"output":compact}
    return {"projections":projected,**raw_score(compile_input)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    study.suite=suite
    study.score=score
    study.main(args.model,args.output)
    (args.output/"projection-lock.json").write_text(serialize(
        {"project_rule.py":sha256(Path(__file__).read_bytes()).hexdigest()})+"\n")
