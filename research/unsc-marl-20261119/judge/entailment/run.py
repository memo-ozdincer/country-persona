"""Score quote entailment under both response-code orders with a frozen judge."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PANEL = HERE/"panel.json"
SYSTEM = ("You judge whether a candidate claim follows from the exact quoted evidence. "
          "Read only the supplied evidence and candidate. Do not reward a related topic or an exact quote by itself. "
          "A claim must preserve the actor, modality, agency, quantifier and restriction. "
          "An allowance of either option does not require one of them. Choose the code whose meaning is correct. "
          "Respond with a single letter A or B.")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def suite():
    panel = json.loads(PANEL.read_text())
    for pair in panel["pairs"]:
        assert pair["quote"] in pair["source"]
        for claim_kind,supported in (("supported",True),("foil",False)):
            for invert in (False,True):
                codes = dict(zip(("A","B"),(
                    "The quote does not establish the claim.","The quote establishes the entire claim."
                ) if invert else (
                    "The quote establishes the entire claim.","The quote does not establish the claim."
                ),strict=True))
                payload = {"source":pair["source"],"highlighted_quote":pair["quote"],
                           "candidate_claim":pair[claim_kind],"decision_codes":codes}
                yield {"id":f"{pair['id']}/{claim_kind}/{int(invert)}","supports":supported,
                       "support_code":"B" if invert else "A",
                       "messages":[{"role":"system","content":SYSTEM},
                                   {"role":"user","content":json.dumps(payload,ensure_ascii=False,separators=(",",":"))}]}


def score(rows):
    panel = json.loads(PANEL.read_text())
    cases = {}
    order = Counter()
    for test in suite():
        row = rows[test["id"]]
        a,b = row["label_logits"]
        guess = "A" if a>b else "B" if b>a else None
        inferred = (guess==test["support_code"]) if guess else None
        order[(test["supports"],inferred)] += 1
        pair = test["id"].rsplit("/",1)[0]
        cases.setdefault(pair,[]).append(inferred)
    groups = {}
    for pair,both in cases.items():
        label = pair.endswith("/supported")
        output = both[0] if both[0] is not None and both[0]==both[1] else None
        groups[pair] = {"reference":label,"calls":both,"stable_prediction":output,
                        "correct":output==label}
    invalid = {r["id"]:{"contained":r["quote"] in r["source"],"judged":False}
               for r in panel["invalid_quotes"]}
    assert all(not v["contained"] for v in invalid.values())
    totals = {
        "calls":len(rows),"correct_calls":order[True,True]+order[False,False],
        "positive_supported":order[True,True],"positive_calls":sum(v for (gold,pred),v in order.items() if gold),
        "negative_rejected":order[False,False],"negative_calls":sum(v for (gold,pred),v in order.items() if not gold),
        "stable_correct":sum(v["correct"] for v in groups.values()),
        "stable_wrong":sum(not v["correct"] and v["stable_prediction"] is not None for v in groups.values()),
        "unstable":sum(v["stable_prediction"] is None for v in groups.values()),
        "invalid_quotes_rejected":len(invalid),
        "minimal_pairs_both_correct":sum(all(groups[f"{p['id']}/{key}"]["correct"] for key in ("supported","foil"))
                                         for p in panel["pairs"]),
    }
    return {"totals":totals,"cases":groups,"invalid_quotes":invalid}


def main(model_path,output):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM,AutoTokenizer

    output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    plan=list(suite())
    runtime={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
             "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
             "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
             "model":str(model_path.resolve()),"torch":torch.__version__,"transformers":transformers.__version__,
             "optimizer_updates":0,"sha256":{p.name:digest(p) for p in (HERE/"run.py",PANEL)}}
    (output/"launch.json").write_text(json.dumps(runtime,indent=2)+"\n")
    tok=AutoTokenizer.from_pretrained(model_path,local_files_only=True,padding_side="left")
    label_ids=[tok.encode(k,add_special_tokens=False) for k in ("A","B")]
    assert all(len(ids)==1 for ids in label_ids) and label_ids[0]!=label_ids[1]
    label_ids=[t[0] for t in label_ids]
    model=AutoModelForCausalLM.from_pretrained(model_path,local_files_only=True,dtype=torch.bfloat16,
                                               attn_implementation="sdpa").eval()
    found={}
    destination=output/"predictions.jsonl"
    with destination.open("x") as out:
        for start in range(0,len(plan),8):
            chunk=plan[start:start+8]
            encoded=[tok.encode(tok.apply_chat_template(p["messages"],tokenize=False,add_generation_prompt=True,
                                                        enable_thinking=False),add_special_tokens=False) for p in chunk]
            inputs=tok.pad({"input_ids":encoded},return_tensors="pt")
            with torch.inference_mode():
                logits=model(**inputs,logits_to_keep=1).logits[:,0,label_ids].float().tolist()
            for row,ids,pair in zip(chunk,encoded,logits,strict=True):
                result={**row,"input_ids":ids,"label_ids":label_ids,"label_logits":pair}
                found[row["id"]]=result
                out.write(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n")
            print(f"Recorded {len(found)} predictions",flush=True)
    report=score(found)
    (output/"metrics.json").write_text(json.dumps(report,indent=2)+"\n")
    (output/"complete.json").write_text(json.dumps({"records":len(found),"sha256":digest(destination)})+"\n")
    print(report["totals"],flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    main(a.model,a.output)
