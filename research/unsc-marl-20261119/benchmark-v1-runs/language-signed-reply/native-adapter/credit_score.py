"""Replay the reward-credit adapter against the same actor and chair controls."""
import json
import math
from pathlib import Path

from safetensors.torch import load_file

import score_run
import train

HERE, E = train.HERE, train.E


def run():
    d = HERE / "credit-evidence"
    complete, launch = (E.read(d / key) for key in ("complete.json", "launch.json"))
    for name, digest in complete["sha256"].items():
        assert train.digest(d / name) == digest
    for p in (HERE / "credit_train.py", HERE / "train.py", HERE / "credit-protocol.md",
              HERE / "evidence/complete.json", HERE.parent / "roster.json"):
        assert launch["sha256"][p.name] == train.digest(p)
    original = score_run.records()
    new = [json.loads(l) for l in (d / "scores.jsonl").read_text().splitlines()]
    for a,b in zip(original,new,strict=True):
        assert {k:v for k,v in a.items() if k != "adapted"} == {k:v for k,v in b.items() if k != "adapted"}
    initial, tuned = [[json.loads(l) for l in (root / "updates.jsonl").read_text().splitlines()]
                      for root in (HERE / "evidence", d)]
    assert len(initial) == len(tuned) == complete["actual_updates"] == 12
    assert [row["ids"] for row in initial] == [row["ids"] for row in tuned]
    assert all(math.isfinite(x) for row in tuned for x in row["gradient_norms"])
    a,b = [load_file(root / "adapter/adapter_model.safetensors") for root in (HERE / "evidence", d)]
    assert all(a[k].shape == b[k].shape for k in a)
    assert a.keys() == b.keys() and len(a) == 8
    assert complete["disk_adapter_reload_exact"] and complete["frozen_outputs_replayed_exactly"]
    data = train.cases.roster()
    vectors = score_run.native_logits(new)
    n = len(data["train"])
    output = {}
    for split, sl in (("train",slice(0,n)),("held",slice(n,None))):
        results = score_run.old_fit.review(data[split], {k: v[sl] for k,v in vectors.items()})
        output[split] = {"rows": results, "summary": score_run.old_fit.aggregate(results)}
    return {"results": output, "controller": score_run.controller_records(output["held"]["rows"]),
            "verified_prompts": len(new), "verified_updates": len(tuned), "disk_reload_exact": True,
            "sha256": {p.name: train.digest(p) for p in (
                Path(__file__), d / "complete.json", HERE / "results.json")}}


if __name__ == "__main__":
    E.emit(run())
