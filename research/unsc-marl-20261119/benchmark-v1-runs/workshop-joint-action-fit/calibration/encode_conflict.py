"""Capture the fixed Qwen representation of the matched conflict prompts."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, __version__

import conflict_roster
import encode

HERE = conflict_roster.HERE
E = conflict_roster.E
env = conflict_roster.env


def run(out):
    gpu = os.environ["CUDA_VISIBLE_DEVICES"]
    assert gpu.startswith("GPU-") and "," not in gpu
    query = ["nvidia-smi", "-i", gpu]
    name, uuid, used = (field.strip() for field in subprocess.check_output(
        [*query, "--query-gpu=name,uuid,memory.used", "--format=csv,noheader,nounits"], text=True).strip().split(","))
    assert uuid == gpu and int(used) == 0
    assert not subprocess.check_output([*query, "--query-compute-apps=pid", "--format=csv,noheader"], text=True).strip()
    out.mkdir()
    roster_path = HERE / "conflict-roster.json"
    cases = E.read(roster_path)
    assert cases == conflict_roster.run()
    files = (Path(__file__), HERE / "conflict_roster.py", roster_path, HERE / "visible-conflict-protocol.md")
    launch = {"host": socket.gethostname(), "gpu_name": name, "gpu_uuid": uuid, "pid": os.getpid(),
              "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                       text=True).strip(),
              "command": [sys.executable, *sys.argv], "run_directory": str(out.resolve()),
              "model": str(encode.MODEL), "torch": torch.__version__, "transformers": __version__,
              "dtype": "bfloat16", "attention": "sdpa", "backbone_updates": 0,
              "sha256": {p.name: encode.digest(p) for p in files}}
    (out / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    tokenizer = AutoTokenizer.from_pretrained(encode.MODEL, local_files_only=True, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(encode.MODEL, local_files_only=True, dtype=torch.bfloat16,
                                                attn_implementation="sdpa", device_map={"": "cuda:0"}).eval()
    action_ids = [tokenizer.encode(t, add_special_tokens=False) for t in env.DECISIONS]
    assert all(len(ids) == 1 for ids in action_ids)
    action_ids = [ids[0] for ids in action_ids]
    rows = [(f'{split}/{row["id"]}', row["messages"]) for split, items in cases.items() for row in items]
    traces, arrays = [], {}
    for start in range(0, len(rows), 8):
        subset = rows[start:start+8]
        tokens = [tokenizer.encode(tokenizer.apply_chat_template(
            m, tokenize=False, add_generation_prompt=True, enable_thinking=False), add_special_tokens=False)
            for _, m in subset]
        inputs = tokenizer.pad({"input_ids": tokens}, return_tensors="pt").to("cuda:0")
        positions = (inputs["attention_mask"].cumsum(-1) - 1).clamp_min(0)
        with torch.inference_mode():
            h = model.model(**inputs, position_ids=positions, use_cache=False).last_hidden_state[:, -1]
            z = model.lm_head(h).float()[:, action_ids]
        for i, (name, _) in enumerate(subset):
            arrays[name + "/hidden"] = h[i].float().cpu().numpy()
            arrays[name + "/logits"] = z[i].cpu().numpy()
            traces.append({"id": name, "input_ids": tokens[i], "action_ids": action_ids,
                           "restricted_logits": arrays[name + "/logits"].tolist()})
    np.savez_compressed(out / "features.npz", **arrays)
    (out / "trace.jsonl").write_text("".join(json.dumps(row) + "\n" for row in traces))
    (out / "complete.json").write_text(json.dumps({p.name: encode.digest(p) for p in sorted(out.iterdir())}, indent=2) + "\n")


if __name__ == "__main__":
    run(Path(sys.argv[1]))
