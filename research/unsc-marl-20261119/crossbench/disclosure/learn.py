"""Shared-reward REINFORCE for two rounds of truthful package disclosures."""
import argparse
from collections import Counter
import hashlib
from itertools import combinations, product
import json
import math
from pathlib import Path
import os
import random
import socket
import subprocess
import sys

import torch
from torch import nn

from protocol import HERE, ROOT, readout, truthful_disclosure

SEED = 26111901
UPDATES = 160
BATCH = 128
MESSAGE_COST = 0.01
TRAIN_OPTIONS = "ABC"
TEST_OPTIONS = "ABCD"
ROLES = ("first", "second")


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(9, 32), nn.Tanh(), nn.Linear(32, 1))

    def forward(self, local, own, other, phase):
        n = local.shape[-1]
        pad = lambda x: torch.nn.functional.pad(x, (0, 1))
        options = torch.arange(n + 1).reshape(1, 1, -1)
        features = (
            pad(local), pad(own), pad(other), options / n, options == n,
            torch.arange(2).reshape(1, -1, 1), local.float().mean(dim=-1, keepdim=True),
            (other != 0).float().mean(dim=-1, keepdim=True), torch.tensor(phase),
        )
        values = torch.stack(torch.broadcast_tensors(*features), dim=-1).float()
        return self.network(values).squeeze(-1)


def run(policy, worlds, mode):
    local = torch.tensor(worlds, dtype=torch.bool)
    blank = torch.zeros_like(local, dtype=torch.int8)
    n = local.shape[-1]
    option = torch.arange(n).reshape(1, 1, -1)
    own = blank
    signed_turns = []
    total_lp, entropy = torch.zeros(len(worlds)), torch.zeros(len(worlds))
    messages = torch.zeros(len(worlds))
    picks = []
    for phase in (0, 1):
        peer = blank if mode == "silent" else own.flip(dims=(1,))
        dist = torch.distributions.Categorical(logits=policy(local, own, peer, phase))
        choice = dist.sample() if mode == "train" else dist.logits.argmax(-1)
        total_lp += dist.log_prob(choice).sum(-1)
        entropy += dist.entropy().sum(-1)
        messages += (choice != n).sum(-1)
        effect = torch.where(local, 1, -1).to(torch.int8) * (option == choice.unsqueeze(-1))
        own = torch.where(effect == 0, own, effect)
        signed_turns.append(effect.tolist())
        picks.append(choice.tolist())
    agreement = (own == 1).all(dim=1).any(-1)
    impasse = (own == -1).any(dim=1).all(-1)
    feasible = local.all(dim=1).any(-1)
    assert (agreement <= feasible).all() and (impasse <= ~feasible).all()
    reward = (agreement | impasse).float() - MESSAGE_COST * messages
    result = []
    labels = "ABCD"[:n]
    for i, world in enumerate(worlds):
        annotated = []
        for phase, values in enumerate(signed_turns):
            for role in (0, 1):
                labels_and_sign = list(zip(labels, values[i][role]))
                accepts = [a for a, sign in labels_and_sign if sign == 1]
                excludes = [a for a, sign in labels_and_sign if sign == -1]
                if not accepts and not excludes:
                    continue
                claim = {"id": f"r{phase}d{role}", "role": ROLES[role], "accepts": accepts, "excludes": excludes}
                assert truthful_disclosure(claim, [a for a, on in zip(labels, world[role]) if on])
                annotated.append(claim)
        state = readout(labels, ROLES, annotated)
        signal = "AGREEMENT_POSSIBLE" if agreement[i] else "IMPASSE" if impasse[i] else "UNRESOLVED"
        assert state["state"] == signal
        result.append({
            "world": world, "feasible": bool(feasible[i]), "state": signal,
            "first": picks[0][i], "second": picks[1][i],
            "claims": annotated, "unique_claims": len({(r["role"], *(r["accepts"] or r["excludes"])) for r in annotated}),
            "reward": float(signal != "UNRESOLVED") - MESSAGE_COST * len(annotated),
        })
    return result, reward, total_lp, entropy


def summarize(rows):
    counts = Counter(x["state"] for x in rows)
    agreement = sum(r["feasible"] for r in rows)
    n = len(rows)
    return {
        "worlds": n, "agreement": counts["AGREEMENT_POSSIBLE"], "agreement_denominator": agreement,
        "impasse": counts["IMPASSE"], "impasse_denominator": n - agreement, "unresolved": counts["UNRESOLVED"],
        "distinct_claims": sum(x["unique_claims"] for x in rows), "nonpass": sum(len(x["claims"]) for x in rows),
        "mean_reward": sum(x["reward"] for x in rows) / n,
    }


def exact(options):
    vals = range(len(options))
    menus = [{*c} for n in range(1, len(options) + 1) for c in combinations(vals, n)]
    return [[[int(i in m) for i in vals] for m in pair] for pair in product(menus, repeat=2)]


def sample(seed, grid):
    rng = random.Random(seed)
    agree = []
    impasse = []
    for pair in grid:
        (agree if any(a and b for a, b in zip(*pair)) else impasse).append(pair)
    return [rng.choice(agree if i % 2 else impasse) for i in range(BATCH)]


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("out", type=Path)
    args = cli.parse_args()
    args.out.mkdir()
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)
    locks = (Path(__file__), HERE / "protocol.py", ROOT / "decision_ledger.py", HERE / "capacity.json")
    dump(args.out / "launch.json", {
        "host": socket.gethostname(), "pid": os.getpid(), "gpu_uuids": [],
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.out.resolve()),
        "runtime": str(torch.__version__), "seed": SEED, "updates": UPDATES, "batch": BATCH,
        "message_cost": MESSAGE_COST, "training_option_labels": TRAIN_OPTIONS, "test_option_labels": TEST_OPTIONS,
        "hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in locks},
    })
    net = Actor()
    grid, held = exact(TRAIN_OPTIONS), exact(TEST_OPTIONS)
    weights = {k: t.detach().clone() for k, t in net.state_dict().items()}
    with torch.no_grad():
        base, *_ = run(net, held, "peer")
    dump(args.out / "initial.json", summarize(base))
    optim = torch.optim.Adam(net.parameters(), lr=0.02)
    with (args.out / "updates.jsonl").open("x") as stream:
        for step in range(UPDATES):
            rows, rewards, logp, entropy = run(net, sample(SEED + step, grid), "train")
            objective = -((rewards - rewards.mean()) * logp + 0.015 * entropy).mean()
            optim.zero_grad()
            objective.backward()
            gn = nn.utils.clip_grad_norm_(net.parameters(), 1.0, error_if_nonfinite=True).item()
            assert math.isfinite(gn)
            optim.step()
            stream.write(json.dumps({"step": step + 1, "loss": objective.item(), "grad_norm": gn,
                                     **summarize(rows)}) + "\n")
    changed = [k for k, t in net.state_dict().items() if not torch.equal(t, weights[k])]
    assert changed
    after = {}
    with torch.no_grad():
        for key in ("peer", "silent"):
            after[key], *_ = run(net, held, key)
    contrasts = Counter((a["state"] != "UNRESOLVED", b["state"] != "UNRESOLVED")
                        for a, b in zip(after["peer"], after["silent"]))
    stats = {"initial": summarize(base), **{key: summarize(rows) for key, rows in after.items()},
             "paired_peer_vs_silent": {str(k): v for k, v in contrasts.items()},
             "changed_parameters": changed}
    dump(args.out / "results.json", stats)
    dump(args.out / "traces.json", {"initial": base, **after})
    dump(args.out / "state.json", {k: v.tolist() for k, v in net.state_dict().items()})
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
