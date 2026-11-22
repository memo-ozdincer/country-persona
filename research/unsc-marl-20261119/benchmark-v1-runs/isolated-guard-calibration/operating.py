"""Measure conservative clearance and replay only the guard on held finals."""
from collections import Counter
import json
from statistics import mean

import guard


def margin(row):
    scores=row["logits"]
    return scores["clear"]-max(scores["uncertain"],scores["failed"])


def compare():
    data=guard.e.read(guard.HERE/"results.json")["results"]
    anchor=data["anchors"]
    fitted=max(0.,max(margin(row) for row in anchor.values() if row["target"]!="clear"))
    rules={
        "mean_logit":lambda row:row["chosen"]=="clear",
        "both_orders_clear":lambda row:row["per_order"]==["clear","clear"],
        "zero_anchor_false_clear":lambda row:margin(row)>fitted,
    }
    report={}
    for mode,pol in rules.items():
        cohorts={}
        for name,group in data.items():
            counts=Counter()
            for row in group.values():
                true=row["target"]=="clear"
                accept=pol(row)
                counts["accepted"]+=accept
                counts["false_clear"]+=accept and not true
                counts["false_block"]+=true and not accept
            cohorts[name]=dict(counts)
        report[mode]=cohorts

    _,links,_=guard.historical.packets()
    outcomes=guard.e.read(guard.HIST/"results.json")["by_episode"]
    comparisons={}
    for name,rule in {"reviewed":lambda row:row["target"]=="clear",**rules}.items():
        arms={}
        for episode,old in outcomes.items():
            row=data["historical"][links[episode]]
            usable=all(blocker.startswith("guard_") for blocker in old["release_blockers"])
            released=old["raw_70"][0] if usable and rule(row) else 0
            arms[episode]=released
        deltas={case:mean(arms[f"{case}/peer/{i}"]-arms[f"{case}/independent/{i}"] for i in (0,1))
                for case in guard.historical.CASES}
        comparisons[name]={"episode_scores":arms,"peer_effects":deltas,"macro":mean(deltas.values())}
    return {"calibrated_clearance_margin":fitted,"clearance":report,"fixed_rubric_replay":comparisons}


if __name__=="__main__":
    print(json.dumps(compare(),indent=2))
