"""Audit one-step teacher action conflicts under the frozen actor observation."""
from collections import Counter, defaultdict
import json
import random

import neural_suffix as suffix

neural,sp,guard,routing=suffix.neural,suffix.sp,suffix.guard,suffix.routing


def evaluate():
    rows=sp.panels((6,7),neural.TEST,900,3)
    # Fixed slice of the existing locked distribution. The probe never trains an actor.
    selection=Counter()
    sample=[]
    for row in rows:
        kind="agreement" if row[1][0]&row[1][1] else "impasse"
        if selection[kind]<256:
            sample.append((kind,row))
            selection[kind]+=1
    degraded=routing.refit.drop_returns([r for _,r in sample],neural.TEST+31)
    sets={"clean":guard.messages([r for _,r in sample],neural.TEST+30,0,0),
          "faults":guard.messages(degraded,neural.TEST+30,.26,.11)}
    results={}
    for name,data in sets.items():
        rng=random.Random(neural.TEST+34)
        grouped=defaultdict(list)
        counts=Counter()
        for i,((label,_),item) in enumerate(zip(sample,data,strict=True)):
            states,_=suffix.sample(item,rng)
            for view,advantages,valid in states:
                for action in range(neural.ACTIONS):
                    if not valid[action]:
                        continue
                    value=advantages[action]
                    counts[label,"action_examples"]+=1
                    if abs(value)>.5:
                        sign=1 if value>0 else -1
                        counts[label,"certificate_changes"]+=1
                        grouped[tuple(view),action].append((i,label,sign,float(value)))
        collisions=[]
        switches=set()
        for (view,action),visits in grouped.items():
            positive=[v for v in visits if v[2]>0]
            negative=[v for v in visits if v[2]<0]
            if positive and negative:
                counts["all","conflicting_decisions"]+=1
                counts["all","opposed_action_examples"]+=len(visits)
                switches.update(v[0] for v in visits)
                collisions.append({"action":action,"actor_view":view,"positive":positive[0],"negative":negative[0],
                                   "positive_examples":len(positive),"negative_examples":len(negative)})
        counts["all","episodes_in_conflicts"] = len(switches)
        results[name]={"presentations":dict(selection),"counts":sp.flatten(counts),
                       "example_witnesses":collisions[:6]}
    return {"scope":"A matched local-observation signature with opposite one-step certificate changes. Episode indices identify the deterministic sample. This measures aliasing in the current feature representation.",
            "panels":results}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
