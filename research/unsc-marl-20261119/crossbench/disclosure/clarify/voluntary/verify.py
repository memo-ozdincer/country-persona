"""Rebuild held-out outcomes from the saved local policy and its initialization."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path

import torch

from train import Actor, HERE, SEED, UPDATES, assess, presentations, tensors


def verify(run):
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    launch = json.loads((run / "launch.json").read_text())
    assert launch["seed"] == SEED and launch["updates"] == UPDATES
    for name, expected in launch["sha256"].items():
        path = (HERE if name == "train.py" else HERE.parent) / name
        assert sha256(path.read_bytes()).hexdigest() == expected
    updates = list(map(json.loads, (run / "updates.jsonl").read_text().splitlines()))
    assert [r["step"] for r in updates] == list(range(UPDATES))
    assert all(math.isfinite(r["grad_norm"]) and r["grad_norm"] > 0 for r in updates)
    held_out = list(presentations(4))
    test = tensors(held_out)
    assert len(held_out) == launch["held_out_presentations"] == 1024
    actor = Actor()
    fitted = torch.load(run / "policy.pt", map_location="cpu", weights_only=True)
    changed = [name for name, p in actor.state_dict().items() if not torch.equal(p, fitted[name])]
    assert changed
    with torch.no_grad():
        baseline = assess(actor, test, "greedy")
        actor.load_state_dict(fitted)
        learned = assess(actor, test, "greedy")
        mask = assess(actor, test, "masked")
    assert json.loads((run / "results.json").read_text()) == {
        "baseline": baseline, "learned": learned, "learned_peer_masked": mask}
    changes = Counter()
    for (menus, _), a, b in zip(held_out, baseline["first_certificate"], learned["first_certificate"], strict=True):
        family = "agreement" if any(x and y for x, y in zip(*menus)) else "impasse"
        change = "gain" if a is None and b is not None else "loss" if a is not None and b is None else (
            "faster" if b is not None and b < a else "slower" if b is not None and b > a else "same")
        changes[(family, change)] += 1
    return {"verified_updates": len(updates), "changed_tensors": changed,
            "paired_changes": {"/".join(key): value for key, value in changes.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    print(json.dumps(verify(parser.parse_args().run), indent=2))
