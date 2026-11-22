"""Transfer a trained local policy with a certificate-budget guard."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import socket
import subprocess
import sys

from environment import presentations, simulate
from joint import committee, measure, restore, roll
from learn import write_json

DEV, TEST = 6, 7


def guarded(policy):
    choose = committee(policy)

    def decide(world, state, role, step, full):
        obs, choices, action = choose(world, state, role, step, full)
        if obs is None:
            return obs, choices, action
        base = obs[-1]
        slots = full.bit_count()-step
        not_excluded = (full & ~(state[1] | state[3])).bit_count()
        if (base[0] in (1, 3) and action[0] == 2 and slots <= not_excluded):
            # A non-matching acceptance cannot eliminate any package. This
            # change would make an impasse certificate impossible if it is
            # still reachable. Keep the original negative disclosure here.
            action = base
        return obs, choices, action
    return decide


def compare(n, policy, output):
    runners = {
        "script": lambda n,w,s: simulate(n,w,s,"flexible"),
        "learned": lambda n,w,s: roll(n,w,s,committee(policy)),
        "guarded": lambda n,w,s: roll(n,w,s,guarded(policy)),
    }
    worlds = [(n,w,s) for w,s in presentations(n)]
    summary, rows = {}, {}
    for name, runner in runners.items():
        summary[name], _, rows[name] = measure(worlds, runner, traces=True)
    filename = output / f"paired-{n}.jsonl"
    paired = Counter()
    with filename.open("x") as out:
        for base, learned, rule in zip(*rows.values(), strict=True):
            assert base[:4] == learned[:4] == rule[:4]
            label = base[3]
            paired[(label, base[4], learned[4], rule[4])] += 1
            out.write(json.dumps([*base[:4], *base[4:], *learned[4:], *rule[4:]],
                                 separators=(",", ":"))+"\n")
    return {"width": n, "metrics": summary,
            "paired": {"/".join(map(str,k)):v for k,v in paired.items()},
            "trace_sha256": sha256(filename.read_bytes()).hexdigest()}


def main(policy_path, output):
    output.mkdir()
    root = Path(__file__).resolve().parent
    source = policy_path.read_bytes()
    write_json(output/"launch.json", {
        "host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
        "process_start": subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
        "command": [sys.executable,*sys.argv], "run_directory": str(output.resolve()),
        "source_hashes": {p: sha256((root/p).read_bytes()).hexdigest()
                          for p in ("guard.py","joint.py","learn.py","environment.py")},
        "policy_path":str(policy_path.resolve()),"policy_sha256":sha256(source).hexdigest(),
        "development":DEV,"fresh_test":TEST, "updates":0,
    })
    policy = restore(json.loads(source))
    for width in (DEV, TEST):
        result = compare(width, policy, output)
        write_json(output/f"metrics-{width}.json", result)
        print(json.dumps(result, indent=2),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.policy, args.output)
