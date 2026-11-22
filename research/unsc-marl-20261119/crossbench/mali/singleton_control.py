"""Test whether an eligible singleton removes the compound request's proof gap."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import joint_bound
import joint_transfer as study

group=study.group
MULTIPLE_ONLY=group.optional_set


def allow_singleton(item,state):
    obs,moves,routine=MULTIPLE_ONLY(item,state)
    width,_,local,*_=item[0]
    public,actor,turn,credit=state
    if obs[-2]!=1 or not credit&group.policy.policy.CREDIT or turn+2>width+1 or obs[6]==0:
        return obs,moves,routine
    peer=1-actor
    target=local[actor][0]&~(public[1]|public[3]|public[2*peer])
    assert target.bit_count()==1
    moves[group.OFFER_SET]=target
    return (tuple(moves),*obs[1:]),moves,routine


def compare(metrics):
    case=study.mali.load(study.mali.CASE)
    menus=study.mali.audited_menus(case)
    frozen=group.decode(study.mali.load(study.TRAINED)["training"])
    values={"conditions":{}}
    with patch.object(group,"optional_set",new=allow_singleton):
        for name in ("authored","archived","stable","pooled"):
            condition=metrics["conditions"][name]
            values["conditions"][name]={**condition,**study.certify(
                case,menus,condition["package"],condition["scope"],frozen)}
        bound=joint_bound.measure(values)
    return {"scope":"Same Mali paths and actions plus singleton questions. Both fixed and frozen learned schedules share the new action. No fit.",
            "bound":bound,"conditions":values["conditions"]}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics",type=Path)
    args=parser.parse_args()
    result=compare(study.mali.load(args.metrics))
    result["input_sha256"]=sha256(args.metrics.read_bytes()).hexdigest()
    print(json.dumps(result,indent=2))
