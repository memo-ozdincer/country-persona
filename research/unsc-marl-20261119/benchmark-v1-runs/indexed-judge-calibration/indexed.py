"""Expand only model-selected citation addresses into exact benchmark spans."""
import argparse
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"live-judge-calibration"
sys.path.insert(0,str(BASE))
import live

e=live.e
OUT=HERE/"evidence"
INDEX_INSTRUCTIONS=(
    "\nCitation format for this run: in each response or quote cell use a printed ID, e.g. A_0, "
    "or a contiguous range in one source or turn, e.g. A_0..A_2. The printed ID stands in for "
    "the exact quotation and the adapter restores it. Keep source objects' block values equal "
    "to the original block id, not the printed sentence id. Keep turn numbers exactly. "
    "Use the empty string for an omitted response. Return a single JSON object. "
    "Do not retype text into the response or quote cells."
)


def annotate(text,base,locations):
    boundaries=[0]+[m.end() for m in re.finditer(r'(?<=[.!?])\s+|\n+',text)]+[len(text)]
    pieces=[]
    for start,stop in zip(boundaries,boundaries[1:]):
        raw=text[start:stop]
        left=start+len(raw)-len(raw.lstrip())
        right=start+len(raw.rstrip())
        if left>=right:
            continue
        key=f"{base}_{len(pieces)}"
        locations[key]=(base,text,left,right)
        pieces.append(f"[{key}] {text[left:right]}")
    return "\n".join(pieces)


def indexed(original,mode):
    packet=json.loads(original["messages"][-1]["content"])
    loc={}
    names={}
    field="evidence" if mode=="final" else "source_blocks"
    for i,row in enumerate(packet[field]):
        prefix=f"S{i}"
        names[row["id"]]=prefix
        row["text"]=annotate(row["text"],prefix,loc)
    if mode=="final":
        packet["answer"]=annotate(packet["answer"],"A",loc)
    else:
        for i,row in enumerate(packet["turns"]):
            row["text"]=annotate(row["text"],f"T{i}",loc)
    system=original["messages"][0]["content"]+INDEX_INSTRUCTIONS
    return live.suite.judge_request(system,packet),loc,names


ORIGINAL=live.requests


def requests():
    return {mode:[row | {"request":indexed(row["request"],mode)[0]} for row in rows]
            for mode,rows in ORIGINAL().items()}


def plan():
    assert live.suite.verify_release()=="1.7"
    files=(Path(__file__),HERE/"protocol.md",BASE/"live.py",BASE/"verified.json")
    return {"release":live.suite.pin(live.prior.RELEASE/"release.json"),"batch":live.BATCH,
            "model_index":live.suite.pin(live.prior.MODEL/"model.safetensors.index.json"),
            "pins":{str(p.relative_to(HERE.parent)):live.suite.pin(p) for p in files},
            "request_hashes":{mode:[e.checksum(row["request"]) for row in rows] for mode,rows in requests().items()}}


def unwrap(text):
    fenced=re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```",text)
    return fenced.group(1) if fenced else text


def expand(mode,verdict,locations,names):
    def recover(ref,owner,allow_empty=False):
        if allow_empty and ref=="":
            return ""
        e.require(isinstance(ref,str),"Citation address must be a string")
        pair=ref.split("..")
        e.require(len(pair) in (1,2) and all(k in locations for k in pair),"Unknown passage address")
        a,b=locations[pair[0]],locations[pair[-1]]
        e.require(a[0]==b[0]==owner and a[2]<=b[2],"Citation range or owner mismatch")
        return a[1][a[2]:b[3]]

    def citations(entries):
        for item in entries:
            owner=names[item["block"]]
            item["quote"]=recover(item["quote"],owner)

    def touches(entries):
        for item in entries:
            item["quote"]=recover(item["quote"],f'T{item["turn"]}')

    if mode=="final":
        for entry in [*verdict["units"],verdict["guard"]]:
            entry["response"]=recover(entry["response"],"A",allow_empty=True)
            citations(entry["source"])
    else:
        for entry in verdict["ratings"]:
            touches(entry["spans"])
            citations(entry["source"])
        for entry in verdict["ideas"]:
            touches(entry["mentions"])
            citations(entry["source"])
    return verdict


def replay(directory,rows):
    inputs={mode:{r["id"]:r["request"] for r in entries} for mode,entries in ORIGINAL().items()}
    rebound=[]
    failures=[]
    for row in rows:
        mode,ident=row["mode"],row["id"]
        original=inputs[mode][ident]
        request,loc,names=indexed(original,mode)
        assert request==row["request"]
        capture=row["reply"]
        reply=capture
        try:
            raw=live.suite.decode_verdict(capture | {"text":unwrap(capture["text"])})
            expanded=expand(mode,raw,loc,names)
            reply=capture | {"text":json.dumps(expanded,ensure_ascii=False)}
        except (ValueError,KeyError,TypeError,AttributeError,IndexError) as problem:
            failures.append({"mode":mode,"id":ident,"reason":str(problem)})
            reply=capture | {"text":""}
        rebound.append(row | {"request":original,"reply":reply})
    return live.replay(directory,rebound) | {"binding_failures":failures}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","verify","replay"))
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    spec=plan()
    if args.mode!="plan":
        assert spec==e.read(HERE/"plan.json")
    if args.mode=="plan":
        e.emit(spec)
    elif args.mode=="replay":
        e.emit(replay(args.output,live.prior.report.load(OUT/"tokens.jsonl")))
    else:
        with patch.object(live,"HERE",HERE),patch.object(live,"OUT",OUT),patch.object(live,"requests",side_effect=requests):
            if args.mode=="run":
                live.run()
            else:
                e.emit(live.verify(live.prior.report.load(OUT/"tokens.jsonl")))
