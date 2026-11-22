"""Measure one-token Qwen actions from prose observations in the relay."""
import argparse
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import relay_marl as core

LETTERS="ABCDEFGH"
HERE=Path(__file__).resolve().parent
SYSTEM=("Work in a fictional decision workshop. Use only your card, the public rule and "
        "actually delivered messages. Votes and messages here do not change any official UN decision. "
        "Return only the letter of one listed action.")


def tasks():
    independent=core.Task("synthetic archive review",("retain","reopen","impasse"),
                          (1,2),(1,2),(("retain","reopen"),("retain","reopen")))
    return {"training":independent,**core.fixtures()}


def display(task,mask):
    if not mask:
        return "not received"
    return " or ".join(a for i,a in enumerate(task.actions[:-1]) if mask&(1<<i))


def public(task):
    return (f"{task.name}. Select a jointly feasible option or {task.actions[-1]} if no option overlaps. "
            f"Possible relay cards: {', '.join(display(task,v) for v in task.first)}. "
            f"Possible far cards: {', '.join(display(task,v) for v in task.second)}.")


def describe(task, phase, one, two=0, sent=False):
    if phase==3:
        legal=tuple(range(len(task.actions)))
        listing=task.actions
        body=(f"You are chair. Relay's delivered card: {display(task,one)}. "
              f"Far delegate's delivered card: {display(task,two)}. Decide from available evidence.")
    else:
        legal,_=core.message_rows(phase,one,two,sent)
        labels={core.PASS:"Pass",core.OWN:"Send your own card",core.FORWARD:"Forward far delegate's card"}
        listing=tuple(labels[x] for x in legal)
        role="far delegate" if phase==0 else "relay delegate"
        body=f"You are the {role}. Your card: {display(task,one)}."
        if phase==0:
            body+=" This is round one, your only opportunity to send to the relay."
        elif phase==1:
            body+=" This is round one. You may send one card to the chair. A peer card arrives after this turn."
        else:
            body+=(f" This is the last round. The chair {'has' if sent else 'does not have'} your card. "
                   f"From the far delegate: {display(task,two)}.")
    prompt="\n".join((public(task),body,*(f"{c}. {v}" for c,v in zip(LETTERS,listing))))
    return legal,[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]


def observations():
    for name,task in tasks().items():
        scenes=(
            *((0,a,0,False) for a in task.second),
            *((1,a,0,False) for a in task.first),
            *((2,a,b,sent) for a,b,sent in product(task.first,(0,*task.second),(False,True))),
            *((3,a,b,False) for a,b in product((0,*task.first),(0,*task.second))),
        )
        for phase,left,right,sent in scenes:
            key=(name,phase,left,right,sent)
            legal,messages=describe(task,phase,left,right,sent)
            if len(legal)>1:
                yield {"observation":key,"legal":legal,"messages":messages}


def hashes():
    return {str(p.relative_to(HERE)):sha256(p.read_bytes()).hexdigest() for p in (
        Path(__file__),HERE/"relay_marl.py",core.KIT/"mali.json",core.KIT/"myanmar.json")}


def score(model_path, directory):
    os.environ["CUDA_VISIBLE_DEVICES"]=""
    import torch
    import transformers
    from transformers import AutoModelForCausalLM,AutoTokenizer

    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    directory.mkdir()
    launch={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
            "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
            "command":[sys.executable,*sys.argv],"run_directory":str(directory.resolve()),
            "model_path":str(model_path.resolve()),"torch":torch.__version__,
            "transformers":transformers.__version__,"sha256":hashes()}
    (directory/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    tokenizer=AutoTokenizer.from_pretrained(model_path,local_files_only=True,padding_side="left")
    all_rows=[]
    for scene in observations():
        rendered=tokenizer.apply_chat_template(scene["messages"],tokenize=False,add_generation_prompt=True,
                                               enable_thinking=False)
        prefix=tokenizer.encode(rendered,add_special_tokens=False)
        label_ids=[]
        for character in LETTERS[:len(scene["legal"])]:
            identifier,=tokenizer.encode(character,add_special_tokens=False)
            assert tokenizer.encode(rendered+character,add_special_tokens=False)==prefix+[identifier]
            label_ids.append(identifier)
        assert len(set(label_ids))==len(label_ids)
        all_rows.append({**scene,"input_ids":prefix,"label_ids":label_ids})
    print(f"{len(all_rows)} prompts; {sum(len(x['input_ids']) for x in all_rows)} input tokens",flush=True)
    model=AutoModelForCausalLM.from_pretrained(model_path,local_files_only=True,dtype=torch.bfloat16,
                                             attn_implementation="sdpa").eval()
    ordered=sorted(all_rows,key=lambda r:len(r["input_ids"]))
    artifact=directory/"actions.jsonl"
    with torch.inference_mode(),artifact.open("x") as stream:
        for start in range(0,len(ordered),8):
            chunk=ordered[start:start+8]
            encoded=tokenizer.pad({"input_ids":[r["input_ids"] for r in chunk]},return_tensors="pt")
            logits=model(**encoded,use_cache=False,logits_to_keep=1).logits[:,-1].float()
            for row,full in zip(chunk,logits,strict=True):
                legal=full[row["label_ids"]]
                mass=float((legal.logsumexp(0)-full.logsumexp(0)).exp())
                stream.write(json.dumps({**row,"scores":legal.tolist(),"legal_mass":mass},ensure_ascii=False)+"\n")
            stream.flush()
            print(f"{start+len(chunk)}/{len(ordered)} complete",flush=True)
    (directory/"complete.json").write_text(json.dumps({
        "records":len(all_rows),"sha256":sha256(artifact.read_bytes()).hexdigest()},indent=2)+"\n")


def read(directory):
    source=directory/"actions.jsonl"
    finish=json.loads((directory/"complete.json").read_text())
    assert finish["sha256"]==sha256(source.read_bytes()).hexdigest()
    lock=json.loads((directory/"launch.json").read_text())
    assert lock["sha256"]==hashes()
    rows={tuple(x["observation"]):x for x in map(json.loads,source.read_text().splitlines())}
    assert len(rows)==finish["records"]
    for plan in observations():
        result=rows[plan["observation"]]
        assert list(plan["legal"])==result["legal"] and plan["messages"]==result["messages"]
    return rows


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory",type=Path)
    cli.add_argument("--model",type=Path,required=True)
    args=cli.parse_args()
    score(args.model,args.directory)
