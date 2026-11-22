"""Share offer-routing experience across different evidence counts and widths."""
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import offer_refit as refit

offers, sp = refit.offers, refit.sp
TRAIN, TEST = 620171, 905071
START = "open_offer"


def features(obs):
    base, legal, peer, peer_unknown, first, _ = obs
    slots, _, unknown, exclusions, positives, _, ordinary_kind, _ = base
    return (legal, slots <= 2, min(unknown, 2), bool(exclusions), bool(positives),
            ordinary_kind, peer, peer_unknown, first)


class SharedPolicy(dict):
    def get(self, observation, default):
        return super().get(features(observation), default)


def fit(cohorts):
    anchors = [offers.measure(rows, START, {})[1] for rows in cohorts]
    current, policy, journal = sum(map(sp.fitness, anchors)), SharedPolicy(), []
    for _ in range(10):
        advantages, hits = defaultdict(float), Counter()
        for rows in cohorts:
            for row in rows:
                trace = []
                solved, end, checks = offers.rollout(row, START, policy, trace=trace)
                for obs, _, prefix, alternatives in trace:
                    for action, beginning in alternatives.items():
                        outcome, elapsed, remainder = offers.rollout(row, START, policy, beginning)
                        key = features(obs), action
                        advantages[key] += (
                            int(outcome) - int(solved) + sp.COST * (end - elapsed)
                            + sp.CHECK_COST * (checks - prefix - remainder - (action == offers.CHECK)))
                        hits[key] += 1
        candidates = sorted((-value, key) for key, value in advantages.items() if value > 0 and hits[key] >= 8)
        for _, (obs, action) in candidates:
            proposal = SharedPolicy({**policy, obs: action})
            counts = [offers.measure(rows, START, proposal)[1] for rows in cohorts]
            if any(new[label, "solved"] < old[label, "solved"]
                   for new, old in zip(counts, anchors, strict=True) for label in refit.CLASSES):
                continue
            reward = sum(map(sp.fitness, counts))
            if reward <= current:
                continue
            policy, current = proposal, reward
            journal.append({"observation": obs, "action": action, "visits": hits[obs, action],
                            "metrics": [sp.flatten(c) for c in counts]})
            break
        else:
            break
    return policy, {"initial": [sp.flatten(c) for c in anchors], "updates": journal}


def usage(rows, policy):
    hits, affected = Counter(), 0
    for row in rows:
        trace = []
        offers.rollout(row, START, policy, trace=trace)
        changed = False
        for obs, action, _, _ in trace:
            key = features(obs)
            if key in policy and action != offers.strategy(obs, START):
                hits[key] += 1
                changed = True
        affected += changed
    return {"changed_paths": affected, "override_calls": sum(hits.values()), "active_rules": len(hits)}


def evaluate():
    light = sp.panels((4, 5), TRAIN, 450, 2)
    heavy = sp.panels((4, 5), TRAIN+1, 450, 3)
    cohorts = (light + heavy, refit.drop_returns(light + heavy, TRAIN+2))
    policy, journal = fit(cohorts)
    wide = sp.panels((6, 7), TEST, 1000, 3)
    result = {"train": journal, "policy": [[k, v] for k, v in sorted(policy.items())]}
    for label, rows in (("reliable", wide), ("missing_returns", refit.drop_returns(wide, TEST+1))):
        result[label] = refit.compare(rows, policy)
        result[label]["usage"] = usage(rows, policy)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "replay"))
    p.add_argument("directory", type=Path)
    args = p.parse_args()
    files = (Path(__file__), Path(refit.__file__), Path(offers.__file__), Path(sp.__file__),
             sp.LOOKUP / "lookup.py", sp.LOOKUP.parent / "train.py", sp.LOOKUP.parents[1] / "environment.py")
    hashes = {str(f.resolve().relative_to(sp.HERE.parents[1])): offers.sha256(f.read_bytes()).hexdigest() for f in files}
    launch, readout = args.directory / "launch.json", args.directory / "results.json"
    if args.mode == "replay":
        assert json.loads(launch.read_text())["sha256"] == hashes
        assert json.loads(json.dumps(evaluate())) == json.loads(readout.read_text())
        print(json.dumps({"verified_hashes": len(hashes), "fit_and_heldout_exact": True}))
        return
    args.directory.mkdir()
    launch.write_text(json.dumps({"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
                                 "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
                                 "command": [sys.executable, *sys.argv], "run_directory": str(args.directory.resolve()),
                                 "sha256": hashes}, indent=2) + "\n")
    outcome = evaluate()
    readout.write_text(json.dumps(outcome, indent=2) + "\n")
    print("Accepted", len(outcome["train"]["updates"]), "updates")
    print({name: outcome[name]["usage"] for name in ("reliable", "missing_returns")})


if __name__ == "__main__":
    main()
