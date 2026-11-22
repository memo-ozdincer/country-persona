"""Grade an array of handovers with id, actions and deliverable objects."""
import argparse
from collections import Counter
import json
from pathlib import Path

from handover import render


def grade(predictions):
    gold=render()["keys"]
    predictions_by_id={row["id"]:row for row in predictions}
    if len(predictions_by_id)!=len(predictions) or set(predictions_by_id)!=set(range(len(gold))):
        raise ValueError("Provide exactly one prediction per input id")
    counts=Counter()
    by_action=Counter()
    misses=[]
    for answer in gold:
        pred=predictions_by_id[answer["id"]]
        fields=set(answer["actions"])
        if any(set(pred[k])!=fields for k in ("actions","deliverable")):
            raise ValueError(f"Missing or extra fields for input {answer['id']}")
        complete=True
        for field,expected in answer["actions"].items():
            choice=pred["actions"][field]
            good=(choice, pred["deliverable"][field])==(expected, answer["deliverable"][field])
            counts["fields"]+=1
            counts["correct_fields"]+=good
            counts["unsupported_confirmations"]+=choice=="confirm" and expected=="verify"
            counts["unsupported_corrections"]+=choice=="correct" and expected=="verify"
            counts["unnecessary_referrals"]+=choice=="verify" and expected!="verify"
            by_action[(expected,"total")]+=1
            by_action[(expected,"correct")]+=good
            if not good: misses.append({"id":answer["id"],"field":field})
            complete &= good
        counts["handovers"]+=1
        counts["complete_handovers"]+=complete
    return {"counts":dict(counts),"by_required_action":{
        op:{k:by_action[op,k] for k in ("total","correct")} for op in ("confirm","correct","verify")},
        "misses":misses}


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("predictions",type=Path)
    print(json.dumps(grade(json.loads(cli.parse_args().predictions.read_text())),indent=2))
