"""Paired response capacity comparison for the same fixed routing schedules."""
from collections import Counter
import json
from unittest.mock import patch

import scope_reply as stage


def evaluate():
    seed=782943
    rows=stage.sp.panels((8,9),seed,650,4)
    variants={
        "reliable":stage.guard.messages(rows,seed+1,0,0),
        "faults":stage.guard.messages(stage.routing.refit.drop_returns(rows,seed+2),seed+1,.26,.11),
    }
    panels={}
    for label,items in variants.items():
        counts=Counter()
        for schedule in ("early_match","match_only",stage.policy.START):
            with patch.object(stage.policy,"advance",side_effect=stage.focused.answer):
                direct,_=stage.policy.measure(items,schedule,{})
            with patch.object(stage.policy,"advance",side_effect=stage.reply):
                scoped,_=stage.policy.measure(items,schedule,{})
            for item,a,b in zip(items,direct,scoped,strict=True):
                x,y=item[0][1]
                group="agreement" if x&y else "impasse"
                counts[schedule,group,str(a[0]),str(b[0])]+=1
                counts[schedule,group,"slot_change"]+=b[1]-a[1]
        panels[label]=stage.sp.flatten(counts)
    return panels


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
