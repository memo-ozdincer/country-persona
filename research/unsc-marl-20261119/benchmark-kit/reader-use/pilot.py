"""Generate blinded memo-use questions and score a frozen CPU reader."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent.parent / "crossbench/colombia2023/peer-question-repair-evidence/results.json"
MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
UNKNOWN = "The note does not explicitly establish this."
MEANINGS = ["source", "alternative", "unspecified"]
SYSTEM = ("Read only the supplied note, even if it might be factually wrong. Answer the "
          "question as a records clerk. Choose unspecified if the note omits the detail, "
          "its speaker, or the requested qualification. Do not import outside facts. Return one letter.")


def dataset():
    items = json.loads((HERE / "items.json").read_text())
    archive = json.loads(ARCHIVE.read_text())["cases"]
    rows = []
    for i,(family, evidence, group, q, good, bad, faithful, false) in enumerate(items):
        arms = {a:v["supplement"] for a,v in archive[family]["same_batch"].items()}
        arms.update(faithful=faithful, reversed=false, empty="No note was received.")
        for arm,note in arms.items():
            for rotation in range(3):
                order = [(j+rotation+i)%3 for j in range(3)]
                choices = [good,bad,UNKNOWN]
                labels = "\n".join(f"{chr(65+j)}. {choices[k]}" for j,k in enumerate(order))
                prompt = f"Note:\n{note}\n\nQuestion: {q}\n{labels}"
                rows.append(dict(item=i,family=family,source=evidence,group=group,arm=arm,
                                 order=[MEANINGS[k] for k in order],prompt=prompt))
    return rows


def run(directory):
    import torch
    import transformers
    from transformers import AutoTokenizer, AutoModelForCausalLM
    directory.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    launch = dict(host=socket.gethostname(),pid=os.getpid(),gpu_uuids=[],device="cpu",
                  start=subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                  command=[sys.executable,*sys.argv],model=str(MODEL),run_directory=str(directory.resolve()),
                  torch=torch.__version__,transformers=transformers.__version__,optimizer_updates=0,
                  sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/"items.json",ARCHIVE)})
    (directory/"launch.json").write_text(json.dumps(launch,indent=2))
    tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True,padding_side="left")
    model=AutoModelForCausalLM.from_pretrained(MODEL,local_files_only=True,dtype=torch.bfloat16,attn_implementation="sdpa").eval()
    labels=[tok.encode(x,add_special_tokens=False) for x in "ABC"]
    assert all(len(seq)==1 for seq in labels)
    rows=dataset()
    with (directory/"reads.jsonl").open("x") as f, torch.inference_mode():
        for start in range(0,len(rows),6):
            batch=rows[start:start+6]
            ids=[tok.apply_chat_template([{"role":"system","content":SYSTEM},{"role":"user","content":r["prompt"]}],
                                         tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False) for r in batch]
            inputs=tok.pad({"input_ids":ids},return_tensors="pt")
            logits=model(**inputs,use_cache=False,logits_to_keep=1).logits[:,-1,:].float()
            for row,inp,scores in zip(batch,ids,logits,strict=True):
                saved=scores[[s[0] for s in labels]].tolist()
                f.write(json.dumps(dict(**row,input_ids=inp,logits=saved,legal_mass=float(scores.softmax(-1)[[s[0] for s in labels]].sum())))+"\n")
            f.flush()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    os.environ["CUDA_VISIBLE_DEVICES"]=""
    run(parser.parse_args().directory)
