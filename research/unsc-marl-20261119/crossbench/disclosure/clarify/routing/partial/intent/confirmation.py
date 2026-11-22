"""Learn a confirmation policy for a publicly declared agreement-only task."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PARTIAL = HERE.parent
sys.path.insert(0, str(PARTIAL))
from train import (
    COST, ROOT, TEST_SEED, examples, full_policy, guarded, label, measure, moves,
    opened, record, replay, restore_full, terminal, flat,
)

WIDTHS = (3, 4)
MAX_UPDATES = 20
TRAIN_SEED = 67144
FRESH_SEED = 88104
SAMPLE_PER_CLASS = 3000


def decision(local, state, role, turn, width):
    full = (1 << width) - 1
    buckets, options = moves(local[role], state, role, full)
    group = next((g for g in (0, 2, 3, 1) if buckets[g]), -1)
    default = (group, False)
    # Exclusions may be useful, but the confirmation baseline gives its
    # counterpart a chance to offer a package after every disclosure.
    peer_accepts = state[2 * (1 - role)]
    key = (
        min(width - turn, 3),
        tuple(min(bits.bit_count(), 2) for bits in buckets),
        min(peer_accepts.bit_count(), 2),
        min((full & ~(state[1] | state[3])).bit_count(), 3),
        tuple(options),
        default,
    )
    return key, options, default


def roll(local, state, role, turn, width, policy):
    full = (1 << width) - 1
    for step in range(turn, width):
        if terminal(state, full):
            return bool(state[0] & state[2]), step - turn
        key, options, default = decision(local, state, role, step, width)
        _, _, state, role = options[policy.get(key, default)]
    return bool(state[0] & state[2]), width - turn


def confirm(row, policy):
    width, _, local, opening = row
    return roll(local, opened(opening, local), 1, 0, width, policy)


def effects(rows, policy):
    results = defaultdict(Counter)
    for width, _, local, opening in rows:
        state, role, full = opened(opening, local), 1, (1 << width) - 1
        for step in range(width):
            if terminal(state, full):
                break
            key, options, default = decision(local, state, role, step, width)
            choice = policy.get(key, default)
            _, _, after, recipient = options[choice]
            success, slots = roll(local, after, recipient, step + 1, width, policy)
            for action, (_, _, alternative, next_role) in options.items():
                if action == choice:
                    continue
                cert, cost = roll(local, alternative, next_role, step + 1, width, policy)
                stats = results[key, action]
                stats["visits"] += 1
                stats["gains"] += cert and not success
                stats["losses"] += success and not cert
                stats["slots_saved"] += slots - cost
            role, state = recipient, after
    return results


def metrics(rows, actor):
    counts, flags = measure(rows, actor)
    return flat(counts), flags


def reward(stats):
    return stats["agreement/certificates"] - COST * (
        stats["agreement/slots"] + stats["impasse/slots"]
    )


def fit(rows):
    incumbent = {}
    initial, protected = metrics(rows, lambda r: confirm(r, incumbent))
    current = initial
    updates = []
    for _ in range(MAX_UPDATES):
        stats = effects(rows, incumbent)
        ranked = sorted(
            (-(v["gains"] - v["losses"] + COST * v["slots_saved"]), key)
            for key, v in stats.items() if v["visits"] >= 3
        )
        for rank, (obs, action) in ranked:
            if rank >= 0:
                break
            changed = {**incumbent, obs: action}
            if action == obs[-1]:
                changed.pop(obs)
            sample, choices = metrics(rows, lambda r: confirm(r, changed))
            if any(a and not b for a, b in zip(protected, choices, strict=True)):
                continue
            if sample["agreement/certificates"] < current["agreement/certificates"] or reward(sample) <= reward(current):
                continue
            incumbent, current = changed, sample
            updates.append({"observation": obs, "action": action,
                            "training_counterfactual": dict(stats[obs, action]), "metrics": sample})
            break
        else:
            break
        if rank >= 0:
            break
    return incumbent, {"initial": initial, "final": current, "updates": updates}


def freeze(policy):
    return [[k, action] for k, action in sorted(policy.items())]


def restore(data):
    return {(key[0], tuple(key[1]), key[2], key[3], tuple(map(tuple, key[4])), tuple(key[5])): tuple(value)
            for key, value in data}


def sample(width):
    rng = random.Random(FRESH_SEED + width)
    cells = {"agreement": [], "impasse": []}
    counts = Counter()
    for entry in examples((width,), FRESH_SEED + width, stress=True):
        cls = label(entry)
        counts[cls] += 1
        if len(cells[cls]) < SAMPLE_PER_CLASS:
            cells[cls].append(entry)
        else:
            index = rng.randrange(counts[cls])
            if index < SAMPLE_PER_CLASS:
                cells[cls][index] = entry
    return cells["agreement"] + cells["impasse"]


def exercise(rows, policy, old):
    baseline = lambda row: confirm(row, {})
    learner = lambda row: confirm(row, policy)
    established = lambda row: full_policy(row, old)
    methods = {
       "confirmation_script": baseline,
       "confirmation_learned": learner,
       "mixed_script": lambda row: replay(row, {}),
       "mixed_established": established,
       # Policies can only switch on the explicitly announced task.
       # Every hidden world is exercised under each announcement.
       "adaptive_confirmation": learner,
       "adaptive_mixed": established,
    }
    output, results = {}, {}
    for name, evaluate in methods.items():
        output[name], results[name] = metrics(rows, evaluate)
    paired = Counter()
    for row, before, after in zip(rows, results["confirmation_script"],
                                  results["confirmation_learned"], strict=True):
        paired[label(row), str(before), str(after)] += 1
    return {"metrics": output, "paired_confirmation": flat(paired)}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save(path, doc):
    path.write_text(json.dumps(doc, indent=2) + "\n")


def main(output):
    output.mkdir()
    oracle_policy = ROOT / "evidence/joint/policy.json"
    paths = [Path(__file__).resolve(), PARTIAL / "train.py", oracle_policy,
             *(ROOT / n for n in ("environment.py", "guard.py", "joint.py", "learn.py"))]
    save(output / "launch.json", {
        "host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                 text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(output.resolve()),
        "inputs": {str(p.relative_to(ROOT)): digest(p) for p in paths},
        "train_widths": WIDTHS, "train_seed": TRAIN_SEED, "test_widths": [6, 7], "test_seed": FRESH_SEED,
        "sample_per_class": SAMPLE_PER_CLASS,
    })
    train = list(examples(WIDTHS, TRAIN_SEED))
    policy, journal = fit(train)
    save(output / "training.json", journal)
    save(output / "policy.json", freeze(policy))
    print(f"Accepted updates: {len(journal['updates'])}", flush=True)
    old = guarded(restore_full(json.loads(oracle_policy.read_text())))
    for n in (6, 7):
        scored = exercise(sample(n), policy, old)
        save(output / f"heldout-{n}.json", scored)
        print(n, scored["metrics"], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    main(p.parse_args().output)
