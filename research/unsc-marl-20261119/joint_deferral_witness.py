"""Expose the exact action sequence of cases requiring both interventions."""
import json
from unittest.mock import patch

import joint_deferral_fit as joint


def witness(item, terms, receipt, actions):
    events=[]
    original=joint.floor.play

    def capture(*args, **kwargs):
        return original(*args,**kwargs,events=events)

    with patch.object(joint.floor,"play",new=capture):
        outcome,views,actions_taken=joint.play(
            item,terms,receipt,lambda _:actions[0],lambda _:actions[1])
    return {"result":outcome,"choices":actions_taken,"views":views,"transcript":events}


def inspect():
    reviews={}
    with patch.object(joint.fit,"SEEDS",new=joint.SEEDS):
        for family,panels in joint.core.audit.samples():
            if family=="fresh_synthetic":
                continue
            for regime,rows in panels.items():
                for i,(item,terms,receipt) in enumerate(rows):
                    fixed=[joint.play(item,terms,receipt,lambda _:a,lambda _:b)[0]
                           for a,b in joint.paired.OPTIONS]
                    if not fixed[3][0] or any(record[0] for record in fixed[:3]):
                        continue
                    traces=[witness(item,terms,receipt,actions) for actions in joint.paired.OPTIONS]
                    assert [tuple(run["result"]) for run in traces]==fixed
                    choices=traces[-1]["choices"]
                    assert len(choices)==2 and all(e[-1] for e in choices)
                    reviews[f"{family}/{regime}/{i}"]={
                        "world":joint.fit.world_label(item),"terms":terms,
                        "actions_owned_by_distinct_roles":choices[0][2]!=choices[1][2],
                        "arms":dict(zip(("fixed","handoff_only","query_only","both"),traces,strict=True)),
                    }
    return reviews


if __name__=="__main__":
    print(json.dumps(inspect(),indent=2))
