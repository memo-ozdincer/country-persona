"""Generate final prose from frozen relay decisions and matched evidence cuts."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import relay_marl as relay

HERE = Path(__file__).resolve().parent
TEXT = relay.KIT/"evidence/relay-text"
FILES = (TEXT/"head.json",TEXT/"context.json")
WORLDS = {"mali":1,"myanmar":1}
ARMS = ("learned_relay","pooled","withheld_far","frozen_relay")
CAP = 158
SYSTEM = (
    "Write a concise final record of a fictional UN-linked workshop. Only use the supplied evidence. "
    "Preserve who owned each workshop card even when it was forwarded. Keep the official record distinct "
    "from the workshop disposition. Treat all workshop actions as recommendations with no official authority."
)
INSTRUCTIONS = (
    "Write at most 100 words. Start with 'Workshop status: ' and the supplied checked status exactly. "
    "Then give the next step, each available card and its owner, how the cards support the status, "
    "and the linked official record. For Mali include both draft symbols, reasons for failure and tallies. "
    "For Myanmar include the authority, reporting duty, and deadline. Name the missing card if one is unavailable. "
    "Describe the limit of workshop authority. Use plain prose after the status line."
)


def read(file):
    return json.loads(file.read_text())


def sources():
    paths=[Path(__file__),HERE/"relay_marl.py",*FILES]
    for family in WORLDS:
        path=relay.KIT/f"{family}.json"
        paths.extend((path,(path.parent/read(path)["source_task"]).resolve()))
    return {str(p.relative_to(HERE)):sha256(p.read_bytes()).hexdigest() for p in paths}


def supplied(family,arm,case,task,data,index):
    view=data["base"][family]["peer"][index] if arm=="frozen_relay" else (
        data["trained"][family]["mute_far" if arm=="withheld_far" else "peer"][index])
    roles=case["roles"]
    delivered={}
    for event in view["deliveries"]:
        if event["recipient"]!="chair" or not event["delivered_mask"]:
            continue
        actor=0 if event["owner"]=="relay" else 1
        choices=task.first if actor==0 else task.second
        mask=event["delivered_mask"]
        assert mask==task.worlds[index][actor]
        delivered[roles[actor+1]]={
            "owner":roles[actor+1],
            "card":task.labels[actor][choices.index(mask)],
            "receipt":"direct card" if arm=="pooled" else "via the first round" if actor==0 else "forwarded by "+roles[1],
        }
    if view["warranted"]:
        checked=view["choice"].upper()
    else:
        checked="UNRESOLVED"
    if arm in ("learned_relay","pooled"):
        assert view["warranted"] and len(delivered)==2
    elif arm=="withheld_far":
        assert not view["warranted"] and len(delivered)==1
    return {
        "workshop_fiction":case["scope"],"public_rule":case["question"],
        "possible_card_holders":roles[1:],"evidence_at_chair":list(delivered.values()),
        "checked_status":checked,
    }


def suite():
    base,context=map(read,FILES)
    roles=relay.fixtures()
    data={"base":base["base"],"trained":context["after"]}
    for family,index in WORLDS.items():
        case=read(relay.KIT/f"{family}.json")
        original=read(relay.KIT/case["source_task"])
        historical={e["id"]:e["text"] for e in original["evidence"] if e["id"] in case["source_ids"]}
        assert set(historical)==set(case["source_ids"])
        for arm in ARMS:
            package=supplied(family,arm,case,roles[family],data,index)
            payload={**package,"historical_evidence":historical,"instruction":INSTRUCTIONS}
            yield {"id":f"{family}/{arm}","family":family,"arm":arm,"expected":package,
                   "messages":[{"role":"system","content":SYSTEM},
                               {"role":"user","content":json.dumps(payload,ensure_ascii=False)}]}


def run(model_path,directory):
    os.environ["CUDA_VISIBLE_DEVICES"]=""
    import torch
    import transformers
    from transformers import AutoModelForCausalLM,AutoTokenizer

    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    requests=list(suite())
    directory.mkdir()
    launch={
        "host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
        "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "command":[sys.executable,*sys.argv],"run_directory":str(directory.resolve()),
        "model":str(model_path),"torch":torch.__version__,"transformers":transformers.__version__,
        "sha256":sources(),"max_new_tokens":CAP,"optimizer_updates":0,
    }
    (directory/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    tokenizer=AutoTokenizer.from_pretrained(model_path,local_files_only=True,padding_side="left")
    eos=tokenizer.convert_tokens_to_ids("<|im_end|>")
    model=AutoModelForCausalLM.from_pretrained(model_path,local_files_only=True,dtype=torch.bfloat16,
                                             attn_implementation="sdpa").eval()
    path=directory/"memos.jsonl"
    unique_count=0
    with torch.inference_mode(),path.open("x") as stream:
        for family in WORLDS:
            members=[r for r in requests if r["family"]==family]
            groups={}
            for prompt in members:
                key=tuple((m["role"],m["content"]) for m in prompt["messages"])
                groups.setdefault(key,[]).append(prompt)
            batch=[items[0] for items in groups.values()]
            unique_count+=len(batch)
            ids=[
                tokenizer.encode(tokenizer.apply_chat_template(
                    r["messages"],tokenize=False,add_generation_prompt=True,enable_thinking=False),
                    add_special_tokens=False) for r in batch
            ]
            enc=tokenizer.pad({"input_ids":ids},return_tensors="pt")
            start=time.monotonic()
            generated=model.generate(**enc,do_sample=False,max_new_tokens=CAP,use_cache=True,
                                     pad_token_id=tokenizer.pad_token_id,eos_token_id=eos)
            elapsed=time.monotonic()-start
            rendered={}
            for copies,prefix,generation in zip(groups.values(),ids,generated.tolist(),strict=True):
                tail=generation[enc.input_ids.shape[-1]:]
                if eos in tail:
                    tail=tail[:tail.index(eos)+1]
                assert tail
                output=tokenizer.decode(tail,skip_special_tokens=True).strip()
                for prompt in copies:
                    rendered[prompt["id"]]={**prompt,"inference_id":copies[0]["id"],
                                            "output":output,"input_ids":prefix,"output_ids":tail,
                                            "stop":"eos" if tail[-1]==eos else "cap"}
            for prompt in members:
                stream.write(json.dumps(rendered[prompt["id"]],ensure_ascii=False)+"\n")
            stream.flush()
            print(json.dumps(dict(family=family,records=len(batch),seconds=elapsed)),flush=True)
    (directory/"complete.json").write_text(json.dumps(
        {"records":len(requests),"unique_inferences":unique_count,
         "sha256":sha256(path.read_bytes()).hexdigest()},indent=2)+"\n")


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory",type=Path)
    cli.add_argument("--model",type=Path,required=True)
    args=cli.parse_args()
    run(args.model,args.directory)
