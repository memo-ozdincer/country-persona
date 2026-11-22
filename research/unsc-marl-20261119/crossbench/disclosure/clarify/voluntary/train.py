"""Train shared sequential local disclosure with balanced terminal rewards."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import torch
from torch import nn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from priority_audit import policy
from public_planner import HORIZON, states
from voluntary_bound import verdict

SEED = 26111907
UPDATES = 160
BATCH = 128
COST = 0.025
PRIORITY_ORDER = (0, 2, 3, 1)


def presentations(n):
    for x, y in product(range(1, 1 << n), repeat=2):
        for a, b in product(range(n), repeat=2):
            if x & (1 << a) and y & (1 << b):
                yield tuple(tuple(bool(m & (1 << i)) for i in range(n)) for m in (x, y)), (a, b)


def tensors(data):
    menus, openings = zip(*data, strict=True)
    local = torch.tensor(menus, dtype=torch.bool)
    public = torch.nn.functional.one_hot(torch.tensor(openings), local.shape[-1]).to(torch.int8)
    return local, public


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(9, 24), nn.Tanh(), nn.Linear(24, 1))
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, own, my_message, peer_message, step):
        size, n = own.shape
        nleft = HORIZON - step
        position = torch.arange(n).expand(size, -1) / n
        peer_accepts = peer_message == 1
        peer_excludes = peer_message == -1
        available = (my_message == 0) & ~peer_excludes
        priority = (3 * (peer_accepts & own) + 2 * (~peer_accepts & ~own) + (~peer_accepts & own)).float()
        inputs = torch.stack(torch.broadcast_tensors(
            own, peer_accepts, peer_excludes, position, my_message.float(),
            own.float().mean(-1, keepdim=True), peer_accepts.float().mean(-1, keepdim=True),
            available.float().mean(-1, keepdim=True), torch.tensor(nleft / HORIZON)
        ), dim=-1).float()
        logits = priority * 2 - 0.01 * position + self.net(inputs).squeeze(-1)
        masked = logits.masked_fill(~available, -torch.inf)
        # A no-op is needed only when this speaker has exhausted useful slots.
        forced_pass = torch.where(available.any(-1), -torch.inf, 0.)
        return torch.cat((masked, forced_pass[:, None]), dim=-1)


def terminal(signed):
    a = (signed == 1).all(dim=1).any(-1)
    d = (signed == -1).any(dim=1).all(-1)
    return a, d


def roll(actor, local, opening, mode):
    count, _, n = local.shape
    signed = opening.clone()
    agree, deadlock = terminal(signed)
    rounds = torch.zeros(count, dtype=torch.long)
    log_p, entropy = torch.zeros(count), torch.zeros(count)
    choices = []
    for step in range(HORIZON):
        i = (step + 1) % 2
        live = ~(agree | deadlock)
        peer = signed[:, 1-i] if mode != "masked" else torch.zeros_like(signed[:, 1-i])
        dist = torch.distributions.Categorical(logits=actor(local[:, i], signed[:, i], peer, step))
        pick = dist.sample() if mode == "train" else dist.logits.argmax(dim=-1)
        log_p += dist.log_prob(pick) * live
        entropy += dist.entropy() * live
        changed = (torch.arange(n) == pick[:, None]) & live[:, None]
        signed[:, i] = torch.where(changed, torch.where(local[:, i], 1, -1), signed[:, i]).to(torch.int8)
        choices.append(torch.where(live, pick, -1).tolist())
        rounds += live
        agree, deadlock = terminal(signed)
    correct = agree | deadlock
    assert (agree <= local.all(dim=1).any(-1)).all() and (deadlock <= ~local.all(dim=1).any(-1)).all()
    return (correct.float() - COST * rounds), log_p, entropy, agree, deadlock, rounds, choices


def assess(actor, inputs, mode):
    reward, _, _, a, d, rounds, choices = roll(actor, *inputs, mode)
    reachable = a | d
    return {"agreement": int(a.sum()), "impasse": int(d.sum()), "mean_reward": float(reward.mean()),
            "mean_turns": float(rounds.float().mean()),
            "first_certificate_counts": dict(Counter(str(int(r)) if ok else "unreached"
                                                     for r, ok in zip(rounds, reachable, strict=True))),
            "first_certificate": [int(r) if ok else None for r, ok in zip(rounds, reachable, strict=True)],
            "actions": choices}


def main(output):
    output.mkdir()
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    training, held_out = list(presentations(3)), list(presentations(4))
    strata = [tensors([p for p in training if any(x and y for x, y in zip(*p[0])) == cls])
              for cls in (True, False)]
    test = tensors(held_out)
    actor = Actor()
    origin = {k: v.detach().clone() for k, v in actor.state_dict().items()}
    optimizer = torch.optim.Adam(actor.parameters(), lr=0.012)
    files = (Path(__file__), *(HERE.parent / name for name in
                              ("priority_audit.py", "voluntary_bound.py", "public_planner.py")))
    files = {p.name: sha256(p.read_bytes()).hexdigest() for p in files}
    launch = {"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
              "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
              "command": [sys.executable, *sys.argv], "run_directory": str(output.resolve()),
              "torch": torch.__version__, "sha256": files, "seed": SEED, "updates": UPDATES,
              "train_presentations_by_class": [len(x[0]) for x in strata], "held_out_presentations": len(held_out)}
    (output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    with torch.no_grad():
        baseline = assess(actor, test, "greedy")
    chooser = policy(PRIORITY_ORDER)
    assert baseline["first_certificate"] == [verdict(world, opening, chooser) for world, opening in states()]
    with (output / "updates.jsonl").open("x") as log:
        for step in range(UPDATES):
            halves = [(x[i], o[i]) for x, o in strata for i in [torch.randint(len(x), (BATCH//2,))]]
            samples = tuple(torch.cat([half[k] for half in halves]) for k in (0, 1))
            reward, lp, entropy, agreement, deadlock, turns, _ = roll(actor, *samples, "train")
            advantage = (reward - reward.mean()).detach()
            loss = -(advantage * lp).mean() - 0.008 * entropy.mean()
            optimizer.zero_grad()
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(actor.parameters(), 1.0)
            assert torch.isfinite(norm) and norm > 0
            optimizer.step()
            log.write(json.dumps({"step": step, "reward": float(reward.mean()),
                                  "agreement": int(agreement.sum()), "impasse": int(deadlock.sum()),
                                  "grad_norm": float(norm), "mean_turns": float(turns.float().mean())}) + "\n")
    assert any(not torch.equal(origin[k], v) for k, v in actor.state_dict().items())
    with torch.no_grad():
        result = {"baseline": baseline, "learned": assess(actor, test, "greedy"),
                  "learned_peer_masked": assess(actor, test, "masked")}
    torch.save(actor.state_dict(), output / "policy.pt")
    (output / "results.json").write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print({k: {f: v[f] for f in ("agreement", "impasse", "mean_reward", "mean_turns")} for k, v in result.items()},
          flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    main(parser.parse_args().output)
