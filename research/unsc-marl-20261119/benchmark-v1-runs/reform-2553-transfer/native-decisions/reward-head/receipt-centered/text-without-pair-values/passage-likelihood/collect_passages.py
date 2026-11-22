"""Collect complete native passage likelihoods and verify the chosen sequences."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
import collect_masked as old

base,head=old.runtime.base,old.head
READ=head.READ
OUT=HERE/"evidence"
SYSTEM=old.SYSTEM.removesuffix("Return only one answer letter.")+(
    "Return exactly the complete wording of one supplied Peru passage, with no label or extra text."
)


def plan():
    rows=[]
    for req in old.locked()["requests"]:
        data=json.loads(req["messages"][1]["content"])
        mapping=data.pop("letter_to_your_card")
        menus=data.pop("your_menu")
        source={k:menus[k] for k in ("1","2")}
        data["available_passages"]=[{"passage":menus[card],"standalone_points":data["standalone_points"][data["your_desk"]][card]}
                                    for card in mapping.values()]
        rows.append({"req":{"id":req["id"],"max_output_tokens":64,"messages":[
            {"role":"system","content":SYSTEM},{"role":"user","content":json.dumps(data,ensure_ascii=False)}]},
                     "candidates":source})
    assert len(rows)==40
    pins=(Path(__file__),HERE/"protocol.md",PARENT/"plan.json",PARENT/"scores.json",Path(old.__file__),
          Path(base.__file__),old.runtime.prior.RELEASE/"release.json")
    return {"rows":rows,"checkpoint_index_sha256":head.prior.digest(base.MODEL/"model.safetensors.index.json"),
            "sha256":{str(p.relative_to(head.RUNS.parent)):head.prior.digest(p) for p in pins}}


def lock():
    value=plan()
    assert value==READ(HERE/"plan.json")
    return value


def run():
    import torch
    from transformers import AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    pinned=lock()
    gpu=os.environ["CUDA_VISIBLE_DEVICES"]
    measured=subprocess.check_output(["nvidia-smi","-i",gpu,"--query-gpu=memory.used,utilization.gpu",
                                      "--format=csv,noheader,nounits"],text=True).strip()
    assert measured=="0, 0"
    tok=AutoTokenizer.from_pretrained(base.MODEL,local_files_only=True)
    eos=tok.convert_tokens_to_ids("<|im_end|>")
    state={}

    def candidates(model,*_args,**kwargs):
        start=kwargs["input_ids"]
        assert start[0].tolist()==base.prompt(tok,state["row"]["req"])
        scores={}
        for key,body in state["row"]["candidates"].items():
            tokens=tok.encode(body,add_special_tokens=False)+[eos]
            assert 0<len(tokens)<=64 and tok.decode(tokens[:-1],skip_special_tokens=False)==body
            output=torch.tensor([tokens],dtype=start.dtype,device=start.device)
            x=torch.cat((start,output),dim=1)
            logits=model(input_ids=x,attention_mask=torch.ones_like(x),use_cache=False,
                         logits_to_keep=len(tokens)+1).logits[0,:-1].float()
            lps=torch.log_softmax(logits,dim=-1).gather(1,output.reshape(-1,1)).flatten().tolist()
            assert len(lps)==len(tokens)
            scores[key]={"text":body,"tokens":tokens,"token_log_probs":lps,"sum":sum(lps)}
        key=max(scores,key=lambda k:scores[k]["sum"])
        state["scores"]=scores
        state["chosen"]=key
        return torch.cat((start,torch.tensor([scores[key]["tokens"]],dtype=start.dtype,device=start.device)),dim=1)

    def collect(generate,directory):
        for row in pinned["rows"]:
            state["row"]=row
            response=generate(row["req"])
            old.head.prior.append(directory/"calls.jsonl",{"id":row["req"]["id"],
                "response":response,"scores":state.pop("scores"),"sum_choice":state.pop("chosen")})

    with patch.object(GenerationMixin,"generate",candidates),patch.object(
            base,"roster",return_value={old.held.CASE["id"]:old.held.CASE}),patch.object(
            base,"HERE",HERE),patch.object(base.suite,"collect",collect),patch.object(
            base.suite.e,"HERE",old.runtime.prior.RELEASE):
        base.run(OUT)


def verify():
    from math import isfinite
    from transformers import AutoTokenizer

    pinned=lock()
    manifest=READ(OUT/"complete.json")
    assert all(head.prior.digest(OUT/key)==value for key,value in manifest.items())
    launch=READ(OUT/"launch.json")
    assert launch["checkpoint_index_sha256"]==pinned["checkpoint_index_sha256"]
    assert launch["protocol_sha256"]==head.prior.digest(HERE/"protocol.md") and launch["optimizer_updates"]==0
    assert launch["gpu_name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
    tok=AutoTokenizer.from_pretrained(base.MODEL,local_files_only=True)
    eos=tok.convert_tokens_to_ids("<|im_end|>")
    calls,trace=([json.loads(line) for line in (OUT/name).read_text().splitlines()]
                 for name in ("calls.jsonl","tokens.jsonl"))
    rows={}
    for row,log,tokens in zip(pinned["rows"],calls,trace,strict=True):
        req=row["req"]
        assert req["id"]==log["id"] and tokens["input_ids"]==base.prompt(tok,req)
        assert log["response"]==tokens["response"] and len(tokens["input_ids"])==log["response"]["input_tokens"]
        scores=log["scores"]
        assert set(scores)==set(row["candidates"])
        for key,result in scores.items():
            text=row["candidates"][key]
            assert result["text"]==text and result["tokens"]==tok.encode(text,add_special_tokens=False)+[eos]
            assert len(result["token_log_probs"])==len(result["tokens"])
            assert all(isfinite(x) and x<=0 for x in result["token_log_probs"])
            assert sum(result["token_log_probs"])==result["sum"]
        chosen=max(scores,key=lambda k:scores[k]["sum"])
        assert log["sum_choice"]==chosen
        assert tokens["output_ids"]==scores[chosen]["tokens"] and log["response"]["termination"]=="complete"
        assert log["response"]["text"]==scores[chosen]["text"] and len(tokens["output_ids"])==log["response"]["output_tokens"]
        rows[req["id"]]={"input_tokens":log["response"]["input_tokens"],"scores":scores,"chosen":chosen}
    return {"rows":rows,"manifest":manifest}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","verify"))
    mode=parser.parse_args().mode
    if mode=="run":
        run()
    else:
        print(json.dumps({"plan":plan,"verify":verify}[mode](),ensure_ascii=False,indent=2))
