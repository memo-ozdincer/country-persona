"""Generate optional native comparisons from the received documents only."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RUNS = PARENT.parent
RELEASE = RUNS.parent/"benchmark-v1.5"


def load(name,path):
    spec=spec_from_file_location(name,path)
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture = load("afghanistan_authority_exact",PARENT/"replay.py")
collector = load("afghanistan_authority_native_writer",RUNS/"syria-baseline/collect.py")
OUT = HERE/"evidence"
SYSTEM = (
    "Write only an optional comparison for a factual UN decision record. Compare the "
    "delivered national statement with the delivered clause of the adopted text. Use "
    "only those two supplied items. Separate what the speaker supported or expected from "
    "what the Council requested, required or preserved. If either item is missing, or "
    "the two items do not support a specific useful comparison, return exactly NONE. "
    "Otherwise return one or two sentences, at most 42 words, with the actor and provision "
    "stated precisely. End there."
)


def plan():
    requests, receipts = {},{}
    for early,late in product((0,1,None),repeat=2):
        ids=[fixture.OPTIONS[i][x] if x is not None else None for i,x in enumerate((early,late))]
        payload=json.dumps({slot:fixture.BLOCKS[key]["text"] if key else None
                            for slot,key in zip(("delivered_national_statement","delivered_adopted_clause"),
                                                ids,strict=True)},ensure_ascii=False)
        key="comparison-"+fixture.sha256(payload.encode()).hexdigest()[:16]
        requests[key]={"request":{"id":key,"max_output_tokens":120,
            "messages":[{"role":"system","content":SYSTEM},{"role":"user","content":payload}]},
            "receipts":ids}
        receipts[f"{early}/{late}"]=key
    paths=(Path(__file__),HERE/"protocol.md",PARENT/"case.json",PARENT/"results.json",
           PARENT/"text-decoder/scores.json",PARENT/"text-decoder/lexical-contrast/scores.json",
           Path(collector.__file__),RELEASE/"release.json")
    return {"requests":dict(sorted(requests.items())),"receipt_keys":receipts,
            "checkpoint_index_sha256":fixture.pin(collector.MODEL/"model.safetensors.index.json"),
            "sha256":{str(p.relative_to(RUNS.parent)):fixture.pin(p) for p in paths}}


def locked():
    record=plan()
    assert json.loads((HERE/"plan.json").read_text())==record
    return record


def run():
    record=locked()
    gpu=os.environ["CUDA_VISIBLE_DEVICES"]
    values=subprocess.check_output(["nvidia-smi","-i",gpu,"--query-gpu=memory.used,utilization.gpu",
                                    "--format=csv,noheader,nounits"],text=True).strip()
    assert values=="0, 0"

    def collect(generate,directory):
        for key,row in record["requests"].items():
            collector.suite.append(directory/"calls.jsonl",{"id":key,"reply":generate(row["request"])})

    with patch.object(collector,"roster",return_value={fixture.CASE["id"]:fixture.CASE}),patch.object(
        collector,"HERE",HERE),patch.object(collector.suite.e,"HERE",RELEASE),patch.object(
        collector.suite,"collect",collect):
        collector.run(OUT)


def verify():
    from transformers import AutoTokenizer

    record=locked()
    manifest=json.loads((OUT/"complete.json").read_text())
    assert set(manifest)=={"launch.json","tokens.jsonl","calls.jsonl"}
    assert all(fixture.pin(OUT/k)==v for k,v in manifest.items())
    launch=json.loads((OUT/"launch.json").read_text())
    assert launch["checkpoint_index_sha256"]==record["checkpoint_index_sha256"]
    assert launch["gpu_name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["optimizer_updates"]==0 and launch["release_sha256"]==fixture.pin(RELEASE/"release.json")
    tokenizer=AutoTokenizer.from_pretrained(collector.MODEL,local_files_only=True)
    eos=tokenizer.convert_tokens_to_ids("<|im_end|>")
    trace,calls=([json.loads(line) for line in (OUT/name).read_text().splitlines()]
                 for name in ("tokens.jsonl","calls.jsonl"))
    output={}
    for (key,row),t,call in zip(record["requests"].items(),trace,calls,strict=True):
        assert key==call["id"] and t["response"]==call["reply"]
        assert t["input_ids"]==collector.prompt(tokenizer,row["request"])
        response=call["reply"]
        assert len(t["input_ids"])==response["input_tokens"]
        assert len(t["output_ids"])==response["output_tokens"]<=120
        assert tokenizer.decode(t["output_ids"],skip_special_tokens=True).strip()==response["text"]
        assert bool(t["output_ids"] and t["output_ids"][-1]==eos)==(response["termination"]=="complete")
        output[key]={"reply":response,"receipts":row["receipts"]}
    return {"outputs":output,"manifest":manifest}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","verify"))
    mode=parser.parse_args().mode
    if mode=="run":
        run()
    else:
        print(json.dumps({"plan":plan,"verify":verify}[mode](),ensure_ascii=False,indent=2))
