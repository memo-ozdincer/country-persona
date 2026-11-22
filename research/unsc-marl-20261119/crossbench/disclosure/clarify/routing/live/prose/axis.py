"""Check disputed prose menus one mandate field at a time."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import study
from episode import serialize,source_paths
from project_rule import SCHEMAS
from reconcile import INPUTS,candidates

HERE = Path(__file__).resolve().parent
raw_suite, raw_score = study.suite, study.score
TASK = ('Use only private_instruction. For this one field, give the exact value ID the instruction requires. '
        'If it allows any value, return null. Return JSON {"value":null,"quote":"..."}. '
        'The quote must be an exact substring of private_instruction and must support your answer. '
        'A word or sentence from the field description is not a quote from the instruction.')


def suite():
    originals, truth = raw_suite()
    plans = {}
    for name,(a,b) in candidates().items():
        if a==b:
            continue
        family = name.split("/")[0]
        card = json.loads(originals[name]["messages"][1]["content"])["private_instruction"]
        for field,values in SCHEMAS[family].items():
            row = {"private_instruction":card,"field_under_review":field,
                   "possible_values":values,"task":TASK}
            id_=f"{name}/{field}"
            plans[id_]={"id":id_,"messages":[
                {"role":"system","content":"Check one requirement of a fictional private instruction."},
                {"role":"user","content":serialize(row)}]}
    return plans,truth


def parse(raw,card,values):
    try:
        reply=json.loads(raw)
        if not isinstance(reply,dict) or set(reply)!={"value","quote"}:
            return None
        value,quote=reply["value"],reply["quote"]
        if value is not None and (not isinstance(value,str) or value not in values):
            return None
        if not isinstance(quote,str) or len(quote.split())<3 or quote not in card:
            return None
    except (ValueError,TypeError):
        return None
    return reply


def score(rows):
    originals,_ = raw_suite()
    paths = source_paths()
    assessments,answers = {},{}
    for name,(a,b) in candidates().items():
        if a==b:
            selected=a
            assessment={"method":"agreement","menu":selected}
        else:
            family=name.split("/")[0]
            card=json.loads(originals[name]["messages"][1]["content"])["private_instruction"]
            fields={field:parse(rows[f"{name}/{field}"]["output"],card,values)
                    for field,values in SCHEMAS[family].items()}
            selected=None
            if all(fields.values()):
                restrictions={field:v["value"] for field,v in fields.items() if v["value"] is not None}
                options=json.loads(paths[family].read_text())["options"]
                selected=[o["id"] for o in options if all(o[k]==v for k,v in restrictions.items())]
            assessment={"method":"field_check" if selected is not None else "unresolved",
                        "fields":fields,"menu":selected}
        assessments[name]=assessment
        answers[name]={"output":serialize({"accepts":selected}) if selected is not None else "{}"}
    return {"checks":assessments,**raw_score(answers)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    study.suite=suite
    study.score=score
    study.main(args.model,args.output)
    paths=[Path(__file__).resolve(),HERE/"reconcile.py",HERE/"project_rule.py",*INPUTS]
    (args.output/"field-lock.json").write_text(serialize(
        {str(path.relative_to(HERE)):sha256(path.read_bytes()).hexdigest() for path in paths})+"\n")
