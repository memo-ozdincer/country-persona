"""Fit a small native Qwen LoRA directly on the restricted team reward."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, __version__

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import capture
import cases

E, MODEL = cases.E, capture.MODEL
SEED = 117443
BATCH = 12
LR = .0002
TRUST = .02
MODULES = tuple(f"model.layers.{layer}.self_attn.{projection}"
                for layer in (27, 31) for projection in ("q_proj", "v_proj"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def input_batch(tokenizer, ids):
    batch = tokenizer.pad({"input_ids": ids}, return_tensors="pt").to("cuda:0")
    position = (batch["attention_mask"].cumsum(-1)-1).clamp_min(0)
    return batch | {"position_ids": position, "use_cache": False, "logits_to_keep": 1}


def scores(model, tokenizer, ids, actions):
    return model(**input_batch(tokenizer, ids)).logits[:, -1, actions].float()


def freeze_identity():
    gpu = os.environ["CUDA_VISIBLE_DEVICES"]
    assert gpu.startswith("GPU-") and "," not in gpu
    query = ["nvidia-smi", "-i", gpu]
    fields = subprocess.check_output([*query, "--query-gpu=name,uuid,memory.used", "--format=csv,noheader,nounits"],
                                     text=True).strip()
    name, uuid, mem = (v.strip() for v in fields.split(","))
    assert uuid == gpu and int(mem) == 0
    assert not subprocess.check_output([*query, "--query-compute-apps=pid", "--format=csv,noheader"], text=True).strip()
    return name, uuid


def capture_vectors(model, tokenizer, rows, index, actions):
    with torch.inference_mode():
        data = [scores(model, tokenizer, [rows[j]["tokens"] for j in index[i:i+BATCH]], actions).cpu()
                for i in range(0, len(index), BATCH)]
    return torch.cat(data)


def fit(directory):
    name, uuid = freeze_identity()
    roster = E.read(HERE.parent / "roster.json")
    assert roster == cases.roster()
    directory.mkdir()
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, padding_side="left")
    actions = [tokenizer.encode(k, add_special_tokens=False) for k in cases.DEC]
    assert all(len(x) == 1 for x in actions) and len({x[0] for x in actions}) == 3
    actions = [x[0] for x in actions]
    table = [{"id": f'{split}/{row["id"]}', "tokens": capture.encode(tokenizer, row["messages"]),
              "utility": row["utility"]} for split, data in roster.items() for row in data]
    n = len(roster["train"])
    assert (n, len(table)) == (144, 188)
    order = torch.randperm(n, generator=torch.Generator().manual_seed(SEED)).tolist()
    indices = [order[i:i+BATCH] for i in range(0, n, BATCH)]
    pins = (Path(__file__), HERE / "protocol.md", HERE.parent / "roster.json", E.HERE / "release.json")
    manifest = {"host": socket.gethostname(), "gpu_uuid": uuid, "gpu_name": name, "pid": os.getpid(),
                "process_start": subprocess.check_output(["ps", "-p", str(os.getpid()), "-o", "lstart="],
                                                         text=True).strip(),
                "command": [sys.executable, *sys.argv], "directory": str(directory.resolve()),
                "model_path": str(MODEL), "model_index_sha256": digest(MODEL / "model.safetensors.index.json"),
                "transformers": __version__, "torch": torch.__version__, "dtype": "bfloat16",
                "attention": "sdpa", "seed": SEED, "learning_rate": LR, "kl_weight": TRUST,
                "planned_updates": len(indices), "sha256": {file.name: digest(file) for file in pins}}
    (directory / "launch.json").write_text(json.dumps(manifest, indent=2) + "\n")
    torch.manual_seed(SEED)
    original = AutoModelForCausalLM.from_pretrained(MODEL, local_files_only=True,
        dtype=torch.bfloat16, attn_implementation="sdpa", device_map={"": "cuda:0"}).eval()
    assert set(MODULES) <= dict(original.named_modules()).keys()
    model = get_peft_model(original, LoraConfig(r=4, lora_alpha=8, lora_dropout=0.,
                                               target_modules=list(MODULES), task_type="CAUSAL_LM"))
    model.eval()
    learners = {k: p for k,p in model.named_parameters() if p.requires_grad}
    assert len(learners) == 8 and all(".lora_" in key for key in learners)
    assert all(p.dtype == torch.float32 for p in learners.values())
    frozen = [(p, p._version) for p in model.parameters() if not p.requires_grad]
    before = {key: val.detach().clone() for key, val in learners.items()}
    with model.disable_adapter():
        base = capture_vectors(model, tokenizer, table, list(range(len(table))), actions)
    baseline = capture_vectors(model, tokenizer, table, list(range(len(table))), actions)
    torch.testing.assert_close(baseline, base, atol=0, rtol=0)
    optimizer = torch.optim.AdamW(learners.values(), lr=LR, weight_decay=0.)
    with (directory / "updates.jsonl").open("w") as trace:
        for step, group in enumerate(indices, start=1):
            instructions = [table[j]["tokens"] for j in group]
            old_policy = base[group].to("cuda:0").log_softmax(-1)
            reward = torch.tensor([table[j]["utility"] for j in group], device="cuda:0")
            new_policy = scores(model, tokenizer, instructions, actions).log_softmax(-1)
            probabilities = new_policy.exp()
            utility = (probabilities * reward).sum(-1).mean()
            kl = (probabilities * (new_policy - old_policy)).sum(-1).mean()
            loss = -utility + TRUST * kl
            optimizer.zero_grad()
            loss.backward()
            gradients = {key: float(p.grad.norm()) for key, p in learners.items()}
            assert all(torch.isfinite(p.grad).all() for p in learners.values()) and max(gradients.values()) > 0.
            optimizer.step()
            row = {"step": step, "ids": [table[j]["id"] for j in group], "gradient_norms": gradients,
                   "utility": float(utility.detach()), "kl_to_frozen": float(kl.detach()), "loss": float(loss.detach())}
            trace.write(json.dumps(row) + "\n")
            trace.flush()
    assert all(p._version == version for p, version in frozen)
    changes = {k: float((p-before[k]).detach().norm()) for k,p in learners.items()}
    assert all(v > 0 for v in changes.values())
    after = capture_vectors(model, tokenizer, table, list(range(len(table))), actions)
    with model.disable_adapter():
        unchanged = capture_vectors(model, tokenizer, table, list(range(len(table))), actions)
    torch.testing.assert_close(unchanged, base, rtol=0, atol=0)
    model.save_pretrained(directory / "adapter", safe_serialization=True)
    model.load_adapter(str(directory / "adapter"), adapter_name="replay")
    model.set_adapter("replay")
    model.eval()
    reloaded = capture_vectors(model, tokenizer, table, list(range(len(table))), actions)
    torch.testing.assert_close(reloaded, after, rtol=0, atol=0)
    with (directory / "scores.jsonl").open("w") as log:
        for row, b, adapted in zip(table, base.tolist(), after.tolist(), strict=True):
            log.write(json.dumps(row | {"frozen": b, "adapted": adapted, "action_ids": actions}) + "\n")
    files = sorted(f for f in directory.rglob("*") if f.is_file())
    (directory / "complete.json").write_text(json.dumps({
        "actual_updates": len(indices), "frozen_parameters_replayed_exactly": True,
        "disk_adapter_reload_exact": True,
        "adapter_elements": sum(p.numel() for p in learners.values()),
        "updated_tensor_norms": changes,
        "sha256": {str(f.relative_to(directory)): digest(f) for f in files}}, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    fit(p.parse_args().directory)
