"""Execute and verify an opt-in slice using the v1.7 evaluator."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
from statistics import mean
import subprocess
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parents[1]/"benchmark-v1.7"
sys.path.insert(0,str(RELEASE))
import evaluate as e
import report
import run_suite

MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
CASES = ("myanmar","tribunals")
OUT = HERE/"evidence"


def plan():
    assert run_suite.verify_release()=="1.7"
    return {"cases":list(CASES),"arm_order":list(e.ARMS),"orders":[0,1],"model":str(MODEL),
            "index_sha256":run_suite.pin(MODEL/"model.safetensors.index.json"),
            "release_sha256":run_suite.pin(RELEASE/"release.json"),
            "collector_sha256":run_suite.pin(Path(__file__)),
            "protocol_sha256":run_suite.pin(HERE/"protocol.md")}


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")


def choose_device():
    gpu = os.environ.get("CUDA_VISIBLE_DEVICES")
    if gpu == "":
        return {"placement":"cpu","cpu_model":next(line.split(":",1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name"))}
    assert gpu and gpu.startswith("GPU-") and "," not in gpu
    args = ["nvidia-smi","-i",gpu]
    name, uid, used = [x.strip() for x in subprocess.check_output(
        [*args,"--query-gpu=name,uuid,memory.used","--format=csv,noheader,nounits"],text=True).split(",")]
    assert uid==gpu and used=="0", (name,uid,used)
    assert not subprocess.check_output([*args,"--query-compute-apps=pid","--format=csv,noheader"],text=True).strip()
    return {"placement":"cuda:0","gpu_uuid":uid,"gpu_name":name}


def get_tokens(tokenizer, request):
    serialized = tokenizer.apply_chat_template(request["messages"],tokenize=False,add_generation_prompt=True,
                                               enable_thinking=False)
    return tokenizer.encode(serialized,add_special_tokens=False)


def run():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, __version__

    device = choose_device()
    OUT.mkdir()
    write(OUT/"launch.json",device | {
        "host":socket.gethostname(),"pid":os.getpid(),"start":subprocess.check_output(
            ["ps","-p",str(os.getpid()),"-o","lstart="],text=True).strip(),
        "argv":[sys.executable,*sys.argv],"run_directory":str(OUT),"dtype":"bfloat16",
        "torch":torch.__version__,"transformers":__version__,"plan_sha256":run_suite.pin(HERE/"plan.json")})
    if device["placement"]=="cpu":
        torch.set_num_threads(12)
        torch.set_num_interop_threads(1)
    tokenizer = AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL,local_files_only=True,dtype=torch.bfloat16,
                                               attn_implementation="sdpa",device_map=device["placement"]).eval()
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    roster = e.cases()
    with patch.object(e,"cases",return_value={key:roster[key] for key in CASES}), torch.inference_mode():
        def call(request):
            ids = get_tokens(tokenizer,request)
            x = torch.tensor([ids],device=device["placement"])
            config = GenerationConfig(max_new_tokens=request["max_output_tokens"],do_sample=False,
                                      eos_token_id=eos,pad_token_id=tokenizer.pad_token_id)
            output = model.generate(input_ids=x,attention_mask=torch.ones_like(x),
                                    generation_config=config)[0,len(ids):].tolist()
            reply = {"text":tokenizer.decode(output,skip_special_tokens=True).strip(),
                     "input_tokens":len(ids),"output_tokens":len(output),
                     "termination":"complete" if output and output[-1]==eos else "cap"}
            run_suite.append(OUT/"tokens.jsonl",{"request":request,"input_ids":ids,"output_ids":output})
            return reply

        run_suite.collect(call,OUT)
    write(OUT/"complete.json",{name:run_suite.pin(OUT/name) for name in
                              ("launch.json","actors.jsonl","episodes.jsonl","tokens.jsonl")})


def packets():
    roster = e.cases()
    rows = report.load(OUT/"episodes.jsonl")
    expected = {f"{case}/{arm}/{order}" for case in CASES for arm in e.ARMS for order in (0,1)}
    assert {row["id"] for row in rows}==expected and len(rows)==len(expected)
    cards = {}
    linked = {}
    by_episode = {row["id"]:row for row in rows}
    for key,row in by_episode.items():
        name,arm,order = key.split("/")
        case = roster[name]
        calls = e.validate_calls(case,arm,int(order),row["calls"])
        packet = e.judge.request(e.final_packet(case,calls))
        cards[packet["id"]] = packet
        linked[key] = packet["id"]
        if arm=="peer":
            baseline = by_episode[f"{name}/independent/{order}"]["calls"][0]
            assert {k:v for k,v in baseline.items() if k!="request_sha256"} == {
                k:v for k,v in row["calls"][0].items() if k!="request_sha256"}
    return dict(sorted(cards.items())),linked,by_episode


def score():
    cards,links,records = packets()
    verdicts = e.read(HERE/"verdicts.json")
    assert verdicts.keys()==cards.keys()
    cases = e.cases()
    results = {}
    for key,row in records.items():
        name,arm,order = key.split("/")
        case = cases[name]
        verified = e.validate_calls(case,arm,int(order),row["calls"])
        results[key] = e.final_score(case,verified,verdicts[links[key]])
    deltas = {}
    for name in CASES:
        deltas[name] = {order: {arm: results[f"{name}/{arm}/{order}"]["released_70"] for arm in e.ARMS}
                        for order in (0,1)}
    return {"by_episode":results,"scores":deltas,"peer_effect":{name:mean(
        order["peer"]-order["independent"] for order in data.values()) for name,data in deltas.items()}}


def verify():
    from transformers import AutoTokenizer

    manifest=e.read(OUT/"complete.json")
    assert all(run_suite.pin(OUT/key)==digest for key,digest in manifest.items())
    tokenizer=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    eos=tokenizer.convert_tokens_to_ids("<|im_end|>")
    actors=report.load(OUT/"actors.jsonl")
    actual=[row for row in actors if not row["reused"]]
    tokens=report.load(OUT/"tokens.jsonl")
    for actor,trace in zip(actual,tokens,strict=True):
        request, reply = actor["request"],actor["reply"]
        assert trace["request"]=={key:request[key] for key in ("messages","max_output_tokens")}
        assert trace["input_ids"]==get_tokens(tokenizer,request)
        ids=trace["output_ids"]
        assert len(ids)==reply["output_tokens"] and len(trace["input_ids"])==reply["input_tokens"]
        assert tokenizer.decode(ids,skip_special_tokens=True).strip()==reply["text"]
        assert bool(ids and ids[-1]==eos)==(reply["termination"]=="complete")
    cards,_,_=packets()
    return {"manifest":manifest,"logical_calls":len(actors),"physical_calls":len(actual),"final_packets":len(cards),
            "termination":dict(Counter(row["reply"]["termination"] for row in actual)),
            "input_tokens":sum(row["reply"]["input_tokens"] for row in actual),
            "output_tokens":sum(row["reply"]["output_tokens"] for row in actual)}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","packets","score","verify"))
    mode=parser.parse_args().mode
    spec=plan()
    if mode!="plan":
        assert spec==e.read(HERE/"plan.json")
    data={"plan":lambda:spec,"run":run,"packets":lambda:packets()[0],"score":score,"verify":verify}[mode]()
    if mode!="run":
        e.emit(data)
