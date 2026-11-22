"""Read three role-local mandate fields from one constrained model call."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import factor

HERE=factor.HERE
base=factor.base
FIELDS={"scope":base["SET_TEXT"],**factor.FIELDS}
LABELS="ABCDEFGHIJKLMNOP"
LOCK=HERE/"joint-receipt-lock.json"


def suite():
    profiles=list(product(*(tuple(v) for v in FIELDS.values())))
    assert len(profiles)==len(LABELS)
    for role,card in factor.LOAD(base["CASE"])["cards"].items():
        for index,order in enumerate((profiles,profiles[::-1])):
            choices={letter:dict(zip(FIELDS,profile,strict=True))
                     for letter,profile in zip(LABELS,order,strict=True)}
            payload={"private_mandate":card,"field_definitions":FIELDS,"answer_profiles":choices}
            yield {"id":f"{role}/{index}","labels":LABELS,"profiles":order,"messages":[
                {"role":"system","content":"Read the fictional private mandate. Identify its publication timing, consultation leadership and confidentiality safeguard requirements. Choose the single answer profile whose three definitions all match. Respond with only its letter."},
                {"role":"user","content":json.dumps(payload,ensure_ascii=False)},
            ]}


def score(rows):
    counts=Counter()
    fields={}
    for plan in suite():
        logits=rows[plan["id"]]["label_logits"]
        best=max(logits)
        winners=[p for p,s in zip(plan["profiles"],logits,strict=True) if s==best]
        role,_=plan["id"].split("/")
        fields.setdefault(role,[]).append(winners)
    evidence,readings={},{}
    options=factor.LOAD(base["CASE"])["options"]
    for role,orders in fields.items():
        want={ "scope":base["REFERENCE"][role],**factor.EXPECTED[role]}
        fields_read={}
        for index,(field,reference) in enumerate(want.items()):
            values={p[index] for order in orders for p in order}
            value=next(iter(values)) if len(values)==1 else None
            fields_read[field]=value
            counts["field","unknown" if value is None else "correct" if value==reference else "wrong"]+=1
        counts["profile","unanimous_correct" if fields_read==want else "incomplete_or_wrong"]+=1
        readings[role]={"orders":orders,"stable_fields":fields_read,"reference":want}
        scope,lead,safeguard=fields_read.values()
        for opt in options:
            passes=(
                None if scope is None else opt["scope"] not in base["GROUPS"][scope],
                None if lead is None else lead=="either" or opt["lead"]=="asean",
                None if safeguard is None else safeguard=="optional" or opt["safeguard"],
            )
            evidence[role,opt["id"]]=False if False in passes else None if None in passes else True
        evidence[role,"all"]=scope
    synthetic={}
    for plan in base["suite"]():
        role,kind,name,_=plan["id"].split("/")
        value=evidence[role,name]
        if kind=="package":
            value="accept" if value is True else "reject" if value is False else None
        synthetic[plan["id"]]={"label_logits":[int(value==v) for v in plan["values"]]}
    result=base["score"](synthetic)
    result["totals"].update({"/".join(k):v for k,v in counts.items()})
    result["joint_readings"]=readings
    result["note"]="Projected package and scope votes. Actual joint logits are in predictions.jsonl. The authored menu gate remains in effect."
    return result


def digest(file):
    return sha256(file.read_bytes()).hexdigest()


def hashes():
    return {str(p.relative_to(HERE.parents[1])):digest(p) for p in
            (Path(__file__).resolve(),HERE/"case.json",HERE/"factor.py",HERE/"run.py",base["TRAINED"])}


def run(model_path,output):
    os.environ["CUDA_VISIBLE_DEVICES"]=""
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    output.mkdir()
    launch={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
            "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
            "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
            "model":str(model_path.resolve()),"torch":torch.__version__,
            "transformers":transformers.__version__,"optimizer_updates":0,"sha256":hashes()}
    (output/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    tokenizer=AutoTokenizer.from_pretrained(model_path,local_files_only=True,padding_side="left")
    label_ids=[]
    for label in LABELS:
        token,=tokenizer.encode(label,add_special_tokens=False)
        label_ids.append(token)
    assert len(set(label_ids))==len(LABELS)
    model=AutoModelForCausalLM.from_pretrained(model_path,local_files_only=True,dtype=torch.bfloat16,
                                               attn_implementation="sdpa").eval()
    plans=list(suite())
    prefixes=[]
    for row in plans:
        rendered=tokenizer.apply_chat_template(row["messages"],tokenize=False,
                                               add_generation_prompt=True,enable_thinking=False)
        prefix=tokenizer.encode(rendered,add_special_tokens=False)
        assert all(tokenizer.encode(rendered+label,add_special_tokens=False)==prefix+[token]
                   for label,token in zip(LABELS,label_ids,strict=True))
        prefixes.append(prefix)
    encoded=tokenizer.pad({"input_ids":prefixes},return_tensors="pt")
    with torch.inference_mode():
        logits=model(**encoded,logits_to_keep=1,use_cache=False).logits[:,-1].float()
        legal=logits[:,label_ids]
        masses=(legal.logsumexp(-1)-logits.logsumexp(-1)).exp().tolist()
    rows=[{**plan,"input_ids":prefix,"label_ids":label_ids,"label_logits":scores,"legal_mass":mass}
          for plan,prefix,scores,mass in zip(plans,prefixes,legal.tolist(),masses,strict=True)]
    trace=output/"predictions.jsonl"
    trace.write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row in rows))
    result=score({r["id"]:r for r in rows})
    (output/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    (output/"complete.json").write_text(json.dumps({"records":len(rows),"sha256":digest(trace)})+"\n")
    print({k:v for k,v in result["totals"].items() if k.count("/")==1},flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("lock","run","replay"))
    parser.add_argument("directory",type=Path,nargs="?")
    parser.add_argument("--model",type=Path)
    args=parser.parse_args()
    if args.mode=="lock":
        with LOCK.open("x") as file:
            json.dump({"records":len(list(suite())),"sha256":hashes()},file,indent=2)
            file.write("\n")
        return
    lock=factor.LOAD(LOCK)
    assert lock["sha256"]==hashes()
    if args.mode=="run":
        run(args.model,args.directory)
        return
    trace=args.directory/"predictions.jsonl"
    rows=list(map(json.loads,trace.read_text().splitlines()))
    assert len(rows)==lock["records"]
    assert factor.LOAD(args.directory/"complete.json")=={"records":len(rows),"sha256":digest(trace)}
    assert factor.LOAD(args.directory/"launch.json")["sha256"]==hashes()
    for plan,row in zip(suite(),rows,strict=True):
        assert json.loads(json.dumps(plan))=={k:row[k] for k in plan}
    assert json.loads(json.dumps(score({r["id"]:r for r in rows})))==factor.LOAD(args.directory/"metrics.json")
    print(json.dumps({"exact":True,"records":len(rows),"hashes":len(hashes())}))


if __name__=="__main__":
    main()
