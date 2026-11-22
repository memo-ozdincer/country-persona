"""Train two policies to choose questions and truthful optional counteroffers."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import os
import random
import socket
import subprocess
import sys

import torch
from torch import nn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from environment import FAMILIES_PATH, world
from evaluate import exhaustive_worlds

SEED = 190226
BATCH = 128
UPDATES = 160
LIMIT = 2
PAIR_COST = 0.04
COUNTER_COST = 0.01
TRAIN = ("climate", "sanctions")
TEST = "women_peace_security"


class Policies(nn.Module):
    def __init__(self):
        super().__init__()
        self.ask = nn.Sequential(nn.Linear(5, 20), nn.Tanh(), nn.Linear(20, 1))
        self.offer = nn.Sequential(nn.Linear(6, 20), nn.Tanh(), nn.Linear(20, 1))

    def scores(self, net, features):
        return net(torch.stack(torch.broadcast_tensors(*features), dim=-1).float()).squeeze(-1)


def evaluate_decisions(local, remote, ask_history, replies, final, pairs, offers):
    """Audit claims independently of the actor masks and reward calculation."""
    feasible = bool(local & remote)
    rejected, previous_counters = set(), set()
    agreed = None
    assert len(ask_history) == len(replies) == pairs <= LIMIT
    recorded_counters = 0
    for asked, response in zip(ask_history, replies):
        assert agreed is None and asked in local and asked not in rejected
        assert response["accept"] == (asked in remote)
        if response["accept"]:
            assert response["counter"] is None
            agreed = asked
            continue
        rejected.add(asked)
        counter = response["counter"]
        if counter is not None:
            assert counter in remote and counter not in previous_counters and counter != min(remote)
            previous_counters.add(counter)
            recorded_counters += 1
            if counter in local:
                agreed = counter
    assert recorded_counters == offers
    if final == "opening_agreement":
        assert min(remote) in local and pairs == 0
    elif final == "agreement":
        assert agreed is not None and feasible
    elif final == "deadlock":
        assert not feasible and local <= rejected and agreed is None
    else:
        assert final == "unresolved" and agreed is None and pairs == LIMIT and not local <= rejected
    return float(final != "unresolved") - PAIR_COST * pairs - COUNTER_COST * offers


def rollout(policy, cases, arms, mode):
    size = len(cases[0]["options"])
    mandates = torch.tensor([c["mandates"] for c in cases], dtype=torch.bool)
    # Orient private views without using a hidden overlap bit as a policy feature.
    indices = torch.arange(len(cases))
    opener = torch.tensor(arms)
    local = mandates[indices, opener]
    remote = mandates[indices, 1 - opener]
    position = torch.arange(size + 1).unsqueeze(0)
    scaled_position = position / size
    local_first = local.max(dim=1).indices.unsqueeze(1)
    remote_first = remote.max(dim=1).indices.unsqueeze(1)
    opened = local[indices, remote_first.squeeze(1)]
    agreed = opened.clone()
    rejected = torch.zeros_like(local)
    counters_seen = torch.zeros_like(local)
    remote_past_questions = torch.zeros_like(local)
    pairs = torch.zeros(len(cases), dtype=torch.long)
    offers = torch.zeros_like(pairs)
    log_q = torch.zeros(len(cases))
    log_r = torch.zeros(len(cases))
    entropy = torch.zeros(len(cases))
    rows_history = []

    def choose(logits, legal):
        dist = torch.distributions.Categorical(logits=logits.masked_fill(~legal, -1e9))
        action = dist.sample() if mode == "sample" else dist.logits.argmax(-1)
        return action, dist.log_prob(action), dist.entropy()

    for step in range(LIMIT):
        remaining = local & ~rejected
        active = remaining.any(-1) & ~agreed
        pairs = pairs + active.long()
        available = torch.cat([remaining, (~active).unsqueeze(1)], dim=1)
        if mode in {"scripted", "binary"}:
            question = available.max(dim=1).indices
        else:
            query_logits = policy.scores(policy.ask, (
                scaled_position, position == local_first, position == remote_first,
                remaining.float().mean(1, keepdim=True), torch.tensor(step / LIMIT),
            )).expand_as(available)
            question, lp, ent = choose(query_logits, available)
            log_q = log_q + lp * active
            entropy = entropy + ent * active
        tagged = (position[:, :size] == question.unsqueeze(1)) & active.unsqueeze(1)
        accept = (remote & tagged).any(-1)
        negative = active & ~accept
        rejected = rejected | (tagged & negative.unsqueeze(1))
        remote_past_questions = remote_past_questions | tagged
        alternatives = remote & ~counters_seen & (position[:, :size] != remote_first)
        # A truthful negative reply can carry one previously undisclosed alternative.
        counter_legal = torch.cat([alternatives & negative.unsqueeze(1), torch.ones_like(negative).unsqueeze(1)], dim=1)
        if mode == "scripted":
            counter = counter_legal.max(dim=1).indices
        elif mode == "binary":
            counter = torch.full_like(question, size)
        else:
            response_logits = policy.scores(policy.offer, (
                scaled_position, position == size, position == local_first, torch.tensor(step / LIMIT),
                remote.float().mean(1, keepdim=True), remote_past_questions.float().mean(1, keepdim=True),
            )).expand_as(counter_legal)
            counter, lp, ent = choose(response_logits, counter_legal)
            log_r = log_r + lp * negative
            entropy = entropy + ent * negative
        if mode == "counter_removed":
            counter = torch.full_like(counter, size)
        made = negative & (counter != size)
        revealed = (position[:, :size] == counter.unsqueeze(1)) & made.unsqueeze(1)
        counters_seen = counters_seen | revealed
        offers = offers + made.long()
        agreed = agreed | accept | (local & revealed).any(-1)
        rows_history.append((active.tolist(), question.tolist(), accept.tolist(), counter.tolist()))

    deadlocked = ~agreed & ~(local & ~rejected).any(-1)
    strict = agreed | deadlocked
    rewards = strict.float() - PAIR_COST * pairs - COUNTER_COST * offers
    all_rows = []
    for i, (case, arm) in enumerate(zip(cases, arms)):
        queries, replies = [], []
        for active, questions, accepted, counters in rows_history:
            if active[i]:
                queries.append(questions[i])
                replies.append({"accept": accepted[i], "counter": None if counters[i] == size else counters[i]})
        final = ("opening_agreement" if opened[i] else "agreement" if agreed[i]
                 else "deadlock" if deadlocked[i] else "unresolved")
        own = {j for j, bit in enumerate(case["mandates"][arm]) if bit}
        peer = {j for j, bit in enumerate(case["mandates"][1 - arm]) if bit}
        reward = evaluate_decisions(own, peer, queries, replies, final, int(pairs[i]), int(offers[i]))
        assert abs(reward - float(rewards[i])) < 1e-6
        all_rows.append({"case": case, "leader": arm, "queries": queries, "replies": replies, "final": final,
                         "feasible": bool(own & peer), "pairs": int(pairs[i]), "counters": int(offers[i]), "reward": reward})
    return all_rows, rewards, log_q, log_r, entropy


def summarize(rows):
    states = Counter(row["final"] for row in rows)
    feasible = sum(row["feasible"] for row in rows)
    agreement = states["agreement"] + states["opening_agreement"]
    return {
        "episodes": len(rows), "feasible": feasible, "agreements": agreement,
        "infeasible": len(rows) - feasible, "deadlocks": states["deadlock"], "unresolved": states["unresolved"],
        "questions": sum(row["pairs"] for row in rows), "counters": sum(row["counters"] for row in rows),
        "mean_reward": sum(row["reward"] for row in rows) / len(rows),
        "agreement_recall": agreement / feasible,
        "deadlock_recall": states["deadlock"] / (len(rows) - feasible),
    }


def sample(seed):
    rng = random.Random(seed)
    cases, leaders = [], []
    for index in range(BATCH):
        family = TRAIN[index % len(TRAIN)]
        ordering = rng.sample(range(3), 3)
        deadlock = (index // len(TRAIN)) % 2 == 0
        while True:
            menus = [{j for j in ordering if rng.random() < 0.5} for _ in range(2)]
            if all(menus) and (not menus[0] & menus[1]) == deadlock:
                cases.append(world(family, ordering, menus))
                leaders.append(rng.randrange(2))
                break
    return cases, leaders


def dump(path, content):
    path.write_text(json.dumps(content, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir()
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)
    locks = (Path(__file__), FAMILIES_PATH, FAMILIES_PATH.with_name("environment.py"), FAMILIES_PATH.with_name("evaluate.py"))
    dump(args.out / "launch.json", {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.out.resolve()), "gpu_uuids": [],
        "runtime": str(torch.__version__), "seed": SEED, "updates": UPDATES, "batch": BATCH, "limit": LIMIT,
        "question_reply_pair_cost": PAIR_COST, "counter_cost": COUNTER_COST,
        "hashes": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in locks},
    })
    policy = Policies()
    start = {k: v.detach().clone() for k, v in policy.state_dict().items()}
    optimizer = torch.optim.Adam(policy.parameters(), lr=0.02)
    test = exhaustive_worlds(TEST)
    test_cases = [case for case in test for _ in range(2)]
    test_leaders = [leader for _ in test for leader in (0, 1)]
    scores = {}
    with torch.no_grad():
        for mode in ("binary", "scripted", "greedy"):
            label = "before" if mode == "greedy" else mode
            rows = rollout(policy, test_cases, test_leaders, mode)[0]
            scores[label] = summarize(rows)
    dump(args.out / "baseline.json", scores)
    with (args.out / "updates.jsonl").open("x") as stream:
        for step in range(UPDATES):
            cases, leaders = sample(SEED + step + 1)
            rows, reward, ask_lp, response_lp, entropy = rollout(policy, cases, leaders, "sample")
            advantage = reward - reward.mean()
            loss = -(advantage * (ask_lp + response_lp) + 0.01 * entropy).mean()
            optimizer.zero_grad()
            loss.backward()
            ask_norm = nn.utils.clip_grad_norm_(policy.ask.parameters(), 1.0, error_if_nonfinite=True).item()
            offer_norm = nn.utils.clip_grad_norm_(policy.offer.parameters(), 1.0, error_if_nonfinite=True).item()
            optimizer.step()
            stream.write(json.dumps({"step": step + 1, "loss": loss.item(), "question_grad_norm": ask_norm,
                                     "response_grad_norm": offer_norm, **summarize(rows)}) + "\n")

    changed = [k for k, v in policy.state_dict().items() if not torch.equal(start[k], v)]
    assert any(k.startswith("ask") for k in changed) and any(k.startswith("offer") for k in changed)
    with torch.no_grad():
        traces = {}
        for mode in ("greedy", "counter_removed"):
            rows = rollout(policy, test_cases, test_leaders, mode)[0]
            key = "learned" if mode == "greedy" else mode
            scores[key] = summarize(rows)
            traces[key] = rows
    paired = Counter((a["final"] != "unresolved", b["final"] != "unresolved")
                     for a, b in zip(traces["learned"], traces["counter_removed"]))
    scores["paired_counter_effect"] = {str(k): v for k, v in paired.items()}
    dump(args.out / "scores.json", scores)
    dump(args.out / "policies.json", {k: v.tolist() for k, v in policy.state_dict().items()})
    dump(args.out / "selected_traces.json", {name: rows[:96] for name, rows in traces.items()})
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
