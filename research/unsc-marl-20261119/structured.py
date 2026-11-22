"""Shared parameter policy gradient for the two-delegate workshop."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import socket
import subprocess
import sys

import torch
from torch import nn

from environment import ABSENT, HOLD, FAMILIES_PATH, audit, outcome, sample_worlds

TRAIN = ("climate", "sanctions")
TEST = ("women_peace_security",)
SEED = 260119
UPDATES = 160
BATCH = 128
EVAL_COUNT = 256


class Delegate(nn.Module):
    def __init__(self):
        super().__init__()
        self.proposal = nn.Sequential(nn.Linear(6, 24), nn.Tanh(), nn.Linear(24, 1))
        self.ballot = nn.Sequential(nn.Linear(6, 24), nn.Tanh(), nn.Linear(24, 1))

    def logits(self, approved, own, peer, phase):
        batch, roles, options = approved.shape
        choices = torch.arange(HOLD, options)
        approved = torch.cat((torch.ones(batch, roles, 1), approved), dim=-1)
        own_mark = choices == own.unsqueeze(-1)
        peer_mark = choices == peer.unsqueeze(-1)
        role_index = torch.arange(roles).view(1, roles, 1).expand_as(approved)
        count = (approved.mean(-1, keepdim=True)).expand_as(approved)
        hold = (choices == HOLD).expand_as(approved)
        inputs = torch.stack((approved, own_mark, peer_mark, role_index, count, hold), dim=-1)
        return (self.proposal if phase == "proposal" else self.ballot)(inputs).squeeze(-1)


def rollout(policy, cases, channel, greedy=False):
    approved = torch.tensor([case["mandates"] for case in cases], dtype=torch.float32)
    unseen = torch.full(approved.shape[:2], ABSENT)
    proposal = torch.distributions.Categorical(logits=policy.logits(approved, unseen, unseen, "proposal"))
    first = proposal.logits.argmax(-1) if greedy else proposal.sample()
    sent = first + HOLD
    received = sent.flip(1)
    if channel == "silent":
        received = unseen
    elif channel == "shuffled":
        received = received.roll(1, 0)
    ballot = torch.distributions.Categorical(logits=policy.logits(approved, sent, received, "ballot"))
    second = ballot.logits.argmax(-1) if greedy else ballot.sample()
    votes = second + HOLD
    rows = [
        {"case": case, "signals": sent_row, "received": observed, "ballots": votes_row,
         **outcome(case, sent_row, votes_row)}
        for case, sent_row, observed, votes_row in zip(cases, sent.tolist(), received.tolist(), votes.tolist())
    ]
    log_prob = (proposal.log_prob(first) + ballot.log_prob(second)).sum(-1)
    entropy = (proposal.entropy() + ballot.entropy()).sum(-1)
    return rows, log_prob, entropy


def summarize(rows):
    return {
        "episodes": len(rows),
        "feasible": sum(r["feasible"] for r in rows),
        **{k: sum(r[k] for r in rows) for k in (
            "strict", "agreement", "valid_deadlock", "false_hold", "unsupported_signal", "unsupported_ballot"
        )},
        "mean_reward": sum(r["reward"] for r in rows) / len(rows),
    }


def save_json(path, content):
    path.write_text(json.dumps(content, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()), "gpu_uuids": [],
        "torch": str(torch.__version__), "seed": SEED, "updates": UPDATES, "batch": BATCH,
        "test_episodes_per_split": EVAL_COUNT,
        "input_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), FAMILIES_PATH, FAMILIES_PATH.with_name("environment.py"))
        },
    }
    save_json(args.output / "launch.json", launch)
    audits = audit()
    save_json(args.output / "reward-audit.json", audits)
    validation = {
        "train_families": sample_worlds(TRAIN, EVAL_COUNT, SEED + 1),
        "test_family": sample_worlds(TEST, EVAL_COUNT, SEED + 2),
    }
    policy = Delegate()
    optimizer = torch.optim.Adam(policy.parameters(), lr=0.015)
    results = {}
    for step in ("before", "after"):
        if step == "after":
            with (args.output / "updates.jsonl").open("x") as trace:
                for update in range(UPDATES):
                    cases = sample_worlds(TRAIN, BATCH, SEED + 10 + update)
                    rows, log_prob, entropy = rollout(policy, cases, "peer")
                    rewards = torch.tensor([row["reward"] for row in rows], dtype=torch.float32)
                    advantage = rewards - rewards.mean()
                    loss = -(advantage * log_prob + 0.015 * entropy).mean()
                    optimizer.zero_grad()
                    loss.backward()
                    norm = nn.utils.clip_grad_norm_(policy.parameters(), 1.0, error_if_nonfinite=True)
                    optimizer.step()
                    trace.write(json.dumps({"update": update + 1, "loss": loss.item(),
                                            "gradient_norm": norm.item(), **summarize(rows)}) + "\n")
        with torch.no_grad():
            for split, cases in validation.items():
                for channel in ("peer", "silent", "shuffled"):
                    rows, _, _ = rollout(policy, cases, channel, greedy=True)
                    name = f"{step}-{split}-{channel}"
                    results[name] = summarize(rows)
                    save_json(args.output / f"{name}.json", rows)
    # Human-readable float arrays suffice to reload the small learned policy.
    save_json(args.output / "policy.json", {k: v.tolist() for k, v in policy.state_dict().items()})
    save_json(args.output / "scores.json", results)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
