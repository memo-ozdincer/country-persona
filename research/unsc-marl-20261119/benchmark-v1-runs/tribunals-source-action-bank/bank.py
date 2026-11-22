"""Enumerate every tribunal one-block action pair and the two speaker orders."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent/"historical-source-messages"
sys.path.insert(0,str(PRIOR))
import exact_notes as prev

e=prev.e
r=prev.report
previous=prev.previous
suite=prev.run_suite
OUT=HERE/"evidence"
CASE="tribunals"


def payload(request):
    return {k:request[k] for k in ("messages","max_output_tokens")}


def design():
    case=e.cases()[CASE]
    requests={}
    for order,a,b in product((0,1),*case["owned"]):
        blocks=[a,b]
        notes=[{"speaker":case["roles"][i],"text":blocks[i]["text"]} for i in (order,1-order)]
        key=f'{order}/{a["id"]}/{b["id"]}'
        requests[key]=e.build_request(case,"independent",order,notes)
    return requests


def key(payload):
    return e.checksum(payload)


def archived():
    available={}
    for row in r.load(PRIOR/"evidence/episodes.jsonl"):
        if row["id"].split("/")[0]==CASE:
            available[key(payload(row["final_request"]))]=row["final"]
    assert len(available)==3
    return available


def plan():
    old=archived()
    requests=design()
    assert set(old)<= {key(payload(req)) for req in requests.values()}
    return {"requests":requests,"case":CASE,"archived_request_ids":sorted(old),
            "pins":{str(path.relative_to(HERE.parent)):suite.pin(path) for path in (
                Path(__file__),HERE/"protocol.md",PRIOR/"exact_notes.py",PRIOR/"evidence/episodes.jsonl",
                PRIOR/"verdicts.json",PRIOR/"coverage.json")},
            "release":previous.plan()["release_sha256"],"model":previous.plan()["index_sha256"]}


def collect(call,directory):
    old=archived()
    for ident, req in design().items():
        contents=payload(req)
        reused=key(contents) in old
        reply=old[key(contents)] if reused else call(contents)
        suite.append(directory/"actors.jsonl",{"id":ident,"request":contents,"reply":reply,"reused":reused})
        suite.append(directory/"episodes.jsonl",{"id":ident,"request_sha256":e.checksum(req),"reply":reply})


def packets():
    spec=design()
    case=e.cases()[CASE]
    rows=r.load(OUT/"episodes.jsonl")
    assert [row["id"] for row in rows]==list(spec)
    out={}
    for row in rows:
        req = spec[row["id"]]
        assert row["request_sha256"]==e.checksum(req)
        packet=e.judge.request(e.final_packet(case,[None,None,row["reply"]]))
        out[row["id"]]=packet
    return dict(sorted((packet["id"],packet) for packet in out.values())), out, rows


def verify():
    from transformers import AutoTokenizer
    files=e.read(OUT/"complete.json")
    assert all(suite.pin(OUT/name)==digest for name,digest in files.items())
    current=r.load(OUT/"actors.jsonl")
    old=archived()
    fresh=[row for row in current if not row["reused"]]
    for row in current:
        if row["reused"]:
            assert old[key(row["request"])]==row["reply"]
    tokenizer=AutoTokenizer.from_pretrained(previous.MODEL,local_files_only=True)
    eos=tokenizer.convert_tokens_to_ids("<|im_end|>")
    for a,t in zip(fresh,r.load(OUT/"tokens.jsonl"),strict=True):
        assert a["request"]==t["request"]
        assert t["input_ids"]==previous.get_tokens(tokenizer,t["request"])
        ids=t["output_ids"]
        reply=a["reply"]
        assert tokenizer.decode(ids,skip_special_tokens=True).strip()==reply["text"]
        assert reply["input_tokens"]==len(t["input_ids"]) and reply["output_tokens"]==len(ids)
        assert bool(ids and ids[-1]==eos)==(reply["termination"]=="complete")
    unique,_,rows=packets()
    return {"rows":len(rows),"physical_calls":len(fresh),"unique_finals":len(unique),
            "tokens":{kind:sum(row["reply"][kind+"_tokens"] for row in fresh) for kind in ("input","output")},
            "termination":dict(Counter(row["reply"]["termination"] for row in fresh)),"files":files}


def score():
    unique,linked,rows=packets()
    verdicts=e.read(HERE/"verdicts.json")
    assert unique.keys()==verdicts.keys()
    case=e.cases()[CASE]
    coverage={tuple(a["source_ids"]):a["potential_points"] for a in
              e.read(PRIOR/"coverage.json")[CASE]["cases"]}
    by_order={}
    for row in rows:
        ident=row["id"]
        order,one,two=ident.split("/")
        result=e.final_score(case,[None,None,row["reply"]],verdicts[linked[ident]["id"]])
        by_order.setdefault(order,{})[f"{one}/{two}"]=result | {"mapped_evidence_coverage":coverage[one,two]}
    return {"by_order":by_order,"best_by_order":{
        order:max(x["released_70"] for x in options.values()) for order,options in by_order.items()}}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","verify","packets","score"))
    mode=p.parse_args().mode
    spec=plan()
    if mode!="plan":
        assert spec==e.read(HERE/"plan.json")
    with patch.object(previous,"HERE",HERE),patch.object(previous,"OUT",OUT),patch.object(
            suite,"collect",side_effect=collect):
        data={"plan":lambda:spec,"run":previous.run,"verify":verify,
              "packets":lambda:packets()[0],"score":score}[mode]()
    if mode!="run":
        e.emit(data)
