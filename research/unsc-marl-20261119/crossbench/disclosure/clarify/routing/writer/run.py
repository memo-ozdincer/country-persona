"""Paired frozen model decision records from public sanctions workshop evidence."""
import argparse
import json
from hashlib import sha256
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CAP = 200
WORDS = 140
HEADINGS = ("History", "Workshop", "Evidence", "Positions", "Authority")
SYSTEM = (
    "You are drafting a decision record for an evaluation of a fictional post-vote UN workshop. "
    "Use only the public historical record and the public workshop evidence supplied. "
    "A workshop compatibility result does not change the real resolution or establish a future vote."
)
TASK = (
    "Write at most 140 words over exactly five lines with headings History:, Workshop:, Evidence:, Positions:, Authority:. "
    "History gives the official draft, adopted resolution, tally, India and Brazil's votes, and India's recorded concern. "
    "Workshop begins with AGREEMENT_POSSIBLE plus option ID, IMPASSE, or UNRESOLVED, exactly as the checked record supports. "
    "Evidence explains the disposition. For agreement, identify the shared package's three fields. "
    "For impasse, state the coverage of exclusions. For unresolved, identify each still unresolved option and what evidence is missing. "
    "Positions gives one relevant, correctly attributed signed claim per workshop role, with its claim ID. "
    "Treat each disclosure as scoped to its particular option. Authority identifies the status of the workshop proposals and what has been authorized."
)


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def sources():
    return (HERE / "run.py", ROOT / "sanctions.json", ROOT / "evidence/sanctions.json")


def suite():
    _, scenario_path, evidence_path = sources()
    scenario, evidence = (json.loads(path.read_text()) for path in (scenario_path, evidence_path))
    assert evidence["scenario_sha256"] == digest(scenario_path)
    pairs = {}
    traces = evidence["replays"]
    for data in traces:
        key = (data["variant"], "".join(data["opening"]))
        pairs.setdefault(key,{})[data["arm"]] = data
    contrasts = [(key, arms) for key, arms in pairs.items()
                 if arms["script"]["readout"]["state"] != arms["guarded"]["readout"]["state"]]
    assert len(contrasts) == 2 and all(k[0] == "impasse" for k, _ in contrasts)
    control = pairs["overlap","BC"]
    assert {k:v for k,v in control["script"].items() if k != "arm"} == {
        k:v for k,v in control["guarded"].items() if k != "arm"}
    chosen = [(key, arm, data) for key, arms in contrasts for arm, data in arms.items()]
    chosen.append((("overlap","BC"), "shared", control["script"]))
    for (variant, opening), arm, data in chosen:
        public = {"scope":scenario["boundary"], "history":scenario["historical"], "roles":scenario["roles"],
                  "packages":scenario["options"], "admitted_disclosures":data["public_claims"],
                  "checked_public_evidence":data["readout"], "task":TASK}
        yield {"id":f"{variant}-{opening}-{arm}","cap":CAP, "expected_state":data["readout"]["state"],
               "messages":[{"role":"system","content":SYSTEM},
                           {"role":"user","content":json.dumps(public,ensure_ascii=False,separators=(",",":"))}]}


def main(model_path, output):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    model_path = model_path.resolve()
    launch = {"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
              "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
              "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
              "model":str(model_path),"torch":torch.__version__,"transformers":transformers.__version__,
              "updates":0, "sources":{str(p.relative_to(ROOT)):digest(p) for p in sources()}}
    (output/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    tok = AutoTokenizer.from_pretrained(model_path,local_files_only=True,padding_side="left")
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,local_files_only=True,dtype=torch.bfloat16,attn_implementation="sdpa").eval()
    batch = list(suite())
    ids = [tok.encode(tok.apply_chat_template(r["messages"],tokenize=False,add_generation_prompt=True,
                                               enable_thinking=False),add_special_tokens=False) for r in batch]
    assert max(map(len,ids))+CAP<4096
    encoded = tok.pad({"input_ids":ids},return_tensors="pt")
    start = time.monotonic()
    with torch.inference_mode():
        predictions = model.generate(**encoded,do_sample=False,max_new_tokens=CAP,
                                     eos_token_id=eos,pad_token_id=tok.pad_token_id)
    transcript = output/"transcript.jsonl"
    with transcript.open("x") as out:
        for row, prefix, tail in zip(batch,ids,predictions[:,encoded.input_ids.shape[-1]:].tolist(),strict=True):
            if eos in tail:
                tail = tail[:tail.index(eos)+1]
            text = tok.decode(tail,skip_special_tokens=True).strip()
            out.write(json.dumps({**row,"input_ids":prefix,"output_ids":tail,"output":text,
                                  "stop":"eos" if tail[-1]==eos else "cap"},ensure_ascii=False)+"\n")
    result = {"records":len(batch),"seconds":round(time.monotonic()-start,2),
              "sha256":digest(transcript),"updates":0}
    (output/"complete.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model",type=Path)
    parser.add_argument("output",type=Path)
    args = parser.parse_args()
    main(args.model,args.output)
