"""Capture and replay a bounded live calibration of the published judge."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"historical-benchmark-slice"
sys.path.insert(0,str(BASE))
import slice_run as prior
from calibrate import anchors, process_anchors, score

suite=prior.run_suite
e=prior.e
OUT=HERE/"evidence"
BATCH=4


def fixtures():
    return {"final":anchors(),"process":process_anchors()}


def requests():
    grouped={}
    for mode,packets in fixtures().items():
        system=(prior.RELEASE/f"{mode}-judge.md").read_text()
        grouped[mode]=[
            {"id":key,"request":suite.judge_request(system,e.judge.request(packet) if mode=="final" else packet)}
            for key,(packet,*_) in packets.items()
        ]
    return grouped


def plan():
    assert suite.verify_release()=="1.7"
    return {"release":suite.pin(prior.RELEASE/"release.json"),
            "model_index":suite.pin(prior.MODEL/"model.safetensors.index.json"),
            "model":str(prior.MODEL),"batch":BATCH,
            "protocol":suite.pin(HERE/"protocol.md"),"script":suite.pin(Path(__file__)),
            "request_hashes":{mode:[e.checksum(r["request"]) for r in rows] for mode,rows in requests().items()}}


def run():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, __version__

    device=prior.choose_device()
    OUT.mkdir()
    prior.write(OUT/"launch.json",device | {"host":socket.gethostname(),"pid":os.getpid(),
        "start":subprocess.check_output(["ps","-p",str(os.getpid()),"-o","lstart="],text=True).strip(),
        "command":[sys.executable,*sys.argv],"run_directory":str(OUT),
        "plan_sha256":suite.pin(HERE/"plan.json"),"torch":torch.__version__,"transformers":__version__})
    if device["placement"]=="cpu":
        torch.set_num_threads(12)
        torch.set_num_interop_threads(1)
    tokenizer=AutoTokenizer.from_pretrained(prior.MODEL,local_files_only=True)
    eos=tokenizer.convert_tokens_to_ids("<|im_end|>")
    pad=tokenizer.pad_token_id
    assert isinstance(pad,int) and pad!=eos
    model=AutoModelForCausalLM.from_pretrained(prior.MODEL,local_files_only=True,dtype=torch.bfloat16,
                                             attn_implementation="sdpa",device_map=device["placement"]).eval()
    config=GenerationConfig(max_new_tokens=suite.JUDGE_BUDGET,do_sample=False,eos_token_id=eos,pad_token_id=pad)
    with torch.inference_mode():
        for mode,rows in requests().items():
            for start in range(0,len(rows),BATCH):
                chunk=rows[start:start+BATCH]
                prompts=[prior.get_tokens(tokenizer,row["request"]) for row in chunk]
                width=max(map(len,prompts))
                x=torch.tensor([[pad]*(width-len(ids))+ids for ids in prompts],device=device["placement"])
                og=torch.tensor([[0]*(width-len(ids))+[1]*len(ids) for ids in prompts],device=device["placement"])
                outputs=model.generate(input_ids=x,attention_mask=og,generation_config=config)[:,width:].tolist()
                for row,ids,out in zip(chunk,prompts,outputs,strict=True):
                    stopped=eos in out
                    tokens=out[:out.index(eos)+1] if stopped else out
                    suite.append(OUT/"tokens.jsonl",{"mode":mode,**row,"input_ids":ids,"padded_width":width,
                        "output_ids":tokens,"reply":{"text":tokenizer.decode(tokens,skip_special_tokens=True).strip(),
                        "input_tokens":len(ids),"output_tokens":len(tokens),"termination":"complete" if stopped else "cap"}})
    prior.write(OUT/"complete.json",{name:suite.pin(OUT/name) for name in ("launch.json","tokens.jsonl")})


def replay(directory,rows):
    directory.mkdir()
    stream=iter(rows)
    def call(request):
        row=next(stream)
        assert row["request"]==request
        return row["reply"]
    try:
        suite.calibrate_judge(call,directory)
    except ValueError as err:
        if str(err)!="Incomplete anchor coverage. See calibration.json.":
            raise
    assert next(stream,None) is None
    return audit(directory,rows)


def audit(directory,rows):
    official=e.read(directory/"calibration.json")
    result={"official":official,"usage":{
        "input":sum(row["reply"]["input_tokens"] for row in rows),
        "output":sum(row["reply"]["output_tokens"] for row in rows),
    },"modes":{}}
    for mode,items in fixtures().items():
        valid=e.read(directory/f"{mode}-verdicts.json")
        selected={key:items[key] for key in valid}
        with patch("calibrate.anchors" if mode=="final" else "calibrate.process_anchors",return_value=selected):
            usable=score(valid,mode)
        raw_totals=Counter()
        raw_labels=[]
        for row in rows:
            if row["mode"]!=mode:
                continue
            expected=items[row["id"]][1]
            raw_totals["expected_labels"]+=len(expected)
            try:
                payload=json.loads(row["reply"]["text"])
                if mode=="final":
                    labels={unit["id"]:unit["status"] for unit in payload["units"]}
                    labels["guard"]=payload["guard"]["status"]
                else:
                    labels={rating["id"]:rating["points"] for rating in payload["ratings"]}
            except (ValueError,TypeError,KeyError):
                continue
            raw_totals["parseable_packets"]+=1
            for name,target in expected.items():
                observed=labels.get(name)
                raw_totals["parsed_labels"]+=int(name in labels)
                raw_totals["correct"]+=int(observed==target)
                if observed!=target:
                    raw_labels.append({"packet":row["id"],"label":name,"expected":target,"observed":observed})
        result["modes"][mode]={"quote_valid_label_agreement":usable,"raw_label_agreement":dict(raw_totals),
                               "raw_label_mismatches":raw_labels}
    return result


def verify(rows):
    from transformers import AutoTokenizer

    receipt=e.read(OUT/"complete.json")
    assert all(suite.pin(OUT/name)==digest for name,digest in receipt.items())
    tok=AutoTokenizer.from_pretrained(prior.MODEL,local_files_only=True)
    eos=tok.convert_tokens_to_ids("<|im_end|>")
    expected=[(mode,r) for mode,group in requests().items() for r in group]
    for row,(mode,item) in zip(rows,expected,strict=True):
        assert (row["id"],row["request"],row["mode"])==(item["id"],item["request"],mode)
        assert prior.get_tokens(tok,item["request"])==row["input_ids"]
        ids=row["output_ids"]
        reply=row["reply"]
        assert (reply["input_tokens"],reply["output_tokens"])==(len(row["input_ids"]),len(ids))
        assert tok.decode(ids,skip_special_tokens=True).strip()==reply["text"]
        assert bool(ids and ids[-1]==eos)==(reply["termination"]=="complete")
    return receipt | {"packets":len(rows)}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","replay","verify"))
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    spec=plan()
    if args.mode!="plan":
        assert spec==e.read(HERE/"plan.json")
    if args.mode=="plan":
        e.emit(spec)
    elif args.mode=="run":
        run()
    else:
        rows=prior.report.load(OUT/"tokens.jsonl")
        e.emit(verify(rows) if args.mode=="verify" else replay(args.output,rows))
