"""Counterfactual policy iteration for choosing a signed claim and next speaker."""
from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

from environment import claim, options_for, presentations, record, routing_prior, simulate, terminal
from learn import COST, write_json

TRAIN = (3, 4, 5)
EVAL = 6
MAX_UPDATES = 16


def actions(local, state, role, step, full):
    options = options_for(local, state, role, full)
    available = {}
    for group, pool in enumerate(options):
        if pool:
            bit = pool & -pool
            after = record(state, role, bit, bool(bit & local))
            for stay in (False, True):
                available[group, stay] = (bit, after, role if stay else 1-role)
    return available


def scripted(local, state, role, step, full, choices):
    selected = claim(local, state, role, step, full, flex=True)
    after = record(state, role, selected, bool(selected & local))
    stay = routing_prior(local, after, role, full) == role
    return next(k for k, (bit, _, _) in choices.items() if bit == selected and k[1] == stay)


def observation(local, state, role, step, full, baseline):
    groups = options_for(local, state, role, full)
    slots = full.bit_count()-step
    unresolved = (full & ~(state[1] | state[3])).bit_count()
    return (step == 0, local.bit_count() == 1, min(slots, 3), slots-unresolved,
            tuple(min(g.bit_count(), 2) for g in groups), baseline)


def committee(policy):
    def decide(world, state, role, step, full):
        local = world[role]
        choices = actions(local, state, role, step, full)
        if not choices:
            return None, {}, None
        default = scripted(local, state, role, step, full, choices)
        obs = observation(local, state, role, step, full, default)
        return obs, choices, policy.get(obs, default)
    return decide


def roll(n, world, state, choose):
    full, role = (1 << n)-1, 1
    trace = []
    for step in range(n):
        if terminal(state, full):
            break
        _, possibilities, action = choose(world, state, role, step, full)
        bit, state, next_role = possibilities[action] if possibilities else (0, state, 1-role)
        trace.append((role, bit, bool(bit & world[role]), next_role))
        role = next_role
    return terminal(state, full), trace


def measure(worlds, runner, traces=False):
    counts = Counter()
    rows = []
    agreement_mask = []
    for n, world, state in worlds:
        label = "agreement" if world[0] & world[1] else "impasse"
        cert, trace = runner(n, world, state)
        counts[label+"_total"] += 1
        counts[label+"_certificates"] += cert
        counts[label+"_slots"] += len(trace)
        if label == "agreement":
            agreement_mask.append(cert)
        if traces:
            rows.append((n, world, state, label, cert, trace))
    return dict(counts), agreement_mask, rows


def counterfactuals(worlds, policy):
    choose = committee(policy)
    totals = defaultdict(Counter)

    @lru_cache(maxsize=200000)
    def continuation(n, world, state, role, step):
        full = (1 << n)-1
        if step == n or terminal(state, full):
            return terminal(state, full), 0
        _, possibilities, action = choose(world, state, role, step, full)
        _, after, next_role = possibilities[action] if possibilities else (0, state, 1-role)
        cert, slots = continuation(n, world, after, next_role, step+1)
        return cert, slots+1

    for n, world, state in worlds:
        role, full = 1, (1 << n)-1
        for step in range(n):
            if terminal(state, full):
                break
            obs, possibilities, current = choose(world, state, role, step, full)
            if not possibilities:
                role = 1-role
                continue
            _, base_state, base_role = possibilities[current]
            cert, slots = continuation(n, world, base_state, base_role, step+1)
            for alt, (_, after, who) in possibilities.items():
                if alt == current:
                    continue
                other_cert, other_slots = continuation(n, world, after, who, step+1)
                stats = totals[obs, alt]
                stats["visits"] += 1
                stats["gains"] += int(other_cert and not cert)
                stats["losses"] += int(cert and not other_cert)
                stats["slots_saved"] += slots-other_slots
            state, role = base_state, base_role
    return totals


def value(stats):
    return sum(stats[g+"_certificates"] - COST*stats[g+"_slots"] for g in ("agreement", "impasse"))


def fit(training):
    initial, protected, _ = measure(training, lambda n,w,s: roll(n,w,s,committee({})))
    current = initial
    policy, updates = {}, []
    for _ in range(MAX_UPDATES):
        cf = counterfactuals(training, policy)
        ranked = sorted((-(v["gains"]-v["losses"]+COST*v["slots_saved"]), k) for k, v in cf.items())
        accepted = False
        for improvement, (obs, alt) in ranked:
            if improvement >= 0:
                break
            proposal = {**policy, obs: alt}
            if alt == obs[-1]:
                del proposal[obs]
            chooser = committee(proposal)
            stats, agreement, _ = measure(training, lambda n,w,s: roll(n,w,s,chooser))
            if (any(x and not y for x,y in zip(protected,agreement,strict=True)) or
                stats["impasse_certificates"] < current["impasse_certificates"] or value(stats) <= value(current)):
                continue
            policy, current = proposal, stats
            updates.append({"observation": obs, "action": alt, "counterfactual": dict(cf[obs,alt]),
                            "metrics": stats})
            accepted = True
            break
        if not accepted:
            break
    return policy, {"widths": TRAIN, "initial": initial, "final": current,
                    "updates": updates, "reward_slot_cost": COST}


def freeze(policy):
    return [{"observation": obs, "action": action} for obs, action in sorted(policy.items())]


def restore(rows):
    policy = {}
    for r in rows:
        *front, groups, default = r["observation"]
        policy[tuple(front)+(tuple(groups),tuple(default))] = tuple(r["action"])
    return policy


def main(output):
    output.mkdir()
    root = Path(__file__).resolve().parent
    write_json(output/"launch.json", {
        "host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
        "process_start": subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "command": [sys.executable,*sys.argv], "run_directory": str(output.resolve()),
        "source_hashes": {p: sha256((root/p).read_bytes()).hexdigest() for p in ("joint.py","learn.py","environment.py")},
        "training_widths": TRAIN, "heldout_width": EVAL,
    })
    training = [(n,w,s) for n in TRAIN for w,s in presentations(n)]
    policy, record = fit(training)
    write_json(output/"training.json", record)
    write_json(output/"policy.json", freeze(policy))
    # Do not inspect or construct width-six observations during policy fitting.
    heldout = [(EVAL,w,s) for w,s in presentations(EVAL)]
    initial, _, base_rows = measure(heldout, lambda n,w,s: simulate(n,w,s,"flexible"), traces=True)
    choose = committee(policy)
    learned, _, learned_rows = measure(heldout, lambda n,w,s: roll(n,w,s,choose), traces=True)
    changes = Counter()
    with (output/"paired.jsonl").open("x") as f:
        for original, fit_row in zip(base_rows,learned_rows,strict=True):
            width, world, opening, label, base_ok, base_trace = original
            assert original[:4] == fit_row[:4]
            _,_,_,_,fit_ok,fit_trace = fit_row
            changes[label,base_ok,fit_ok] += 1
            f.write(json.dumps([width, world, opening, label, base_ok, fit_ok, base_trace, fit_trace],
                               separators=(",",":"))+"\n")
    out = {"width": EVAL, "initial": initial, "learned": learned,
           "paired": {"/".join(map(str,k)):v for k,v in changes.items()}}
    write_json(output/"heldout.json", out)
    print(json.dumps({"update_count": len(record["updates"]), **out}, indent=2),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    main(parser.parse_args().output)
