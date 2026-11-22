"""Capture a free-written 2744 record for each delivery receipt set."""
import argparse
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
BASE = RUNS / "delisting-2744"
RELEASE = RUNS.parent / "benchmark-v1.6"
OUT = HERE / "evidence"
MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
BUDGET = 280
THREADS = 12
SYSTEM = (
    "Write a complete Security Council decision record, at most 160 words, using only the supplied "
    "evidence. First state the disposition and scope exactly. Attribute any delivered statement to "
    "its speaker and describe any delivered adopted clause separately. If those sources support a "
    "specific relationship, explicitly explain it without treating a preference as an adopted "
    "requirement, or a report as a decision. Keep actors, decision authority, timing and any "
    "exception distinct. Leave out details that were not delivered. Return only the final record."
)


def read(path):
    return json.loads(path.read_text())


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n")


def requests(case):
    result = {}
    for early, late in product((None, *case["early"]), (None, *case["late"])):
        key = f"{early}/{late}"
        payload = {"task": case["task"], "public_record": [s["text"] for s in case["public"]]}
        if early is not None:
            message = case["early"][early]["text"]
            if early == "a3plus":
                message = message.replace("urged effective implementation", "hoped for full implementation")
            payload["delegate_statement"] = message
        if late is not None:
            payload["adopted_document"] = case["late"][late]["text"]
        result[key] = {"id": key, "max_output_tokens": BUDGET, "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]}
    assert len(result) == 12
    return result


def plan():
    case = read(BASE/"case.json")
    files = (Path(__file__), HERE/"protocol.md", HERE/"rubric.json", HERE/"replay.py",
             BASE/"case.json", BASE/"plan.json", BASE/"results.json", RELEASE/"release.json")
    return {"requests": requests(case), "checkpoint_index_sha256": pin(MODEL/"model.safetensors.index.json"),
            "pins": {str(p.relative_to(RUNS.parent)):pin(p) for p in files}}


def locked():
    spec = plan()
    assert spec == read(HERE/"plan.json")
    return spec


def prompt(tokenizer, request):
    text = tokenizer.apply_chat_template(request["messages"], tokenize=False, add_generation_prompt=True,
                                         enable_thinking=False)
    return tokenizer.encode(text, add_special_tokens=False)


def append(file, row):
    file.write(json.dumps(row, ensure_ascii=False)+"\n")
    file.flush()


def device_receipt():
    selected = os.environ.get("CUDA_VISIBLE_DEVICES")
    if selected == "":
        cpu = next(line.split(":",1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                   if line.startswith("model name"))
        return {"device":"cpu", "cpu_model":cpu, "intraop_threads":THREADS}
    assert selected and selected.startswith("GPU-") and "," not in selected
    fields = subprocess.check_output(["nvidia-smi","-i",selected,"--query-gpu=name,uuid,memory.used",
                                      "--format=csv,noheader,nounits"],text=True).strip()
    name, uuid, used = [x.strip() for x in fields.split(",")]
    assert uuid == selected and used == "0"
    assert not subprocess.check_output(["nvidia-smi","-i",selected,"--query-compute-apps=pid",
                                        "--format=csv,noheader"],text=True).strip()
    return {"device":"cuda","gpu_name":name,"gpu_uuid":uuid}


def run():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, __version__

    spec = locked()
    device = device_receipt()
    if device["device"] == "cpu":
        torch.set_num_threads(THREADS)
        torch.set_num_interop_threads(1)
    OUT.mkdir()
    write(OUT/"launch.json", device | {
        "host":socket.gethostname(), "pid":os.getpid(), "process_start": subprocess.check_output(
            ["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "command":[sys.executable,*sys.argv], "run_directory":str(OUT),
        "plan_sha256":pin(HERE/"plan.json"),"checkpoint_index_sha256":spec["checkpoint_index_sha256"],
        "torch":torch.__version__,"transformers":__version__,"dtype":"bfloat16",
        "attention":"sdpa","optimizer_updates":0})
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    placement = "cpu" if device["device"] == "cpu" else "cuda:0"
    model = AutoModelForCausalLM.from_pretrained(MODEL, local_files_only=True, dtype=torch.bfloat16,
                                               attn_implementation="sdpa", device_map=placement).eval()
    gen = GenerationConfig(max_new_tokens=BUDGET, do_sample=False, eos_token_id=eos,
                           pad_token_id=tok.pad_token_id, use_cache=True)
    with (OUT/"calls.jsonl").open("w") as calls, (OUT/"tokens.jsonl").open("w") as tokens, torch.inference_mode():
        for key, request in spec["requests"].items():
            ids = prompt(tok,request)
            x = torch.tensor([ids],device=placement)
            out = model.generate(input_ids=x,attention_mask=torch.ones_like(x),generation_config=gen)
            output = out[0,len(ids):].tolist()
            reply = {"text":tok.decode(output,skip_special_tokens=True).strip(),
                     "termination":"complete" if output and output[-1]==eos else "cap",
                     "input_tokens":len(ids),"output_tokens":len(output)}
            append(calls, {"id":key,"reply":reply})
            append(tokens, {"input_ids":ids,"output_ids":output,"reply":reply})
    write(OUT/"complete.json", {key:pin(OUT/key) for key in ("calls.jsonl","tokens.jsonl","launch.json")})


def verify():
    from transformers import AutoTokenizer

    spec = locked()
    receipt = read(OUT/"complete.json")
    assert set(receipt)=={"calls.jsonl","tokens.jsonl","launch.json"}
    assert all(pin(OUT/k)==v for k,v in receipt.items())
    launch = read(OUT/"launch.json")
    assert launch["plan_sha256"] == pin(HERE/"plan.json")
    assert launch["checkpoint_index_sha256"] == spec["checkpoint_index_sha256"]
    assert launch["optimizer_updates"] == 0
    tok = AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    calls,tokens=([json.loads(line) for line in (OUT/name).read_text().splitlines()]
                  for name in ("calls.jsonl","tokens.jsonl"))
    outputs={}
    for (key,request),call,trace in zip(spec["requests"].items(),calls,tokens,strict=True):
        assert call["id"]==key and call["reply"]==trace["reply"]
        assert trace["input_ids"]==prompt(tok,request)
        r=call["reply"]
        assert len(trace["input_ids"])==r["input_tokens"]
        ids=trace["output_ids"]
        assert len(ids)==r["output_tokens"]<=BUDGET
        assert tok.decode(ids,skip_special_tokens=True).strip()==r["text"]
        assert bool(ids and ids[-1]==eos)==(r["termination"]=="complete")
        outputs[key]=r
    return {"manifest":receipt,"outputs":outputs}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","verify"))
    mode=parser.parse_args().mode
    if mode=="run":
        run()
    else:
        print(json.dumps((plan if mode=="plan" else verify)(),ensure_ascii=False,indent=2))
