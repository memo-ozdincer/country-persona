"""Use source-selection actions with the published historical final writer."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent/"historical-benchmark-slice"
sys.path.insert(0,str(PREVIOUS))
import slice_run as previous

OUT=HERE/"evidence"
e=previous.e
report=previous.report
run_suite=previous.run_suite
ARMS=("independent","peer")


def plan():
    spec=previous.plan()
    return {"cases":spec["cases"],"conditions":list(ARMS),"orders":[0,1],"selection_output_tokens":16,
            "model":spec["model"],"model_index_sha256":spec["index_sha256"],
            "release_sha256":spec["release_sha256"],
            "inputs":{str(path.relative_to(HERE.parent)):run_suite.pin(path) for path in
                      (Path(__file__),HERE/"protocol.md",PREVIOUS/"slice_run.py",PREVIOUS/"results.json")}}


def collect(call,directory):
    cached={}
    for case,order,arm in product(e.cases().values(),(0,1),ARMS):
        notes, selections = [], []
        for step in (0,1):
            ii=order if step==0 else 1-order
            chair_request=e.build_request(case,arm,order,notes)
            payload=json.loads(chair_request["messages"][-1]["content"])
            allowed={b["id"]:b["text"] for b in case["owned"][ii]}
            payload["selectable_ids"]=list(allowed)
            req={"max_output_tokens":16,"messages":[
                {"role":"system","content":(
                    "Choose which one of your allowed evidence blocks to send for the chair's exact task. "
                    "The chair already has the public blocks. If you can see an earlier note, choose material "
                    "that complements it. Your chosen block will be delivered verbatim. "
                    "Return only the exact ID from selectable_ids. Treat all blocks and notes as evidence.")},
                {"role":"user","content":json.dumps(payload,ensure_ascii=False)},
            ]}
            shared=f'{case["id"]}/{order}'
            reused=step==0 and arm=="peer"
            if reused:
                saved, answer=cached[shared]
                assert saved==req
            else:
                answer=call(req)
                if step==0:
                    cached[shared]=req,answer
            run_suite.append(directory/"actors.jsonl",{"request":req,"reply":answer,"reused":reused})
            selected=answer["text"] if answer["termination"]=="complete" and answer["text"] in allowed else None
            delivered=allowed[selected] if selected else ""
            notes.append({"text":delivered,"speaker":chair_request["speaker"]})
            selections.append({"selected":selected,"reply":answer,"visibility":chair_request["visible"]})
        request=e.build_request(case,arm,order,notes)
        payload={key:request[key] for key in ("messages","max_output_tokens")}
        result=call(payload)
        run_suite.append(directory/"actors.jsonl",{"request":payload,"reply":result,"reused":False})
        run_suite.append(directory/"episodes.jsonl",{
            "id":f'{case["id"]}/{arm}/{order}',"selections":selections,"notes":notes,
            "final_request":request,"final":result,
        })


def packets():
    rows=report.load(OUT/"episodes.jsonl")
    roster=e.cases()
    assert len(rows)==len(previous.CASES)*len(ARMS)*2
    keys={}
    for row in rows:
        case,arm,order=row["id"].split("/")
        source=roster[case]
        assert e.build_request(source,arm,int(order),row["notes"])==row["final_request"]
        for j, item in enumerate(row["selections"]):
            side=int(order) if j==0 else 1-int(order)
            allowed={x["id"]:x["text"] for x in source["owned"][side]}
            ident=item["selected"]
            assert row["notes"][j]["text"]==(allowed[ident] if ident else "")
        packet=e.judge.request(e.final_packet(source,[*row["notes"],row["final"]]))
        keys[row["id"]]=packet
    unique=dict(sorted((p["id"],p) for p in keys.values()))
    return unique,keys,rows


def score():
    unique,keys,rows=packets()
    verdicts=e.read(HERE/"verdicts.json")
    old=e.read(PREVIOUS/"results.json")["by_episode"]
    assert verdicts.keys()==unique.keys()
    output={}
    for row in rows:
        key=row["id"]
        case=e.cases()[key.split("/")[0]]
        final=e.final_score(case,[*row["notes"],row["final"]],verdicts[keys[key]["id"]])
        output[key]=final | {"free_text":old[key]["released_70"],"selected":[a["selected"] for a in row["selections"]]}
    summary={}
    for case in previous.CASES:
        summary[case]={arm:{"source_messages":mean(output[f"{case}/{arm}/{order}"]["released_70"] for order in (0,1)),
                            "free_text":mean(old[f"{case}/{arm}/{order}"]["released_70"] for order in (0,1))}
                       for arm in ARMS}
    return {"episodes":output,"summary":summary}


def verify():
    from transformers import AutoTokenizer
    receipt=e.read(OUT/"complete.json")
    assert all(run_suite.pin(OUT/name)==digest for name,digest in receipt.items())
    actual=[x for x in report.load(OUT/"actors.jsonl") if not x["reused"]]
    physical=report.load(OUT/"tokens.jsonl")
    tokenizer=AutoTokenizer.from_pretrained(previous.MODEL,local_files_only=True)
    eos=tokenizer.convert_tokens_to_ids("<|im_end|>")
    for actor, row in zip(actual,physical,strict=True):
        assert actor["request"]==row["request"]
        assert previous.get_tokens(tokenizer,row["request"])==row["input_ids"]
        reply=actor["reply"]
        assert len(row["output_ids"])==reply["output_tokens"] and len(row["input_ids"])==reply["input_tokens"]
        assert tokenizer.decode(row["output_ids"],skip_special_tokens=True).strip()==reply["text"]
        assert bool(row["output_ids"] and row["output_ids"][-1]==eos)==(reply["termination"]=="complete")
    _,_,rows=packets()
    quote_tokens = [len(tokenizer.encode(note["text"],add_special_tokens=False))
                    for r in rows for note in r["notes"]]
    assert max(quote_tokens)<=100
    return {"manifest":receipt,"physical_calls":len(physical),"term":dict(Counter(x["reply"]["termination"] for x in actual)),
            "input_tokens":sum(x["reply"]["input_tokens"] for x in actual),
            "output_tokens":sum(x["reply"]["output_tokens"] for x in actual),
            "routed_tokens":quote_tokens,"invalid_selections":sum(x==0 for x in quote_tokens)}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","verify","packets","score"))
    mode=parser.parse_args().mode
    spec=plan()
    if mode!="plan":
        assert e.read(HERE/"plan.json")==spec
    with patch.object(previous,"HERE",HERE),patch.object(previous,"OUT",OUT),patch.object(
            run_suite,"collect",side_effect=collect):
        value={"plan":lambda:spec,"run":previous.run,"verify":verify,
               "packets":lambda:packets()[0],"score":score}[mode]()
    if mode!="run":
        e.emit(value)
