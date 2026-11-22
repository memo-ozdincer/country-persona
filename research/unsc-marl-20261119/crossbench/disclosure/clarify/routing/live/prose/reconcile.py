"""Resolve disagreeing role menus with order-swapped, quote-checked comparisons."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import study
from episode import serialize

HERE = Path(__file__).resolve().parent
raw_suite, raw_score = study.suite, study.score
INPUTS = [HERE/"evidence/metrics.json",HERE/"projection-evidence/metrics.json"]
TASK = ('Which candidate complete menu follows the private instruction exactly? Apply only what the card requires. '
        'If a restriction is not stated, do not add it. Return only JSON {"pick":1,"quote":"..."}, '
        'with pick 1 or 2, or null if neither. quote must be a short exact excerpt of private_instruction '
        'that distinguishes the two candidates.')


def candidates():
    left,right=(json.loads(p.read_text()) for p in INPUTS)
    output={}
    for name,value in left["menus"].items():
        assert value["status"]=="well_formed" and right["menus"][name]["status"]=="well_formed"
        a,b=value["estimated"],right["menus"][name]["estimated"]
        output[name]=(tuple(o for i,o in enumerate("ABCDEFG") if a&(1<<i)),
                      tuple(o for i,o in enumerate("ABCDEFG") if b&(1<<i)))
    return output


def suite():
    plans, reference = raw_suite()
    pairs = candidates()
    requests = {}
    for name,(left,right) in pairs.items():
        if left==right:
            continue
        for index,options in enumerate(((left,right),(right,left))):
            original=plans[name]
            user=json.loads(original["messages"][1]["content"])
            user["candidate_complete_menus"] = {str(i+1):menu for i,menu in enumerate(options)}
            user["task"]=TASK
            identifier=f"{name}/order-{index}"
            requests[identifier]={"id":identifier,"messages":[original["messages"][0],
                                                            {"role":"user","content":serialize(user)}]}
    return requests,reference


def validate(raw, card):
    def unique(pairs):
        item=dict(pairs)
        if len(item)!=len(pairs):
            raise ValueError("duplicate key")
        return item
    try:
        payload=json.loads(raw,object_pairs_hook=unique)
        if not isinstance(payload,dict) or set(payload)!={"pick","quote"}:
            return None
        pick,quote=payload["pick"],payload["quote"]
        if type(pick) is not int or pick not in (1,2) or not isinstance(quote,str):
            return None
        if len(quote.split())<4 or quote not in card:
            return None
    except (ValueError,TypeError):
        return None
    return {"pick":pick,"quote":quote}


def score(rows):
    plans, _ = raw_suite()
    reconciliation, answers = {},{}
    for name,(left,right) in candidates().items():
        if left==right:
            selected=left
            outcome={"method":"agreement","menu":selected}
        else:
            card=json.loads(plans[name]["messages"][1]["content"])["private_instruction"]
            checks=[validate(rows[f"{name}/order-{i}"]["output"],card) for i in (0,1)]
            selected=None
            if all(checks) and checks[0]["pick"]!=checks[1]["pick"]:
                selected=(left,right)[checks[0]["pick"]-1]
            outcome={"method":"stable_adjudication" if selected is not None else "unresolved",
                     "menu":selected,"adjudications":checks}
        reconciliation[name]=outcome
        answers[name]={"output":serialize({"accepts":selected}) if selected is not None else "{}"}
    return {"reconciliation":reconciliation,**raw_score(answers)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    study.suite=suite
    study.score=score
    study.main(args.model,args.output)
    (args.output/"reconciliation-lock.json").write_text(serialize(
        {str(path.relative_to(HERE)):sha256(path.read_bytes()).hexdigest()
         for path in [Path(__file__).resolve(),*INPUTS]})+"\n")
