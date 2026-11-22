"""Replay intent selection, local verification variants, and sourced traces."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import lookup
import timing
import proof_guard
from workshop_lookup import transfer

sys.path.insert(0, str(lookup.HERE.parent/"intent"))
import confirmation


def read(path):
    return json.loads(path.read_text())


def normalized(value):
    return json.loads(json.dumps(value))


def verify():
    work=lookup.HERE/"evidence"
    intent=lookup.HERE.parent/"intent/evidence"
    full=work/"fit"
    lookup_timing=work/"timing"
    for path, field in ((intent,"inputs"),(full,"sources"),(lookup_timing,"sha256")):
        metadata=read(path/"launch.json")
        assert all(lookup.digest(lookup.ROOT/name)==hash_ for name,hash_ in metadata[field].items())
    old=confirmation.guarded(confirmation.restore_full(read(lookup.ROOT/"evidence/joint/policy.json")))

    policy,replay=confirmation.fit(list(lookup.examples(confirmation.WIDTHS,confirmation.TRAIN_SEED)))
    assert normalized(replay)==read(intent/"training.json")
    assert normalized(confirmation.freeze(policy))==read(intent/"policy.json")
    for n in (6,7):
        assert confirmation.exercise(confirmation.sample(n),policy,old)==read(intent/f"heldout-{n}.json")

    rows=list(lookup.examples((3,4),lookup.TRAIN))
    bundle, journal=lookup.fit(rows)
    assert normalized(journal)==read(full/"training.json")
    assert normalized(lookup.freeze(bundle))==read(full/"policy.json")
    earlier, timing_journal=timing.fit(rows)
    assert normalized(timing_journal)==read(lookup_timing/"training.json")
    assert normalized(timing.freeze(earlier))==read(lookup_timing/"policy.json")

    for n in (5,6):
        held=list(lookup.examples((n,),lookup.TEST+n,stress=n==6))
        assert lookup.compare(held,bundle)==read(full/f"heldout-{n}.json")
        assert lookup.compare(held,earlier)==read(lookup_timing/f"exposed-{n}.json")
    assert lookup.compare(timing.fresh(),earlier)==read(lookup_timing/"fresh-7.json")
    assert proof_guard.audit(bundle)==read(full/"preservation.json")
    for confirm,file in ((False,"workshop.json"),(True,"workshop-confirmation.json")):
        assert transfer(full/"policy.json",confirm)==read(full/file)
    # Revealing one private sign changes only the requesting role's state.
    key,actions,default=lookup.choices((0,0,0,0),((0,2),(2,1)),0,0,2,1)
    after,local,actor,credit=lookup.transition(actions[(lookup.CHECK,True)],(1,2),
                                              ((0,2),(2,1)),0,1,(lookup.CHECK,True))
    assert after==(0,0,0,0) and local==((1,2),(2,1)) and actor==credit==0
    return {"confirmation_updates":len(replay["updates"]),"joint_lookup_updates":len(journal["updates"]),
            "earlier_lookup_updates":len(timing_journal["updates"]),"verified_un_traces":48,
            "sources":{p.name:sha256(p.read_bytes()).hexdigest() for p in
                       (lookup.HERE/"proof_guard.py",lookup.HERE/"workshop_lookup.py")}}


if __name__=="__main__":
    print(json.dumps(verify(),indent=2))
