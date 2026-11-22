"""Fit matched local policies with and without priority for two-action episodes."""
import json
from unittest.mock import patch

import numpy as np

import joint_deferral_fit as negotiation

paired = negotiation.paired
fit = negotiation.fit
SEEDS = {"train": 489703, "dev": 865299, "heldout": 462211, "archive": 314919}


def needs_both(paths):
    return paths[3][0][0] and not any(v[0][0] for v in paths[:3])


def shows_both(paths):
    return any(len(path[2])==2 for path in paths)


def masked(data, eligible):
    return {regime:[r for r in rows if eligible(r[1])] for regime,rows in data.items()}


def select(train, dev):
    grid=paired.make_grid()
    assert grid[0]==paired.FIXED
    raw_t,raw_d=(paired.count_grid(rows,grid) for rows in (train,dev))
    by_joint=[]
    for rows in (train,dev):
        statistic=paired.count_grid(masked(rows,shows_both),grid)
        essential=paired.count_grid(masked(rows,needs_both),grid)
        by_joint.append((statistic,essential))

    def total(counts, index):
        return sum(int((v[index]-v[0]) @ np.asarray((200,-3,-1))) for v in counts.values())

    def solves(counts, index):
        return sum(int(v[index,0]) for v in counts.values())

    records=[]
    for index,rules in enumerate(grid):
        if any(np.any(v[index,0]<v[0,0]) for split in (raw_t,raw_d) for v in split.values()):
            continue
        overall_train,overall_dev=total(raw_t,index),total(raw_d,index)
        both_t,need_t=by_joint[0]
        both_d,need_d=by_joint[1]
        records.append({
            "rules":rules,
            "overall_train_team_gain":overall_train, "overall_dev_team_gain":overall_dev,
            "joint_train_team_gain":total(both_t,index), "joint_dev_team_gain":total(both_d,index),
            "required_both_train_solved":solves(need_t,index),
            "required_both_dev_solved":solves(need_d,index),
            "complexity":sum(r is not None for r in rules), "index":index,
        })

    def rank_standard(row):
        return (row["overall_dev_team_gain"],row["overall_train_team_gain"],
                -row["complexity"],-row["index"])

    def rank_joint(row):
        return (row["required_both_dev_solved"],row["required_both_train_solved"],
                row["joint_dev_team_gain"],row["joint_train_team_gain"],*rank_standard(row))

    return {"ordinary":max(records,key=rank_standard),"joint_curriculum":max(records,key=rank_joint),
            "protected_candidates":len(records),
            "guarded_candidates_that_use_both":sum(all(r is not None for r in record["rules"])
                                                   for record in records)}


def support(panels):
    return {name:{
        "presentations":len(rows),
        "both_observed_in_a_branch":sum(shows_both(paths) for _,paths in rows),
        "requires_both":sum(needs_both(paths) for _,paths in rows),
        "distinct_roles_when_both_needed":sum(
            needs_both(paths) and paths[3][2][0][2]!=paths[3][2][1][2] for _,paths in rows),
    } for name,rows in panels.items()}


def summarize(panels, policies):
    comparison=paired.report(panels,policies)
    for result in comparison.values():
        result["arms"]["always_defer"]=result["arms"].pop("always_packet")
    return {
        "population":comparison,
        "both_available":paired.report(masked(panels,shows_both),policies),
        "both_required":paired.report(masked(panels,needs_both),policies),
    }


def run():
    with patch.object(fit,"SEEDS",new=SEEDS),patch.object(
            paired,"FEATURES",new=negotiation.FEATURES):
        train=negotiation.prepare(fit.synth("train",(6,7),850,3))
        dev=negotiation.prepare(fit.synth("dev",(6,7),620,3))
        picks=select(train,dev)
        test=negotiation.prepare(fit.synth("heldout",(7,8),700,3))
        archives={name:negotiation.prepare(rows) for name,rows in negotiation.core.audit.samples()
                  if name!="fresh_synthetic"}
    policies={k:picks[k] for k in ("ordinary","joint_curriculum")}
    return {
        "scope":"Matched offline selection on synthetic rollouts. The curriculum prioritizes cases needing both interventions and cases where both can occur. The two fits use the same local views, cases and guards. UN families and the synthetic holdout do not enter selection.",
        "seeds":SEEDS,"features":negotiation.FEATURES,"fit":picks,
        "training_support":support(train),"development_support":support(dev),
        "heldout_support":support(test),"heldout":summarize(test,policies),
        "workshops":{name:{"support":support(rows),**summarize(rows,policies)} for name,rows in archives.items()},
    }


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
