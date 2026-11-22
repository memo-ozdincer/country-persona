"""Construct synthetic cases that need two decisions on one matched fault tape."""
from collections import Counter
import json
import random
from unittest.mock import patch

import joint_coordination_curriculum as curriculum
import joint_deferral_fit as study

fit, paired = study.fit, study.paired
SEEDS = {"train": 842603,"dev": 155411,"heldout": 364163,"archive": fit.SEEDS["archive"]}
PANELS = {"train": ((6,7),800), "dev": ((6,7),600), "heldout": ((7,8),650)}
SEARCH_TOGGLES = 155


def four(item,terms,receipt):
    return [study.play(item,terms,receipt,lambda _:a,lambda _:b) for a,b in paired.OPTIONS]


def primary(routes):
    good, _, sequence = routes[3]
    if not good[0] or len(sequence)!=2 or not all(action[-1] for action in sequence):
        return None
    distinct = sequence[0][2]!=sequence[1][2]
    controls=sum(r[0][0] for r in routes[:3])
    return 3-controls, distinct


def improve(item,terms,receipt,routes,randomizer):
    rank = primary(routes)
    if rank is None or rank[0]==3:
        return item,routes,()
    best=(rank,item,routes,())
    row,tape=item
    choices=[(role,turn,index) for role,turn in tape for index in range(row[0])]
    randomizer.shuffle(choices)
    attempts=0
    # The flip component stays fixed. A mutation changes only which signed
    # proposition is lost at a particular role and slot, in every arm.
    for _ in range(2):
        origin=best
        for role,turn,index in choices:
            if attempts>=SEARCH_TOGGLES:
                break
            if (role,turn,index) in origin[3]:
                continue
            explored=origin[1][1].copy()
            drop,flip=explored[role,turn]
            explored[role,turn]=drop^(1<<index),flip
            candidate=row,explored
            branches=four(candidate,terms,receipt)
            attempts+=1
            strength=primary(branches)
            if strength is None or strength<=best[0]:
                continue
            best=strength,candidate,branches,(*origin[3],(role,turn,index))
            if strength==(3,True):
                return best[1:]
        if best==origin:
            break
    return best[1:]


def record(split):
    width,size=PANELS[split]
    with patch.object(fit,"SEEDS",new=SEEDS):
        panels=fit.synth(split,width,size,3)
    output={"counts":{},"items":[]}
    # Save one challenge per original synthetic row, even if multiple tapes
    # can be perturbed to make its paired paths jointly dependent.
    used=set()
    for name,rows in panels.items():
        if name=="clean":
            continue
        count=Counter()
        for i,(item,terms,receipt) in enumerate(rows):
            count["presentations"]+=1
            routes=four(item,terms,receipt)
            if primary(routes) is None:
                continue
            count["both_actions_and_initial_certificate"]+=1
            selected,alternatives,toggles=improve(item,terms,receipt,routes,random.Random(SEEDS[split]+37*i))
            if not curriculum.needs_both(alternatives):
                continue
            count["both_needed"]+=1
            world_key=(item[0],terms)
            if world_key in used:
                count["duplicates"]+=1
                continue
            used.add(world_key)
            distinct=primary(alternatives)[1]
            count["unique"]+=1
            count["distinct_role_coordination"]+=distinct
            output["items"].append({
                "base_index":i, "regime":name, "world_class":fit.world_label(item),
                "row": selected[0], "tape":[[list(k),v] for k,v in selected[1].items()],
                "terms":terms,"drop_bit_toggles":toggles,"actions_by_distinct_roles":distinct,
                "branches":alternatives,
            })
        output["counts"][name]=dict(count)
    return output


def run():
    return {"scope":"Procedurally selected synthetic challenge cases. No UN data enters construction. Tape perturbations are shared by all four branches, and the synthetic naming and observation protocol are unchanged. This is a challenge distribution, not a rate estimate.",
            "seeds":SEEDS,"search_budget_per_eligible_tape":SEARCH_TOGGLES,
            "splits":{split:record(split) for split in PANELS}}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
