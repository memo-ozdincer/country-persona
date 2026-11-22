"""Reproduce the check-or-defer fit, holdouts, stress and workshop replay."""
from hashlib import sha256
import json
from pathlib import Path

import deferral
from check_failure import evaluate as check_failure, replay as unreliable
from deferral_cases import evaluate as workshops
from lookup import play as prior_play


def read(path):
    return json.loads(path.read_text())


def canonical(value):
    return json.loads(json.dumps(value))


def verify():
    p=deferral.HERE/"evidence/deferral"
    meta=read(p/"launch.json")
    assert all(deferral.digest(deferral.ROOT/name)==value for name,value in meta["sha256"].items())
    rows=list(deferral.train_set())
    assert all(prior_play(row,{})==deferral.play(row,{}) for row in rows)
    learned,log=deferral.fit(rows)
    assert canonical(log)==read(p/"training.json")
    assert canonical(deferral.freeze(learned))==read(p/"policy.json")
    assert learned==deferral.restore(read(p/"policy.json"))
    for w in (5,6):
        groups=list(deferral.examples((w,),deferral.TEST_SEED+w,stress=w==6))
        assert deferral.compare(groups,learned)==read(p/f"width-{w}.json")
    assert deferral.compare(deferral.fresh(),learned)==read(p/"fresh-7.json")
    assert check_failure(learned)==read(p/"unreturned-checks.json")
    assert workshops(learned)==read(p/"workshops.json")
    for n,private,known,opening in rows[:144]:
        a,b,c=deferral.play((n,private,known,opening),learned)
        full=(1<<n)-1
        assert unreliable((n,private,known,opening),learned,(full,full))==(a,b,c,0)
    artifacts=("training.json","policy.json","width-5.json","width-6.json","fresh-7.json",
               "unreturned-checks.json","workshops.json")
    return {"training_presentations":len(rows),"accepted_changes":len(log["updates"]),
            "reliable_and_unreliable_arms_verified":True,
            "artifact_sha256":{name:sha256((p/name).read_bytes()).hexdigest() for name in artifacts}}


if __name__=="__main__":
    print(json.dumps(verify(),indent=2))
