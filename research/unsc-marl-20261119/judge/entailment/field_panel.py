"""Compare field-first mandate extraction on the same package calibration cards."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import package_panel as panel

HERE = Path(__file__).resolve().parent
from project_rule import SCHEMAS

SYSTEM = ("Read only the supplied private mandate. Find the explicit restriction for this one field. "
          "When the field is unrestricted or not mentioned, choose No restriction on this field. "
          "If the mandate requires a single value, choose that value. "
          "Ignore conditions on all other fields. Respond with just the letter of the correct answer.")


def suite():
    for family, _, item in panel.inputs():
        for index, card in enumerate(item["cards"]):
            for field, definitions in SCHEMAS[family].items():
                order = [None, *definitions]
                labels = "ABCD"[:len(order)]
                for reverse in (False, True):
                    values = list(reversed(order)) if reverse else order
                    options = {
                        label: ("No restriction on this field." if value is None else definitions[value])
                        for label, value in zip(labels, values, strict=True)
                    }
                    body={"private_mandate":card["prose"],"field":field,"answers":options}
                    yield {"id":f"{family}/{index}/{field}/{int(reverse)}","values":values,
                           "labels":labels,
                           "messages":[{"role":"system","content":SYSTEM},
                                       {"role":"user","content":panel.codec(body)}]}


def score(rows):
    decisions = {}
    for plan in suite():
        row = rows[plan["id"]]
        pair = decisions.setdefault(plan["id"].rsplit("/",1)[0], [])
        logits = row["label_logits"]
        assert len(logits)==len(plan["values"])
        best = max(logits)
        choices = [v for v,m in zip(plan["values"],logits,strict=True) if m==best]
        pair.append({"unique":len(choices)==1,"value":choices[0] if len(choices)==1 else None})
    scores, field_count, exact_fields = {}, 0, 0
    for family, case, item in panel.inputs():
        for index, card in enumerate(item["cards"]):
            parsed={}
            available=True
            for field in SCHEMAS[family]:
                pair = decisions[f"{family}/{index}/{field}"]
                stable = pair[0]["unique"] and pair[1]["unique"] and pair[0]["value"]==pair[1]["value"]
                if not stable:
                    available=False
                else:
                    value=pair[0]["value"]
                    if value is not None:
                        parsed[field]=value
                    exact_fields += value==card["expected"].get(field)
                field_count += 1
            for option in case["options"]:
                accept=all(option[k]==v for k,v in parsed.items()) if available else None
                scores[f"{family}/{index}/{option['id']}"]={"accept":accept}
    result=panel.evaluate(scores)
    result["field_decisions"]=decisions
    result["totals"].update({"exact_fields":exact_fields,"fields":field_count})
    return result


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main(model_path, output):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM,AutoTokenizer

    output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    repo=(*panel.dependencies(),HERE/"field_panel.py",panel.PROSE/"project_rule.py")
    launch={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
            "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
            "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
            "model":str(model_path.resolve()),"torch":torch.__version__,"transformers":transformers.__version__,
            "optimizer_updates":0,"sha256":{str(p):digest(p) for p in repo}}
    (output/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    tokenizer=AutoTokenizer.from_pretrained(model_path,local_files_only=True,padding_side="left")
    choices=[tokenizer.encode(k,add_special_tokens=False) for k in "ABCD"]
    assert all(len(x)==1 for x in choices)
    choices=[x[0] for x in choices]
    assert len(set(choices))==4
    model=AutoModelForCausalLM.from_pretrained(model_path,local_files_only=True,dtype=torch.bfloat16,
                                               attn_implementation="sdpa").eval()
    planned=list(suite())
    records={}
    trace=output/"predictions.jsonl"
    with trace.open("x") as f:
        for start in range(0,len(planned),8):
            batch=planned[start:start+8]
            inputs=[tokenizer.encode(tokenizer.apply_chat_template(
                row["messages"],tokenize=False,add_generation_prompt=True,enable_thinking=False),
                add_special_tokens=False) for row in batch]
            encoded=tokenizer.pad({"input_ids":inputs},return_tensors="pt")
            with torch.inference_mode():
                output_logits=model(**encoded,logits_to_keep=1).logits[:,0,choices].float().tolist()
            for template, prompt, logits in zip(batch,inputs,output_logits,strict=True):
                size=len(template["labels"])
                row={**template,"input_ids":prompt,"label_ids":choices[:size],"label_logits":logits[:size]}
                records[row["id"]]=row
                f.write(panel.codec(row)+"\n")
            print(f"Recorded {len(records)} predictions",flush=True)
    result=score(records)
    (output/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    (output/"complete.json").write_text(panel.codec({"records":len(records),"sha256":digest(trace)})+"\n")
    print(result["totals"],flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    main(a.model,a.output)
