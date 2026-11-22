"""Verify all texts and compute order-stable downstream answers and unsupported recoveries."""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import statistics
from pilot import dataset,HERE,ARCHIVE


def score(full_record=False):
    from assembled import assembled
    evidence=HERE/("assembled-evidence" if full_record else "evidence")
    launch=json.loads((evidence/"launch.json").read_text())
    for path in (HERE/"pilot.py",HERE/"items.json",ARCHIVE):
        assert sha256(path.read_bytes()).hexdigest()==launch["sha256"][path.name]
    supports=json.loads((HERE/"memo-support.json").read_text())
    if full_record:
        assert (evidence/"wrapper.sha256").read_text().strip()==sha256((HERE/"assembled.py").read_bytes()).hexdigest()
        for spans in supports.values():
            spans[2]="submitted by France"
            spans[6]="abstentions by China and Russia"
    groups=defaultdict(list)
    masses=[]
    for expected,line in zip(assembled() if full_record else dataset(),(evidence/"reads.jsonl").read_text().splitlines(),strict=True):
        row=json.loads(line)
        assert all(row[k]==v for k,v in expected.items())
        outcome=row["order"][max(range(3),key=row["logits"].__getitem__)]
        groups[row["arm"],row["item"]].append(outcome)
        masses.append(row["legal_mass"])
        if row["arm"] in supports:
            span=supports[row["arm"]][row["item"]]
            if span: assert span in row["prompt"].split("\n\nQuestion:")[0]
    counts=defaultdict(Counter)
    items=[]
    for (arm,i),answers in groups.items():
        assert len(answers)==3
        answer=answers[0] if len(set(answers))==1 else "unstable"
        group="target" if i%4<2 else "other"
        if arm in supports:
            supported=bool(supports[arm][i])
            expected="source" if supported else "unspecified"
        else:
            expected={"empty":"unspecified","faithful":"source","reversed":"alternative"}[arm]
        c=counts[arm,group]
        c["items"]+=1
        c["faithful_to_note"]+=answer==expected
        c["stable_source_answer"]+=answer=="source"
        c["supported_recovery"]+=answer==expected=="source"
        c["unsupported_recovery"]+=answer=="source" and expected!="source"
        c["unstable"]+=answer=="unstable"
        items.append(dict(arm=arm,item=i,expected=expected,reads=answers))
    return {"calls":len(masses),"median_legal_mass":statistics.median(masses),"items":items,
            "counts":{a+"/"+g:dict(c) for (a,g),c in counts.items()}}


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembled",action="store_true")
    print(json.dumps(score(parser.parse_args().assembled),indent=2))
