"""Compare focused lookup with a pre-result local choice of one lookup source."""
import argparse
from collections import Counter
from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import target_set as group
import target_transfer

policy,sp=group.policy,group.SP
BASE_TRANSITION=group.transition


def enabled(minimum):
    def choose(item,state,move,actions,routine,recorded=None):
        if move==group.OFFER_SET:
            row,_=item
            public,asker,_,credit=state
            peer=1-asker
            yes,no=row[2][peer]
            targets=actions[move]
            target=group.select(targets,yes,no,public[2*asker])
            unknown=((1<<row[0])-1)&~(yes|no|public[1]|public[3])
            if credit&(1<<peer) and unknown&target and unknown.bit_count()>=minimum:
                after,charged,receipt=group.old.ORIGINAL_TRANSITION(
                    item,state,policy.MATCH_SCOPE,{policy.MATCH_SCOPE:target},routine,recorded)
                return after,charged,{**receipt,"request_set":targets,"unknown_before":unknown}
        return BASE_TRANSITION(item,state,move,actions,routine,recorded)

    stack=ExitStack()
    stack.enter_context(patch.object(group,"transition",new=choose))
    stack.enter_context(group.enabled())
    return stack


def evaluate(raw,factored):
    panel=sp.panels((6,7),group.TEST,900,3)
    wrap=policy.guard.messages
    drop=policy.routing.refit.drop_returns
    cohorts={"reliable":wrap(panel,group.TEST+1,0,0),
             "faults":wrap(drop(panel,group.TEST+2),group.TEST+1,.26,.11)}
    with group.enabled():
        references={name:policy.measure(items,group.BASE,{})[0] for name,items in cohorts.items()}
    output={}
    for minimum in (2,3,4):
        scores={}
        with enabled(minimum):
            for name,items in cohorts.items():
                metrics=Counter()
                for item,reference in zip(items,references[name],strict=True):
                    events=[]
                    solved,slots,checks,*_=policy.play(item,group.BASE,{},events=events)
                    left,right=item[0][1]
                    label="agreement" if left&right else "impasse"
                    metrics[label,"retained" if solved==reference[0] else "gain" if solved else "loss"]+=1
                    metrics[label,"solved"]+=solved
                    metrics[label,"slots"]+=slots
                    metrics[label,"checks"]+=checks
                    metrics[label,"scope_choices"]+=sum(
                        e["query"] is not None and e["query"].get("lookup")=="scope_only" for e in events)
                scores[name]=sp.flatten(metrics)
        output[minimum]={"synthetic":scores,"archive":{
            label:target_transfer.evaluate(path,bundle=True,scope_minimum=minimum)
            for label,path in (("raw",raw),("factored",factored))}}
    return {"inputs":{label:sha256(path.read_bytes()).hexdigest()
                      for label,path in (("raw",raw),("factored",factored))},
            "scope":"Frozen schedule. Use scope for an unknown selected reply if the respondent has enough publicly unblocked unknowns. Select before either lookup. One lookup and two slots.",
            "variants":output}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw",type=Path)
    p.add_argument("factored",type=Path)
    args=p.parse_args()
    print(json.dumps(evaluate(args.raw,args.factored),indent=2))
