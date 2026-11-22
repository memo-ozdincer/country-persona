"""Counterfactual MARL with an explicit proposal action and charged scope checks."""
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

import scope_policy as sp
from scope_policy_refit import Policy as PriorPolicy

WAIT, OFFER, CHECK = range(3)
TRAIN, TEST = 67182, 299431


def moves(row, current):
    width, _, local, _, _ = row
    state, role, step, credit = current
    base, may_check, _, ordinary = sp.move_options(width, state, local, role, step, credit)
    _, options, _ = sp.choices(state, local, role, step, width, 0)
    available = {WAIT: ordinary}
    if base[6] != 0:
        if may_check:
            available[CHECK] = None
        if (2, False) in options and options[2, False] != ordinary:
            available[OFFER] = options[2, False]
    peer = state[2 * (1 - role)]
    unknown_peer = peer & ~(local[role][0] | local[role][1] | state[1] | state[3])
    observation = (base, tuple(available), bool(peer), bool(unknown_peer), step == 0,
                   min((state[1] | state[3]).bit_count(), 2))
    return observation, available


def strategy(obs, script):
    available = obs[1]
    if OFFER in available and (script == "offer_first" or
                               (script == "open_offer" and obs[4])):
        return OFFER
    return CHECK if CHECK in available else WAIT


def transition(row, current, picked, actions):
    state, role, step, credit = current
    return sp.advance(row, state, role, step, credit, picked == CHECK, actions[picked])


def rollout(row, script, policy, current=None, trace=None):
    n, _, local, opening, _ = row
    current = current or (sp.opened(opening, local), 1, 0, 3)
    calls = 0
    while current[2] < n + 1 and not sp.terminal(current[0], (1 << n) - 1):
        obs, actions = moves(row, current)
        picked = policy.get(obs, strategy(obs, script))
        assert picked in actions
        if trace is not None and len(actions) > 1:
            trace.append((obs, picked, calls, {
                other: transition(row, current, other, actions) for other in actions if other != picked}))
        current = transition(row, current, picked, actions)
        calls += picked == CHECK
    return sp.terminal(current[0], (1 << n) - 1), current[2], calls


def measure(rows, script, policy):
    outcomes, counts = [], Counter()
    for row in rows:
        outcome = rollout(row, script, policy)
        outcomes.append(outcome)
        group = "agreement" if row[1][0] & row[1][1] else "impasse"
        counts[group, "paths"] += 1
        for field, value in zip(("solved", "slots", "checks"), outcome, strict=True):
            counts[group, field] += value
    return outcomes, counts


def fit(rows):
    anchors, original = measure(rows, "verify_first", {})
    policy, history = {}, []
    current = original
    for _ in range(8):
        estimate, visits = defaultdict(float), Counter()
        for row in rows:
            trace = []
            solved, end, calls = rollout(row, "verify_first", policy, trace=trace)
            for obs, picked, prior_checks, alternatives in trace:
                for action, beginning in alternatives.items():
                    success, finish, extra = rollout(row, "verify_first", policy, beginning)
                    new_checks = extra + prior_checks + (action == CHECK)
                    key = obs, action
                    estimate[key] += (int(success) - int(solved) + sp.COST * (end - finish)
                                      + sp.CHECK_COST * (calls - new_checks))
                    visits[key] += 1
        ranked = sorted((-value, key) for key, value in estimate.items() if value > 0 and visits[key] >= 6)
        for _, (obs, action) in ranked:
            candidate = {**policy, obs: action}
            outcomes, updated = measure(rows, "verify_first", candidate)
            if any(a[0] and not b[0] for a, b in zip(anchors, outcomes, strict=True)):
                continue
            if sp.fitness(updated) <= sp.fitness(current):
                continue
            policy, current = candidate, updated
            history.append({"obs": obs, "action": action, "visits": visits[obs, action],
                            "metrics": sp.flatten(updated)})
            break
        else:
            break
    return policy, {"initial": sp.flatten(original), "updates": history}


def report(rows, policy):
    learned, metric = measure(rows, "verify_first", policy)
    result = {"learned": sp.flatten(metric)}
    for script in ("verify_first", "offer_first", "open_offer"):
        baseline, counts = measure(rows, script, {})
        paired = Counter()
        for row, a, b in zip(rows, baseline, learned, strict=True):
            tag = "agreement" if row[1][0] & row[1][1] else "impasse"
            paired[tag, str(a[0]), str(b[0])] += 1
        result[script] = {"metrics": sp.flatten(counts), "learned_pairs": sp.flatten(paired)}
    return result


def study():
    train = sp.panels((4, 5), TRAIN, 600, 2)
    _, baseline = measure(train, "verify_first", {})
    assert baseline == sp.stats(train, PriorPolicy())[1]
    policy, learning = fit(train)
    heldout = sp.panels((6, 7), TEST, 1000, 3)
    rng = random.Random(TEST + 1)
    incomplete = [(*r[:-1], tuple(s if rng.random() > .25 else 0 for s in r[-1])) for r in heldout]
    return {"training": learning, "policy": [[obs, action] for obs, action in sorted(policy.items())],
            "reliable": report(heldout, policy), "missing_returns": report(incomplete, policy)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "replay"))
    p.add_argument("output", type=Path)
    args = p.parse_args()
    files = (Path(__file__).resolve(), Path(sp.__file__).resolve(), sp.HERE / "scope_policy_refit.py",
             sp.LOOKUP / "lookup.py", sp.LOOKUP.parent / "train.py", sp.LOOKUP.parents[1] / "environment.py")
    hashes = {str(f.relative_to(sp.HERE.parents[1])): sha256(f.read_bytes()).hexdigest() for f in files}
    results = args.output / "results.json"
    launch = args.output / "launch.json"
    if args.mode == "replay":
        assert json.loads(launch.read_text())["sha256"] == hashes
        assert json.loads(json.dumps(study())) == json.loads(results.read_text())
        print(json.dumps({"verified_hashes": len(hashes), "fit_and_heldout_exact": True}, indent=2))
        return
    args.output.mkdir()
    launch.write_text(json.dumps({"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
                                  "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
                                  "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
                                  "sha256": hashes}, indent=2) + "\n")
    result = study()
    results.write_text(json.dumps(result, indent=2) + "\n")
    print("Accepted", len(result["training"]["updates"]), "updates")


if __name__ == "__main__":
    main()
