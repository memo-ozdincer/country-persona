"""Run frozen Qwen role replies on the paired live routing episode."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

from episode import CAP, episode, hashes, serialize


def main(model_path, output):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    launch = {"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
              "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
              "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
              "model":str(model_path.resolve()),"torch":torch.__version__,"transformers":transformers.__version__,
              "optimizer_updates":0,"sha256":hashes()}
    (output/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    tok = AutoTokenizer.from_pretrained(model_path,local_files_only=True,padding_side="left")
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,local_files_only=True,dtype=torch.bfloat16,attn_implementation="sdpa").eval()
    path = output/"transcript.jsonl"

    def generate(batch):
        ids = [tok.encode(tok.apply_chat_template(row["messages"],tokenize=False,add_generation_prompt=True,
                                                   enable_thinking=False),add_special_tokens=False) for row in batch]
        assert max(map(len,ids))+CAP<4096
        inputs = tok.pad({"input_ids":ids},return_tensors="pt")
        with torch.inference_mode():
            decoded = model.generate(**inputs,do_sample=False,max_new_tokens=CAP,
                                     eos_token_id=eos,pad_token_id=tok.pad_token_id)
        out = {}
        with path.open("a") as f:
            for row, prefix, tail in zip(batch,ids,decoded[:,inputs.input_ids.shape[-1]:].tolist(),strict=True):
                if eos in tail:
                    tail = tail[:tail.index(eos)+1]
                text = tok.decode(tail,skip_special_tokens=True).strip()
                record = {**row,"input_ids":prefix,"output_ids":tail,"output":text,"ended":tail[-1]==eos}
                out[row["id"]] = record
                f.write(serialize(record)+"\n")
        print(f"Saved {len(out)} new replies",flush=True)
        return out

    result = episode(generate)
    (output/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    (output/"complete.json").write_text(serialize({"records":result["records"],
          "transcript_sha256":sha256(path.read_bytes()).hexdigest(),"optimizer_updates":0})+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    main(args.model,args.output)
