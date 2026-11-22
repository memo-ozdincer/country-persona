"""Measure the held-out gap between local observations and hidden-state choices."""
from collections import Counter, defaultdict
import json

import robust_retry_fit as fitted

episode=fitted.episode


def policy_value(rows,choice):
    return fitted.score(rows,choice)[0]


def best(rows,guard):
    candidates=[]
    for i in range(len(episode.ACTIONS)):
        if guard and any(paths[0][0] and not paths[i][0] for _,_,paths in rows):
            continue
        value=sum(episode.base.objective.utility(*paths[i][:3]) for _,_,paths in rows)
        candidates.append((value,-i))
    return -max(candidates)[1]


def classify(panels):
    all_rows=[r for data in panels.values() for r in data]
    groups=defaultdict(list)
    for row in all_rows:
        groups[row[1]].append(row)
    unrestricted={obs:best(rows,False) for obs,rows in groups.items()}
    protected={obs:best(rows,True) for obs,rows in groups.items()}
    collisions={}
    for obs,rows in groups.items():
        if obs is None:
            continue
        details={}
        for i,action in enumerate(episode.ACTIONS[1:],start=1):
            counts=Counter(int(p[i][0])-int(p[0][0]) for _,_,p in rows)
            gains=counts[1]
            losses=counts[-1]
            if gains and losses:
                details[action]={"wins":gains,"losses":losses,"same":counts[0]}
        if details:
            collisions["".join("1" if present else "0" for present in obs)]=details
    totals={}
    for label,rows in panels.items():
        clairvoyant=Counter()
        for row in rows:
            actor=best([row],False)
            clairvoyant.update(policy_value([row],lambda _:actor))
        totals[label]={name:episode.sp.flatten(score) for name,score in (
            ("immediate",policy_value(rows,lambda _:0)),("unrestricted_local",policy_value(rows,unrestricted.__getitem__)),
            ("protected_local",policy_value(rows,protected.__getitem__)),("clairvoyant",clairvoyant))}
    return {"scope":"These are in-sample upper bounds for synthetic held-out rows. The global local tables maximize summed reward using the evaluated outcomes. The protected table never sacrifices an individual proof that immediate retry delivered. The clairvoyant can use a different action for identical observations.",
            "local_signatures":len(groups)-int(None in groups),
            "conflicting_signatures":collisions,"by_condition":totals}


if __name__=="__main__":
    data=episode.panels((7,8),550,3,fitted.SEEDS["heldout"])
    print(json.dumps(classify(data),indent=2))
