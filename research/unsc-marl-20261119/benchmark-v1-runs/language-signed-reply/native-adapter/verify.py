"""Verify trained parameter scope, exposure, prompts and outcome replay."""
from collections import Counter
import json
import math

import torch
from safetensors.torch import load_file
from transformers import AutoTokenizer

import score_run
import train

HERE, E = train.HERE, train.E


def verify():
    d = HERE / "evidence"
    o = E.read(d / "complete.json")
    launch = E.read(d / "launch.json")
    assert launch["sha256"] == {p.name: train.digest(p) for p in (
        HERE / "train.py", HERE / "protocol.md", HERE.parent / "roster.json", E.HERE / "release.json")}
    for key, stamp in o["sha256"].items():
        assert train.digest(d / key) == stamp
    blobs = load_file(d / "adapter/adapter_model.safetensors")
    assert len(blobs) == 8 and all("lora_" in k and (".27." in k or ".31." in k) for k in blobs)
    assert sum(t.numel() for t in blobs.values()) == o["adapter_elements"]
    assert all(torch.isfinite(x).all() for x in blobs.values())
    assert set(o["updated_tensor_norms"]) == {k.replace(".weight", ".default.weight") for k in blobs}
    assert all(norm > 0 for norm in o["updated_tensor_norms"].values())
    roster = train.cases.roster()
    assert roster == E.read(HERE.parent / "roster.json")
    tokenizer = AutoTokenizer.from_pretrained(train.MODEL, local_files_only=True)
    rows = score_run.records()
    actions = [tokenizer.encode(k, add_special_tokens=False)[0] for k in train.cases.DEC]
    expected = [(f"{split}/{row['id']}", row) for split, entries in roster.items() for row in entries]
    for outcome, (key, row) in zip(rows, expected, strict=True):
        assert outcome["id"] == key and outcome["tokens"] == train.capture.encode(tokenizer, row["messages"])
        assert outcome["action_ids"] == actions and outcome["utility"] == row["utility"]
        assert all(math.isfinite(x) for label in ("frozen", "adapted") for x in outcome[label])
    updates = [json.loads(line) for line in (d / "updates.jsonl").read_text().splitlines()]
    count = len(roster["train"])
    order = torch.randperm(count, generator=torch.Generator().manual_seed(train.SEED))
    assert o["actual_updates"] == launch["planned_updates"] == len(updates) == 12
    assert [n for row in updates for n in row["ids"]] == [expected[j][0] for j in order.tolist()]
    assert Counter(n for row in updates for n in row["ids"]) == Counter(k for k,_ in expected[:count])
    assert all(abs(row["loss"] - (-row["utility"] + train.TRUST*row["kl_to_frozen"])) < 2.e-7 for row in updates)
    assert o["frozen_parameters_replayed_exactly"] and o["disk_adapter_reload_exact"]
    assert score_run.run() == E.read(HERE / "results.json")
    return {"verified_updates": len(updates), "verified_prompts": len(rows), "held_prompt_count": len(rows) - count,
            "adapter_elements": o["adapter_elements"], "frozen_outputs_exact_in_run": True,
            "disk_adapter_reload_exact": True,
            "role_local_check_and_controller_replay": True}


if __name__ == "__main__":
    E.emit(verify())
