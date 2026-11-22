"""Capture frozen Qwen features and logits for the locked action-policy roster."""
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

import environment as env

MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
HERE = env.HERE


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run(directory):
    gpu = os.environ["CUDA_VISIBLE_DEVICES"]
    assert gpu.startswith("GPU-") and "," not in gpu
    query = ["nvidia-smi", "-i", gpu]
    name, device, used = (s.strip() for s in subprocess.check_output(
        [*query, "--query-gpu=name,uuid,memory.used", "--format=csv,noheader,nounits"], text=True).strip().split(","))
    assert device == gpu and int(used) == 0
    assert not subprocess.check_output(
        [*query, "--query-compute-apps=pid", "--format=csv,noheader"], text=True).strip()
    roster = env.E.read(HERE / "roster.json")
    assert roster == env.roster()
    directory.mkdir()
    pins = (Path(__file__), HERE / "roster.json", HERE / "environment.py", HERE / "protocol.md", env.E.HERE / "release.json")
    launch = {
        "host": socket.gethostname(), "gpu_name": name, "gpu_uuid": gpu, "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "run_directory": str(directory.resolve()), "command": [sys.executable, *sys.argv],
        "model": str(MODEL), "torch": torch.__version__, "transformers": __version__,
        "frozen_model_updates": 0, "dtype": "bfloat16", "attention": "sdpa",
        "sha256": {path.name: digest(path) for path in pins},
    }
    (directory / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa",
        device_map={"": "cuda:0"}).eval()
    actions = {label: tokenizer.encode(label, add_special_tokens=False) for label in (*env.RESPONSES, *env.DECISIONS)}
    assert all(len(x) == 1 for x in actions.values()) and len({x[0] for x in actions.values()}) == len(actions)
    items = []
    for split, rows in roster.items():
        for row in rows:
            if split == "archived":
                items.append((split, row["id"], "archived", row["chair"], env.DECISIONS))
                continue
            items.append((split, row["id"], "responder", row["responder"], env.RESPONSES))
            items.extend((split, row["id"], label, msgs, env.DECISIONS)
                         for label, msgs in zip(env.RESPONSES, row["chair"], strict=True))
    output = {}
    traces = []
    for start in range(0, len(items), 8):
        group = items[start:start + 8]
        ids = [tokenizer.encode(tokenizer.apply_chat_template(msgs, tokenize=False,
            add_generation_prompt=True, enable_thinking=False), add_special_tokens=False)
            for _, _, _, msgs, _ in group]
        inputs = tokenizer.pad({"input_ids": ids}, return_tensors="pt").to("cuda:0")
        # Match the unpadded positions for the explicit decoder call.
        positions = (inputs["attention_mask"].cumsum(-1) - 1).clamp_min(0)
        with torch.inference_mode():
            hidden = model.model(**inputs, position_ids=positions, use_cache=False).last_hidden_state[:, -1]
            logits = model.lm_head(hidden).float()
        for i, (split, key, stage, _, labels) in enumerate(group):
            name = f"{split}/{key}/{stage}"
            selected = logits[i, [actions[label][0] for label in labels]].cpu().numpy()
            output[name + "/hidden"] = hidden[i].float().cpu().numpy()
            output[name + "/logits"] = selected
            traces.append({"id": name, "input_ids": ids[i], "action_ids": {v: actions[v][0] for v in labels},
                           "restricted_logits": selected.tolist()})
    np.savez_compressed(directory / "features.npz", **output)
    (directory / "trace.jsonl").write_text("".join(json.dumps(t) + "\n" for t in traces))
    (directory / "complete.json").write_text(json.dumps({p.name: digest(p) for p in directory.iterdir()}, indent=2) + "\n")
    print(f"{len(traces)} prompts encoded")


if __name__ == "__main__":
    run(Path(sys.argv[1]))
