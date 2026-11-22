"""Capture the frozen signed-action logits and state for all locked prompts."""
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, __version__

import cases

HERE = cases.HERE
MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")


def digest(file):
    return sha256(file.read_bytes()).hexdigest()


def encode(tokenizer, messages):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return tokenizer.encode(prompt, add_special_tokens=False)


def run(directory):
    gpu = os.environ["CUDA_VISIBLE_DEVICES"]
    assert gpu.startswith("GPU-") and "," not in gpu
    info = subprocess.check_output(["nvidia-smi", "-i", gpu, "--query-gpu=name,uuid,memory.used",
                                    "--format=csv,noheader,nounits"], text=True).strip()
    name, uuid, used = [x.strip() for x in info.split(",")]
    assert uuid == gpu and int(used) == 0
    assert not subprocess.check_output(["nvidia-smi", "-i", gpu, "--query-compute-apps=pid",
                                        "--format=csv,noheader"], text=True).strip()
    directory.mkdir()
    roster = cases.E.read(HERE / "roster.json")
    assert roster == cases.roster()
    files = (Path(__file__), HERE / "cases.py", HERE / "protocol.md", HERE / "roster.json", cases.E.HERE / "release.json")
    receipt = {"host": socket.gethostname(), "gpu_name": name, "gpu_uuid": uuid, "pid": os.getpid(),
               "process_start": subprocess.check_output(["ps", "-p", str(os.getpid()), "-o", "lstart="],
                                                        text=True).strip(),
               "command": [sys.executable, *sys.argv], "run_directory": str(directory.resolve()),
               "model": str(MODEL), "checkpoint_index_sha256": digest(MODEL / "model.safetensors.index.json"),
               "torch": torch.__version__, "transformers": __version__, "attention": "sdpa",
               "dtype": "bfloat16", "optimizer_updates": 0, "sha256": {p.name: digest(p) for p in files}}
    (directory / "launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, padding_side="left")
    actions = [tokenizer.encode(label, add_special_tokens=False) for label in cases.DEC]
    assert all(len(ids) == 1 for ids in actions) and len({ids[0] for ids in actions}) == len(actions)
    actions = [ids[0] for ids in actions]
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa",
        device_map={"":"cuda:0"}).eval()
    prompts = [(f'{split}/{row["id"]}', encode(tokenizer, row["messages"])) for split, rows in roster.items() for row in rows]
    hidden, logits, traces = [], [], []
    for i in range(0, len(prompts), 8):
        group = prompts[i:i+8]
        inputs = tokenizer.pad({"input_ids": [tokens for _, tokens in group]}, return_tensors="pt").to("cuda:0")
        positions = (inputs["attention_mask"].cumsum(-1)-1).clamp_min(0)
        with torch.inference_mode():
            reps = model.model(**inputs, position_ids=positions, use_cache=False).last_hidden_state[:, -1]
            scores = model.lm_head(reps).float()[:, actions]
        hidden.extend(reps.float().cpu().numpy())
        logits.extend(scores.cpu().numpy())
        traces.extend({"id": key, "input_ids": tokens, "action_ids": actions, "restricted_logits": row.tolist()}
                      for (key, tokens), row in zip(group, scores.cpu().numpy(), strict=True))
    np.savez_compressed(directory / "vectors.npz", hidden=np.stack(hidden), logits=np.stack(logits))
    (directory / "trace.jsonl").write_text("".join(json.dumps(r) + "\n" for r in traces))
    (directory / "complete.json").write_text(json.dumps({f.name: digest(f) for f in sorted(directory.iterdir())}, indent=2) + "\n")


if __name__ == "__main__":
    run(Path(sys.argv[1]))
