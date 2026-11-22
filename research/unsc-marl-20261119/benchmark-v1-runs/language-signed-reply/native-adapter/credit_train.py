"""Use exact reward-maximizing targets in the matched native LoRA fit."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, __version__

import train

E, HERE, MODEL = train.E, train.HERE, train.MODEL


def run(out):
    gpu, uid = train.freeze_identity()
    out.mkdir()
    source = E.read(HERE / "evidence/complete.json")
    spec = E.read(HERE.parent / "roster.json")
    assert spec == train.cases.roster()
    tokens = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, padding_side="left")
    action_ids = [tokens.encode(c, add_special_tokens=False)[0] for c in train.cases.DEC]
    raw = [(f'{split}/{r["id"]}', r) for split, rows in spec.items() for r in rows]
    table = [{"id": key, "tokens": train.capture.encode(tokens,r["messages"]),
              "utility": r["utility"]} for key,r in raw]
    n = len(spec["train"])
    order = torch.randperm(n, generator=torch.Generator().manual_seed(train.SEED)).tolist()
    trace_path = out / "updates.jsonl"
    previous = [json.loads(l) for l in (HERE / "evidence/updates.jsonl").read_text().splitlines()]
    assert [s for row in previous for s in row["ids"]] == [table[i]["id"] for i in order]
    counts = torch.tensor([r["utility"] for r in table[:n]]).argmax(-1).bincount(minlength=3)
    class_weight = (len(order) / (3*counts.float())).to("cuda:0")
    pins = (Path(__file__), HERE / "train.py", HERE / "credit-protocol.md", HERE / "evidence/complete.json",
            HERE.parent / "roster.json")
    launch = {"host": socket.gethostname(), "gpu_name": gpu, "gpu_uuid": uid, "pid": os.getpid(),
              "process_start": subprocess.check_output(
                  ["ps", "-p", str(os.getpid()), "-o", "lstart="], text=True).strip(),
              "command": [sys.executable, *sys.argv], "run_directory": str(out.resolve()),
              "model": str(MODEL), "torch": torch.__version__, "transformers": __version__,
              "dtype": "bfloat16", "attention": "sdpa", "seed": train.SEED,
              "lr": train.LR, "kl": train.TRUST, "class_counts": counts.tolist(),
              "sha256": {f.name: train.digest(f) for f in pins}}
    (out / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    torch.manual_seed(train.SEED)
    model = AutoModelForCausalLM.from_pretrained(MODEL, local_files_only=True, dtype=torch.bfloat16,
                                                attn_implementation="sdpa", device_map={"": "cuda:0"}).eval()
    assert set(train.MODULES) <= dict(model.named_modules()).keys()
    model = get_peft_model(model, LoraConfig(r=4, lora_alpha=8, lora_dropout=0.,
                                           target_modules=list(train.MODULES), task_type="CAUSAL_LM"))
    model.eval()
    learned = [p for p in model.parameters() if p.requires_grad]
    fixed = [(p,p._version) for p in model.parameters() if not p.requires_grad]
    assert len(learned) == 8 and sum(p.numel() for p in learned) == source["adapter_elements"]
    opt = torch.optim.AdamW(learned, lr=train.LR, weight_decay=0.)
    select = list(range(len(table)))
    with model.disable_adapter():
        baseline = train.capture_vectors(model, tokens, table, select, action_ids)
    prior = [json.loads(l) for l in (HERE / "evidence/scores.jsonl").read_text().splitlines()]
    assert baseline.tolist() == [r["frozen"] for r in prior]
    with trace_path.open("w") as log:
        for i in range(0, n, train.BATCH):
            group = order[i:i+train.BATCH]
            native = train.scores(model, tokens, [table[k]["tokens"] for k in group], action_ids)
            distribution = native.log_softmax(-1)
            frozen = baseline[group].to("cuda:0").log_softmax(-1)
            reward = torch.tensor([table[k]["utility"] for k in group], device="cuda:0")
            label = reward.argmax(-1)
            nll = -(distribution.gather(1,label[:,None])[:,0]*class_weight[label]).mean()
            kld = (distribution.exp()*(distribution-frozen)).sum(-1).mean()
            utility = (distribution.exp()*reward).sum(-1).mean()
            objective = nll + train.TRUST*kld
            opt.zero_grad()
            objective.backward()
            norm = [float(p.grad.norm()) for p in learned]
            assert all(torch.isfinite(p.grad).all() for p in learned) and max(norm)>0
            opt.step()
            step = {"step": 1 + i//train.BATCH, "ids": [table[j]["id"] for j in group],
                    "weighted_nll": float(nll.detach()), "kl": float(kld.detach()),
                    "utility": float(utility.detach()), "gradient_norms": norm}
            log.write(json.dumps(step)+"\n")
            log.flush()
    assert all(p._version == version for p,version in fixed)
    output = train.capture_vectors(model, tokens, table, select, action_ids)
    model.save_pretrained(out / "adapter", safe_serialization=True)
    model.load_adapter(str(out / "adapter"), adapter_name="replay")
    model.set_adapter("replay")
    model.eval()
    torch.testing.assert_close(train.capture_vectors(model, tokens, table, select, action_ids), output, rtol=0, atol=0)
    with model.disable_adapter():
        torch.testing.assert_close(train.capture_vectors(model, tokens, table, select, action_ids), baseline, rtol=0, atol=0)
    with (out / "scores.jsonl").open("w") as f:
        for row, base, tuned in zip(table, baseline.tolist(), output.tolist(), strict=True):
            f.write(json.dumps(row | {"frozen": base, "adapted": tuned, "action_ids": action_ids}) + "\n")
    files = sorted(p for p in out.rglob("*") if p.is_file())
    (out / "complete.json").write_text(json.dumps({"actual_updates": n//train.BATCH,
        "disk_adapter_reload_exact": True, "frozen_outputs_replayed_exactly": True,
        "sha256": {str(p.relative_to(out)): train.digest(p) for p in files}}, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    run(parser.parse_args().directory)
