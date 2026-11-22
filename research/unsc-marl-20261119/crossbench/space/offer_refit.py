"""Learn proposal routing with separate certificate constraints by outcome class."""
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

import offer_policy as offers

sp = offers.sp
START = "open_offer"
CLASSES = ("agreement", "impasse")
TRAIN_SEED = 171741
TEST_SEED = 700817


def drop_returns(rows, seed):
    rng = random.Random(seed)
    return [(*row[:-1], tuple(mask if rng.random() >= .25 else 0 for mask in row[-1]))
            for row in rows]


def fit(clean):
    cohorts = (clean, drop_returns(clean, TRAIN_SEED + 1))
    anchor = [offers.measure(rows, START, {})[1] for rows in cohorts]
    policy, log = {}, []
    current = sum(map(sp.fitness, anchor))
    for _ in range(10):
        values, visits = defaultdict(float), Counter()
        for rows in cohorts:
            for row in rows:
                trace = []
                correct, finish, calls = offers.rollout(row, START, policy, trace=trace)
                for obs, _, prefix, alternatives in trace:
                    for picked, state in alternatives.items():
                        value, ending, count = offers.rollout(row, START, policy, state)
                        values[obs, picked] += (
                            int(value) - int(correct) + sp.COST * (finish - ending)
                            + sp.CHECK_COST * (calls - prefix - count - (picked == offers.CHECK)))
                        visits[obs, picked] += 1
        ranked = sorted((-v, key) for key, v in values.items() if v > 0 and visits[key] >= 8)
        for _, (obs, action) in ranked:
            candidate = {**policy, obs: action}
            outcomes = [offers.measure(rows, START, candidate)[1] for rows in cohorts]
            if any(new[k, "solved"] < old[k, "solved"]
                   for new, old in zip(outcomes, anchor, strict=True) for k in CLASSES):
                continue
            reward = sum(map(sp.fitness, outcomes))
            if reward <= current:
                continue
            policy, current = candidate, reward
            log.append({"obs": obs, "action": action, "visits": visits[obs, action],
                        "metrics": [sp.flatten(c) for c in outcomes]})
            break
        else:
            break
    return policy, {"initial": [sp.flatten(c) for c in anchor], "updates": log}


def compare(rows, learned):
    results = {}
    chosen, scores = offers.measure(rows, START, learned)
    results["learned"] = sp.flatten(scores)
    for script in ("verify_first", "offer_first", "open_offer"):
        baseline, scores = offers.measure(rows, script, {})
        paired = Counter()
        for row, old, new in zip(rows, baseline, chosen, strict=True):
            label = "agreement" if row[1][0] & row[1][1] else "impasse"
            paired[label, str(old[0]), str(new[0])] += 1
        results[script] = {"metrics": sp.flatten(scores), "pairs": sp.flatten(paired)}
    return results


def study():
    train = sp.panels((4, 5), TRAIN_SEED, 600, 2)
    policy, log = fit(train)
    holdout = sp.panels((6, 7), TEST_SEED, 1000, 3)
    return {"start": START, "training": log, "policy": [[k, v] for k, v in sorted(policy.items())],
            "reliable": compare(holdout, policy),
            "missing_returns": compare(drop_returns(holdout, TEST_SEED+1), policy)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "replay"))
    p.add_argument("directory", type=Path)
    args = p.parse_args()
    files = (Path(__file__).resolve(), Path(offers.__file__).resolve(), Path(sp.__file__).resolve(),
             sp.LOOKUP / "lookup.py", sp.LOOKUP.parent / "train.py", sp.LOOKUP.parents[1] / "environment.py")
    checksums = {str(f.relative_to(sp.HERE.parents[1])): offers.sha256(f.read_bytes()).hexdigest() for f in files}
    launch = args.directory / "launch.json"
    result = args.directory / "results.json"
    if args.mode == "replay":
        assert checksums == json.loads(launch.read_text())["sha256"]
        assert json.loads(json.dumps(study())) == json.loads(result.read_text())
        print(json.dumps({"verified_hashes": len(checksums), "fit_and_heldout_exact": True}, indent=2))
        return
    args.directory.mkdir()
    launch.write_text(json.dumps({"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
                                  "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
                                  "command": [sys.executable, *sys.argv], "run_directory": str(args.directory.resolve()),
                                  "sha256": checksums}, indent=2) + "\n")
    data = study()
    result.write_text(json.dumps(data, indent=2) + "\n")
    print("Accepted", len(data["training"]["updates"]), "updates")


if __name__ == "__main__":
    main()
