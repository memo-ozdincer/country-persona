"""Search from any synthetic trace that exposes both local decisions."""
from collections import Counter
import json
import random
from unittest.mock import patch

import coordination_challenge as initial

fit, curriculum = initial.fit, initial.curriculum
SEEDS = {"train": 438821,"dev": 202817,"heldout": 359149,"archive": fit.SEEDS["archive"]}
ROWS = {"train": ((7,8),850),"dev": ((7,8),630),"heldout": ((7,8),680)}
LIMIT = 260


def grade(paths):
    outcome, _, actions = paths[3]
    if len(actions)!=2:
        return (-1,False,False)
    distinct=actions[0][2]!=actions[1][2]
    solo_wins=sum(bool(v[0][0]) for v in paths[:3])
    return 3-solo_wins if outcome[0] else -1, outcome[0], distinct


def search(item, terms, receipt, original, seed):
    width=item[0][0]
    moves=[(r,t,i,k) for r,t in item[1] for i in range(width) for k in (0,1)]
    random.Random(seed).shuffle(moves)
    best=grade(original),item,original,()
    for turn in range(2):
        anchor=best
        for r,t,i,k in moves[turn*(LIMIT//2):(turn+1)*(LIMIT//2)]:
            if (r,t,i,k) in anchor[3]:
                continue
            tape=anchor[1][1].copy()
            flags=list(tape[r,t])
            flags[k]^=1<<i
            tape[r,t]=tuple(flags)
            alternative=item[0],tape
            paths=initial.four(alternative,terms,receipt)
            rank=grade(paths)
            if rank>best[0]:
                best=rank,alternative,paths,(*anchor[3],(r,t,i,k))
                if rank==(3,True,True):
                    return best[1:]
    return best[1:]


def make(split):
    widths,size=ROWS[split]
    with patch.object(fit,"SEEDS",new=SEEDS):
        panels=fit.synth(split,widths,size,3)
    result,seen = {},set()
    for mode,rows in panels.items():
        if mode=="clean":
            continue
        totals,best=Counter(),[]
        for index,(item,terms,receipt) in enumerate(rows):
            totals["presentations"]+=1
            routes=initial.four(item,terms,receipt)
            if len(routes[3][2])!=2:
                continue
            totals["eligible_starts"]+=1
            current,paths,toggles=search(item,terms,receipt,routes,SEEDS[split]+index)
            if not curriculum.needs_both(paths):
                continue
            key=item[0],terms
            if key in seen:
                totals["duplicate_worlds"]+=1
                continue
            seen.add(key)
            distinct=grade(paths)[2]
            totals["unique_required_both"]+=1
            totals["distinct_roles"]+=distinct
            best.append({"original_index":index,"row":current[0],"terms":terms,
                         "tape":[[list(k),v] for k,v in current[1].items()],
                         "toggles":toggles,"world_class":fit.world_label(item),
                         "distinct_roles":distinct,"branches":paths})
        result[mode]={"counts":dict(totals),"items":best}
    return result


def run():
    return {"scope":"Synthetic challenge construction seeded from any two-decision trace, with up to two tape edits. Report the selected cases as challenge examples. Every branch uses the same selected tape and preserves observed action boundaries.",
            "seeds":SEEDS,"attempts_per_eligible_tape":LIMIT,
            "splits":{split:make(split) for split in ROWS}}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
