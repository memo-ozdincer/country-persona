"""Check the matched answer-format intervention and the pooled binary margins."""
import argparse
from collections import Counter
import json
from pathlib import Path


def prompts(path):
    inputs={}
    for row in map(json.loads,path.read_text().splitlines()):
        key,_=row["id"].rsplit("/",1)
        body=json.loads(row["messages"][1]["content"])
        entry=(row["messages"][0]["content"],body["evidence"],body["candidate_clause"])
        assert key not in inputs or inputs[key]==entry
        inputs[key]=entry
    return inputs


def evaluate(binary,three_way,three_way_guard):
    root=binary.parent
    assert prompts(binary)==prompts(three_way)
    metrics=json.loads((root/"metrics.json").read_text())
    prior=json.loads(three_way_guard.read_text())
    counts=Counter()
    table={}
    for case,record in metrics["cases"].items():
        pooled=sum(record["margins"])/len(record["margins"])
        resolved="failed" if pooled>0 else "clear" if pooled<0 else None
        expected=record["reference_guard"]
        grade="uncertain" if resolved is None else "correct" if resolved==expected else "wrong"
        counts[grade]+=1
        table[case]={"expected":expected,"binary_stable":record["stable"],
                     "three_way_stable_guard":prior["cases"][case]["stable_guard"],
                     "binary_average_margin":pooled,"binary_pooled":resolved,"pooled_grade":grade}
    return {"equal_inputs":["system prompt","candidate clause","evidence"],
            "edited":"Answer choices and layouts.",
            "binary_stable":metrics["totals"],"binary_pooled":dict(counts),
            "three_way_stable":prior["counts"],"cases":table,
            "scope":"Equal-weight pooling uses both recorded logit margins at a fixed zero threshold. Small exposed archive comparison."}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("binary",type=Path)
    p.add_argument("three_way",type=Path)
    p.add_argument("three_way_guard",type=Path)
    args=p.parse_args()
    print(json.dumps(evaluate(args.binary,args.three_way,args.three_way_guard),indent=2))
