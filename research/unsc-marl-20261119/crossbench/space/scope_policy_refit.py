"""Fit residual scope-routing actions against the strongest fixed schedule."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys

import scope_policy as routing

TRAIN_SEED = 76873
TEST_SEED = 54287


class Policy(dict):
    def get(self, observation, _):
        return super().get(observation, observation[6] != 0)


def fit(rows):
    policy = Policy()
    anchor, initial = routing.stats(rows, policy)
    history, current = [], initial
    for _ in range(8):
        effects = defaultdict(list)
        for row in rows:
            trace = []
            solved, finish, _ = routing.rollout(row, policy, trace=trace)
            for obs, chosen, alternate in trace:
                variant, end, _ = routing.rollout(row, policy, start=alternate)
                effects[obs, not chosen].append(int(variant) - int(solved) + routing.COST * (finish - end))
        ranked = sorted((-sum(values), obs, action)
                        for (obs, action), values in effects.items() if len(values) >= 5 and sum(values) > 0)
        for _, obs, action in ranked:
            proposal = Policy({**policy, obs: action})
            outcomes, measured = routing.stats(rows, proposal)
            if any(a and not b for a, b in zip(anchor, outcomes, strict=True)):
                continue
            if routing.fitness(measured) <= routing.fitness(current):
                continue
            policy, current = proposal, measured
            history.append({"observation": obs, "check": action, "visits": len(effects[obs, action]),
                            "scores": routing.flatten(current)})
            break
        else:
            break
    return policy, {"initial": routing.flatten(initial), "updates": history}


def evaluate():
    policy, log = fit(routing.panels((4, 5), TRAIN_SEED, 700, 2))
    holdout = routing.panels((6, 7), TEST_SEED, 1200, 3)
    rnd = random.Random(TEST_SEED + 1)
    degraded = [(*row[:-1], tuple(mask if rnd.random() >= .25 else 0 for mask in row[-1])) for row in holdout]
    result = {"train": log, "policy": [[obs, action] for obs, action in sorted(policy.items())]}
    for name, panel in (("heldout", holdout), ("unreturned_checks", degraded)):
        # The library's empty table is the initial weaker script. Include
        # the strong script explicitly to show its paired wins and losses.
        result[name] = routing.compare(panel, policy)
        strong, baseline = routing.stats(panel, Policy())
        new, _ = routing.stats(panel, policy)
        pairs = defaultdict(int)
        for row, a, b in zip(panel, strong, new, strict=True):
            tag = "agreement" if row[1][0] & row[1][1] else "impasse"
            pairs[tag, str(a), str(b)] += 1
        result[name]["strong_script"] = routing.flatten(baseline)
        result[name]["paired_vs_strong"] = routing.flatten(pairs)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "replay"))
    p.add_argument("output", type=Path)
    args = p.parse_args()
    files = (Path(__file__).resolve(), Path(routing.__file__).resolve(),
             routing.LOOKUP / "lookup.py", routing.LOOKUP.parent / "train.py",
             routing.LOOKUP.parents[1] / "environment.py")
    hashes = {str(f.relative_to(routing.HERE.parents[1])): sha256(f.read_bytes()).hexdigest() for f in files}
    if args.mode == "run":
        args.output.mkdir()
        launch = {"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
                  "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
                  "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()), "sha256": hashes}
        (args.output/"launch.json").write_text(json.dumps(launch, indent=2) + "\n")
        result = evaluate()
        (args.output/"results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"updates": len(result["train"]["updates"]), **{
            name: result[name]["paired_vs_strong"] for name in ("heldout", "unreturned_checks")}}, indent=2))
    else:
        assert json.loads((args.output/"launch.json").read_text())["sha256"] == hashes
        assert json.loads(json.dumps(evaluate())) == json.loads((args.output/"results.json").read_text())
        print(json.dumps({"verified_hashes": len(hashes), "fit_and_two_panels_exact": True}, indent=2))


if __name__ == "__main__":
    main()
