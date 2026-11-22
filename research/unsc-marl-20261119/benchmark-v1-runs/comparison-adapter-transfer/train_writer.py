"""Run a bounded completion-only LoRA fit and same-device held generation."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE=Path(__file__).resolve().parent
RUNS=HERE.parent
HOLD=RUNS/"delisting-comparison-writer"
OUT=HERE/"evidence"
sys.path.insert(0,str(HOLD))
import collect_relation as old
import examples

MODEL=old.chair.MODEL
read=old.read
write=old.chair.write
pin=old.pin
LAYERS=tuple(f"model.layers.{i}.self_attn.{p}" for i in (27,31) for p in ("q_proj","v_proj"))
SEED=117443
EPOCHS=2
LR=0.0002


def plan():
    training=examples.build()
    assert len(training)==12
    assert {r["id"].split("/")[0] for r in training}=={"2721","2664"}
    assert sum(r["target"]=="NONE" for r in training)==6
    assert all(len(r["target"].split())<=40 for r in training)
    held=read(HOLD/"plan.json")
    files=(Path(__file__),HERE/"examples.py",HERE/"protocol.md",HOLD/"plan.json",HOLD/"score.py",
           HOLD/"verified.json",RUNS/"afghanistan-2721-source-contrast/case.json",
           RUNS/"humanitarian-2664-admission/case.json")
    return {"training":training,"held":held["requests"],"system":old.SYSTEM,"seed":SEED,
            "epochs":EPOCHS,"learning_rate":LR,"target_layers":list(LAYERS),
            "checkpoint_index_sha256":held["checkpoint_index_sha256"],
            "pins":{str(x.relative_to(RUNS.parent)):pin(x) for x in files}}


def encode(tokenizer,messages):
    return old.chair.prompt(tokenizer,{"messages":messages})


def run():
    import torch
    from peft import LoraConfig,get_peft_model
    from transformers import AutoModelForCausalLM,AutoTokenizer,GenerationConfig,__version__

    spec=plan()
    assert spec==read(HERE/"plan.json")
    hw=old.chair.device_receipt()
    assert hw["device"]=="cuda"
    OUT.mkdir()
    write(OUT/"launch.json",hw|{"host":socket.gethostname(),"pid":os.getpid(),"process_start":
        subprocess.check_output(["ps","-p",str(os.getpid()),"-o","lstart="],text=True).strip(),
        "command":[sys.executable,*sys.argv],"run_directory":str(OUT),
        "torch":torch.__version__,"transformers":__version__,"plan_sha256":pin(HERE/"plan.json"),
        "model_index_sha256":pin(MODEL/"model.safetensors.index.json")})
    torch.manual_seed(SEED)
    tokenizer=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    eos=tokenizer.convert_tokens_to_ids("<|im_end|>")
    backbone=AutoModelForCausalLM.from_pretrained(MODEL,local_files_only=True,
        dtype=torch.bfloat16,attn_implementation="sdpa",device_map={"":"cuda:0"}).eval()
    assert set(LAYERS)<=dict(backbone.named_modules()).keys()
    model=get_peft_model(backbone,LoraConfig(r=4,lora_alpha=8,lora_dropout=0.,
                         target_modules=list(LAYERS),task_type="CAUSAL_LM")).eval()
    learn={k:p for k,p in model.named_parameters() if p.requires_grad}
    assert len(learn)==8 and all(".lora_" in x for x in learn)
    frozen=[(p,p._version) for p in model.parameters() if not p.requires_grad]
    at_start={k:p.detach().clone() for k,p in learn.items()}
    config=GenerationConfig(max_new_tokens=old.BUDGET,do_sample=False,eos_token_id=eos,
                            pad_token_id=tokenizer.pad_token_id,use_cache=True)

    def generate(mode):
        with (OUT/f"{mode}.jsonl").open("w") as file,torch.inference_mode():
            for key,row in spec["held"].items():
                ids=encode(tokenizer,row["messages"])
                x=torch.tensor([ids],device="cuda:0")
                gen=model.generate(input_ids=x,attention_mask=torch.ones_like(x),generation_config=config)
                output=gen[0,len(ids):].tolist()
                reply={"text":tokenizer.decode(output,skip_special_tokens=True).strip(),
                       "termination":"complete" if output[-1]==eos else "cap",
                       "input_tokens":len(ids),"output_tokens":len(output)}
                old.chair.append(file,{"id":key,"input_ids":ids,"output_ids":output,"reply":reply})

    with model.disable_adapter():
        generate("frozen")
    train=[]
    for row in spec["training"]:
        prompt=encode(tokenizer,[{"role":"system","content":spec["system"]},
            {"role":"user","content":json.dumps(row["payload"],ensure_ascii=False)}])
        suffix=tokenizer.encode(row["target"],add_special_tokens=False)+[eos]
        assert tokenizer.decode(suffix,skip_special_tokens=True).strip()==row["target"]
        train.append((row["id"],prompt,suffix))
    rng=torch.Generator().manual_seed(SEED)
    opt=torch.optim.AdamW(learn.values(),lr=LR,weight_decay=0.)
    step=0
    with (OUT/"updates.jsonl").open("w") as file:
        for _ in range(EPOCHS):
            for index in torch.randperm(len(train),generator=rng).tolist():
                key,prefix,suffix=train[index]
                seq=torch.tensor([prefix+suffix[:-1]],device="cuda:0")
                target=torch.tensor(suffix,device="cuda:0")
                logits=model(input_ids=seq,attention_mask=torch.ones_like(seq),use_cache=False,
                             logits_to_keep=len(suffix)).logits[0].float()
                assert logits.shape[0]==len(suffix)
                loss=torch.nn.functional.cross_entropy(logits,target)
                opt.zero_grad()
                loss.backward()
                grad={k:float(p.grad.norm()) for k,p in learn.items()}
                assert all(torch.isfinite(p.grad).all() for p in learn.values()) and max(grad.values())>0
                opt.step()
                step+=1
                old.chair.append(file,{"step":step,"case":key,"loss":float(loss.detach()),"gradients":grad,
                        "prompt_ids":prefix,"target_ids":suffix})
    assert all(p._version==v for p,v in frozen)
    changes={k:float((p-at_start[k]).detach().norm()) for k,p in learn.items()}
    assert all(x>0 for x in changes.values())
    probe=torch.tensor([encode(tokenizer,next(iter(spec["held"].values()))["messages"])],device="cuda:0")

    def logits_probe():
        with torch.inference_mode():
            return model(input_ids=probe,use_cache=False,logits_to_keep=1).logits.detach().cpu()

    expected=logits_probe()
    model.save_pretrained(OUT/"adapter",safe_serialization=True)
    model.load_adapter(str(OUT/"adapter"),adapter_name="replay")
    model.set_adapter("replay")
    torch.testing.assert_close(logits_probe(),expected,rtol=0,atol=0)
    generate("adapted")
    files=sorted(f for f in OUT.rglob("*") if f.is_file())
    write(OUT/"complete.json",{"updates":step,"frozen_versions_verified":True,
          "reloaded_logits_exact":True,"parameter_deltas":changes,
          "sha256":{str(f.relative_to(OUT)):pin(f) for f in files}})


def verify():
    from transformers import AutoTokenizer

    spec=plan()
    assert spec==read(HERE/"plan.json")
    receipt=read(OUT/"complete.json")
    assert receipt["updates"]==EPOCHS*len(spec["training"])
    assert all(pin(OUT/k)==v for k,v in receipt["sha256"].items())
    launch=read(OUT/"launch.json")
    assert launch["plan_sha256"]==pin(HERE/"plan.json")
    assert launch["model_index_sha256"]==spec["checkpoint_index_sha256"]
    tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    eos=tok.convert_tokens_to_ids("<|im_end|>")
    groups={}
    for mode in ("frozen","adapted"):
        rows=[json.loads(line) for line in (OUT/f"{mode}.jsonl").read_text().splitlines()]
        groups[mode]={}
        for (name,request),row in zip(spec["held"].items(),rows,strict=True):
            assert name==row["id"] and row["input_ids"]==encode(tok,request["messages"])
            ids=row["output_ids"]
            report=row["reply"]
            assert (len(ids),len(row["input_ids"]))==(report["output_tokens"],report["input_tokens"])
            assert bool(ids and ids[-1]==eos)==(report["termination"]=="complete")
            assert tok.decode(ids,skip_special_tokens=True).strip()==report["text"]
            groups[mode][name]=report
    return {"receipt":receipt,"outputs":groups}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","verify"))
    mode=p.parse_args().mode
    if mode=="run":
        run()
    else:
        print(json.dumps((plan if mode=="plan" else verify)(),ensure_ascii=False,indent=2))
