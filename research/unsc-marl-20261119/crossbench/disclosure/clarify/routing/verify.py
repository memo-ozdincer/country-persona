"""Replay source locks, trained rules, and every held-out action."""
from collections import Counter
from hashlib import sha256
import argparse
import json
from pathlib import Path

from environment import presentations, simulate
from guard import guarded
from joint import committee, fit, freeze, restore, roll


def read(path):
    return json.loads(path.read_text())


def locks(path):
    meta = read(path / "launch.json")
    root = Path(__file__).resolve().parent
    assert all(sha256((root/name).read_bytes()).hexdigest() == digest
               for name, digest in meta["source_hashes"].items())
    return meta


def verify(joint_run, guard_run):
    joint_launch, launch = locks(joint_run), locks(guard_run)
    policy_path = joint_run / "policy.json"
    assert sha256(policy_path.read_bytes()).hexdigest() == launch["policy_sha256"]
    expected = read(policy_path)
    policies = restore(expected)
    training = [(n,w,s) for n in joint_launch["training_widths"] for w,s in presentations(n)]
    retrained, logs = fit(training)
    assert json.loads(json.dumps(freeze(retrained))) == expected
    assert json.loads(json.dumps(logs)) == read(joint_run / "training.json")

    def is_keep_only(rule):
        obs = rule["observation"]
        return rule["action"][0] == obs[-1][0] and rule["action"][1] and not obs[-1][1]

    keep = committee(restore([p for p in expected if is_keep_only(p)]))
    actor, shield = committee(policies), guarded(policies)
    verified = {}
    for n in (launch["development"], launch["fresh_test"]):
        paired = Counter()
        candidate_file = guard_run / f"paired-{n}.jsonl"
        evidence = read(guard_run / f"metrics-{n}.json")
        assert sha256(candidate_file.read_bytes()).hexdigest() == evidence["trace_sha256"]
        with candidate_file.open() as rows:
            for (world, opening), raw in zip(presentations(n), rows, strict=True):
                label = "agreement" if world[0] & world[1] else "impasse"
                base = simulate(n, world, opening, "flexible")
                fitted = roll(n, world, opening, actor)
                helped = roll(n, world, opening, shield)
                exact = json.dumps([n, world, opening, label, *base, *fitted, *helped], separators=(",", ":"))
                assert exact+"\n" == raw
                assert roll(n, world, opening, keep) == helped
                paired[label,base[0],fitted[0],helped[0]] += 1
        verified[n] = {"cases": sum(paired.values()), "guard_reproduced_by_keep_only_rule": True,
                       "sha256": evidence["trace_sha256"]}
        assert {"/".join(map(str,k)):v for k,v in paired.items()} == evidence["paired"]
    return {"accepted_policy_updates_replayed": len(logs["updates"]), "evaluation": verified}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("joint", type=Path)
    p.add_argument("guard", type=Path)
    args = p.parse_args()
    print(json.dumps(verify(args.joint,args.guard),indent=2))
