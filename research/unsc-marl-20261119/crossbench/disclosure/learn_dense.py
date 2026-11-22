"""One reward ablation for public exclusion evidence in infeasible worlds."""
import argparse
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys

import torch
from torch import nn

from learn import (Actor, BATCH, HERE, MESSAGE_COST, ROOT, SEED, TEST_OPTIONS, TRAIN_OPTIONS, UPDATES,
                   dump, exact, run, sample, summarize)
from run import digest

SHAPING_WEIGHT = 0.75


def exclusion_bonus(rows):
    # Applied only in training. The environment knows the label and the policy
    # observes its own signed menu and visible disclosures, as in the control.
    return torch.tensor([
        SHAPING_WEIGHT * len({p for c in row["claims"] for p in c["excludes"]}) / len(TRAIN_OPTIONS)
        if not row["feasible"] else 0.0 for row in rows
    ], dtype=torch.float32)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("out", type=Path)
    args = cli.parse_args()
    args.out.mkdir()
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)
    baseline = HERE / "terminal"
    parent = json.loads((baseline / "launch.json").read_text())
    assert all(digest(path) == parent["hashes"][path.name] for path in (
        HERE / "learn.py", HERE / "protocol.py", ROOT / "decision_ledger.py", HERE / "capacity.json"))
    locks = (Path(__file__), HERE / "learn.py", HERE / "protocol.py", ROOT / "decision_ledger.py",
             baseline / "launch.json", baseline / "results.json")
    dump(args.out / "launch.json", {
        "host": socket.gethostname(), "pid": os.getpid(), "gpu_uuids": [],
        "process_start": subprocess.check_output(
            ["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.out.resolve()),
        "runtime": str(torch.__version__), "seed": SEED, "updates": UPDATES, "batch": BATCH,
        "message_cost": MESSAGE_COST, "training_option_labels": TRAIN_OPTIONS,
        "test_option_labels": TEST_OPTIONS, "shaping_weight": SHAPING_WEIGHT,
        "hashes": {p.name: digest(p) for p in locks},
    })
    policy = Actor()
    grid, test = exact(TRAIN_OPTIONS), exact(TEST_OPTIONS)
    with torch.no_grad():
        init = summarize(run(policy, test, "peer")[0])
    assert init == json.loads((baseline / "initial.json").read_text())
    dump(args.out / "initial.json", init)
    optim = torch.optim.Adam(policy.parameters(), lr=0.02)
    with (args.out / "updates.jsonl").open("x") as stream:
        for step in range(UPDATES):
            rows, base, logp, entropy = run(policy, sample(SEED + step, grid), "train")
            bonus = exclusion_bonus(rows)
            reward = base + bonus
            loss = -((reward - reward.mean()) * logp + 0.015 * entropy).mean()
            optim.zero_grad()
            loss.backward()
            gn = nn.utils.clip_grad_norm_(policy.parameters(), 1.0, error_if_nonfinite=True).item()
            assert math.isfinite(gn)
            optim.step()
            stream.write(json.dumps({"step": step + 1, "loss": loss.item(), "grad_norm": gn,
                                     "mean_auxiliary_reward": bonus.mean().item(), **summarize(rows)}) + "\n")
    trace = {}
    with torch.no_grad():
        for name in ("peer", "silent"):
            trace[name] = run(policy, test, name)[0]
    stats = {"initial": init, **{key: summarize(rows) for key, rows in trace.items()}}
    dump(args.out / "results.json", stats)
    dump(args.out / "traces.json", trace)
    dump(args.out / "state.json", {k: v.tolist() for k, v in policy.state_dict().items()})
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
