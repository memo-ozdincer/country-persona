"""Shared tabular policy iteration for multi-agent next-speaker selection.

Collect both action returns in exact self-play on widths 3 and 4, then
accept switches that improve training return while retaining certificates.
Width 5 is evaluation-only and is not involved in accepting any switch.
"""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import argparse
import os
import socket
import subprocess
import sys

from environment import claim, control, options_for, presentations, record, routing_prior, simulate, terminal

TRAIN = (3, 4)
EVAL = 5
COST = 0.025


def observation(local, post, role, full, step, bit):
    groups = options_for(local, post, role, full)
    return (
        local.bit_count() == 1,
        step == 0,
        min(full.bit_count()-step-1, 3),
        bool(bit & local),
        bool(groups[0]),
        bool(groups[2]),
        bool(groups[3]),
        min((full & ~(post[1] | post[3])).bit_count(), 3),
    )


def router(flips):
    def choose(local, post, role, full, step, bit):
        prior = routing_prior(local, post, role, full)
        return 1-prior if observation(local, post, role, full, step, bit) in flips else prior
    return choose


def continuation(n, world, state, role, start, route):
    full = (1 << n) - 1
    slots = 0
    for step in range(start, n):
        if terminal(state, full):
            break
        local = world[role]
        bit = claim(local, state, role, step, full, flex=True)
        if bit:
            state = record(state, role, bit, bool(bit & local))
            role = route(local, state, role, full, step, bit)
        else:
            role = 1-role
        slots += 1
    return terminal(state, full), slots


def explore(training, flips):
    route = router(flips)
    samples = defaultdict(Counter)
    for n, world, state in training:
        role = 1
        full = (1 << n) - 1
        for step in range(n-1):
            if terminal(state, full):
                break
            local = world[role]
            bit = claim(local, state, role, step, full, flex=True)
            if not bit:
                role = 1-role
                continue
            state = record(state, role, bit, bool(bit & local))
            if terminal(state, full):
                break
            next_role = route(local, state, role, full, step, bit)
            key = observation(local, state, role, full, step, bit)
            result = continuation(n, world, state, next_role, step+1, route)
            other = continuation(n, world, state, 1-next_role, step+1, route)
            samples[key]["visits"] += 1
            samples[key]["lost"] += int(result[0] and not other[0])
            samples[key]["gained"] += int(other[0] and not result[0])
            samples[key]["slots_saved"] += result[1] - other[1]
            role = next_role
    return samples


def measure(worlds, mode, route):
    counts = Counter()
    traces = []
    for n, world, opening in worlds:
        outcome = "agreement" if world[0] & world[1] else "impasse"
        ok, steps = simulate(n, world, opening, mode, route)
        counts[f"{outcome}_total"] += 1
        counts[f"{outcome}_certificates"] += ok
        counts[f"{outcome}_slots"] += len(steps)
        traces.append({"n": n, "menus": world, "opening": opening, "outcome": outcome,
                       "certified": ok, "turns": steps})
    return dict(counts), traces


def fit(output):
    training = [(n, w, s) for n in TRAIN for w, s in presentations(n)]
    flips = set()
    baseline, _ = measure(training, "flexible", router(flips))
    current = baseline
    history = []
    while True:
        samples = explore(training, flips)
        candidates = sorted(((-v["slots_saved"], k) for k, v in samples.items()
                             if v["lost"] == 0 and v["slots_saved"] > 0))
        accepted = False
        for _, key in candidates:
            proposal = flips ^ {key}
            stats, _ = measure(training, "flexible", router(proposal))
            same_coverage = all(stats[f"{c}_certificates"] == baseline[f"{c}_certificates"]
                                for c in ("agreement", "impasse"))
            saved = sum(current[f"{c}_slots"]-stats[f"{c}_slots"] for c in ("agreement", "impasse"))
            if not same_coverage or saved <= 0:
                continue
            flips = proposal
            current = stats
            accepted = True
            history.append({"observation": key, "sampled_counterfactual": dict(samples[key]),
                            "global_slots_saved": saved, "train_metrics": stats})
            break
        if not accepted:
            break
    return flips, {"training_widths": TRAIN, "training_baseline": baseline, "training_final": current,
                   "updates": history, "trains_on_heldout": False, "certificate_reward": 1.0, "slot_cost": COST}


def write_json(file, content):
    file.write_text(json.dumps(content, indent=2) + "\n")


def main(output):
    output.mkdir()
    root = Path(__file__).resolve().parent
    locks = {p.name: sha256(p.read_bytes()).hexdigest() for p in (root / "learn.py", root / "environment.py")}
    write_json(output / "launch.json", {"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU",
               "gpu_uuids": [], "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p",
               str(os.getpid())], text=True).strip(), "command": [sys.executable, *sys.argv],
               "run_directory": str(output.resolve()), "source_hashes": locks,
               "eval_width": EVAL, "eval_budget": EVAL})
    flips, training = fit(output)
    write_json(output / "policy.json", {"flipped_observations": sorted(flips)})
    write_json(output / "training.json", training)
    # Materialize the holdout only after the policy is fixed and saved.
    worlds = [(EVAL, world, opening) for world, opening in presentations(EVAL)]
    summary = {}
    for name, mode, flips_now in (("alternating", "alternating", set()),
                                 ("matched_alternating", "flexible_claims_alternating", set()),
                                 ("scripted_flexible", "flexible", set()),
                                 ("learned_flexible", "flexible", flips)):
        summary[name], traces = measure(worlds, mode, router(flips_now))
        with (output / f"{name}.jsonl").open("x") as out:
            for row in traces:
                out.write(json.dumps(row, separators=(",", ":")) + "\n")
    summary["development_controls"] = [control(n, include_capacity=True) for n in TRAIN]
    write_json(output / "heldout.json", summary)
    print(json.dumps({"updates": len(training["updates"]), "holdout": summary}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    main(parser.parse_args().output)
