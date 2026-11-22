"""Reconstruct the prompt graph and audit arm-masked final annotations."""
import argparse
from hashlib import sha256
import json
from run import ARMS, HERE, episode, pins, runner, trace

E = HERE/"evidence"


def data():
    path=E/"transcript.jsonl"
    return {r["id"]:r for r in map(json.loads,path.read_text().splitlines())}


def masked(key):
    return sha256(("handover-brief-v1/"+key).encode()).hexdigest()[:9]


def deck(rows):
    return dict(sorted((masked(k),dict(docket=k.split("/")[0],text=r["output"]))
                       for k,r in rows.items() if "/final/" in k))


def audit(rows):
    launch=json.loads((E/"launch.json").read_text())
    complete=json.loads((E/"complete.json").read_text())
    assert pins()==launch["sha256"]
    for filename,field in [("transcript.jsonl","transcript_sha256"),("final-records.json","final_records_sha256")]:
        assert runner.digest(E/filename)==complete[field]
    seen=set()
    def read(requests):
        batch={}
        for req in requests:
            k=req["id"]
            assert k not in seen and all(rows[k][p]==v for p,v in req.items())
            assert 0<len(rows[k]["output_ids"])<=req["cap"]
            seen.add(k)
            batch[k]=rows[k]
        return batch
    restored=episode(read)
    assert set(rows)==seen and len(seen)==complete["records"]==28
    saved=json.loads((E/"final-records.json").read_text())
    assert saved=={x["family"]:{k:v["output"] for k,v in x["final"].items()} for x in restored}
    marks=json.loads((HERE/"marks.json").read_text())
    assert set(marks)==set(deck(rows))
    scores={}
    for family in ("guinea","libya"):
        for j in (0,1):
            for arm in ARMS:
                ids=trace(family,arm,j)
                k=ids[-1]
                r=rows[k]
                m=marks[masked(k)]
                assert len(m["spans"])==7
                assert all(span is None or (span and span in r["output"]) for span in m["spans"])
                scores[k]=dict(points=10*sum(s is not None for s in m["spans"]),guard=m["guard"],
                               input_tokens=sum(len(rows[i]["input_ids"]) for i in ids),
                               output_tokens=sum(len(rows[i]["output_ids"]) for i in ids),
                               words=len(r["output"].split()),capped=[i for i in ids if not rows[i]["ended"]])
    return {"calls_verified":len(seen),"scores":scores}


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("mode",choices=["deck","score"])
    rows=data()
    print(json.dumps(deck(rows) if cli.parse_args().mode=="deck" else audit(rows),indent=2,ensure_ascii=False))
