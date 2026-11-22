"""Replay fitting, sampled heldout comparisons, and the UN task transfers."""
import argparse
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

import train
import preserve
import task_replay
from environment import terminal, record


def load(path):
    return json.loads(path.read_text())


def normalize(payload):
    return json.loads(json.dumps(payload))


def exact(row):
    """Enumerate every truthful local action with future knowledge of both menus."""
    width, _, local, first = row
    full=(1 << width)-1

    @lru_cache(maxsize=None)
    def reachable(state, role, remaining):
        if terminal(state,full):
            return True
        if not remaining:
            return False
        yes, no=local[role]
        known=(yes|no) & ~(state[1]|state[3]|state[2*role])
        if not known:
            return reachable(state,1-role,remaining-1)
        for i in range(width):
            bit=1<<i
            if known&bit:
                sign=bool(yes&bit)
                after=record(state,role,bit,sign)
                choices=(1-role,) if sign else (role,1-role)
                if any(reachable(after,nxt,remaining-1) for nxt in choices):
                    return True
        return False

    return reachable(train.opened(first,local),1,width)


def verify(location):
    evidence,guards = location/"training", location/"guards"
    closures = {}
    for file in (evidence/"launch.json",guards/"launch.json"):
        for name,digest in load(file)["sha256"].items():
            assert sha256((train.ROOT/name).read_bytes()).hexdigest()==digest
            closures[name]=digest
    role_policy=evidence/"policy.json"
    assert sha256(role_policy.read_bytes()).hexdigest()==load(guards/"launch.json")["policy_sha256"]
    fitted, journal=train.fit(list(train.examples(train.TRAIN_WIDTHS,train.TRAIN_SEED)))
    assert normalize(train.freeze(fitted))==load(role_policy)
    assert normalize(journal)==load(evidence/"training.json")
    old=train.guarded(train.restore_full(load(train.ROOT/"evidence/joint/policy.json")))
    for width in train.TEST_WIDTHS:
        cohort=list(train.examples((width,),train.TEST_SEED+width,stress=width==6))
        assert train.compare(cohort,fitted,old)==load(evidence/f"heldout-{width}.json")
        assert preserve.report(cohort,fitted)==load(guards/f"exposed-{width}.json")
    assert preserve.report(preserve.fresh(),fitted)==load(guards/"fresh-7.json")

    finite=list(train.examples((3,4),12723))
    assert all(exact(row)==train.evidence_available(row) for row in finite)

    files, hashes=task_replay.sources()
    manifests={k:load(p) for k,p in files.items()}
    for adjusted,name in ((False,"tasks.json"),(True,"tasks-guarded.json")):
        rebuilt={"input_sha256":hashes,"outcomes":task_replay.compare(fitted,manifests,adjusted)}
        assert rebuilt==load(location/name)
    return {"training_updates":len(journal["updates"]),"certificate_ceiling_exact_cases":len(finite),
            "fresh_presentations":2*preserve.FRESH_PER_CLASS,"task_source_hashes":hashes,
            "training_and_evaluation_hashes":closures}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.evidence),indent=2))
