"""Audit the communication cut and render named-role contribution records."""
import json
from pathlib import Path
import sys

import relay_marl as train


def evaluate(results):
    tables={}
    transcripts={}
    for name,task in train.fixtures().items():
        card=json.loads((train.KIT/f"{name}.json").read_text())
        labels=(dict(zip(task.first,task.labels[0],strict=True)),
                dict(zip(task.second,task.labels[1],strict=True)))
        grouped=[]
        for left,right in task.worlds:
            gold=task.valid(left,right)
            only_left=task.warrant(left,0)
            only_right=task.warrant(0,right)
            grouped.append({"cards":[labels[0][left],labels[1][right]],
                "acceptable":[task.actions[i] for i in sorted(gold)],
                "both_role_facts_required":not only_left and not only_right,
                "warranted_with_only_relay":[task.actions[i] for i in sorted(only_left)],
                "warranted_with_only_far_delegate":[task.actions[i] for i in sorted(only_right)]})
        tables[name]=grouped
        transcripts[name]={}
        for reward, by_reward in results["arms"].items():
            transcripts[name][reward]={}
            for arm,episodes in by_reward["after"][name].items():
                witnesses=[]
                for score, world in zip(episodes,grouped,strict=True):
                    visible=set()
                    process,spoken=[],{}
                    for log in score["deliveries"]:
                        bit=0 if log["owner"]=="relay" else 1
                        sender=card["roles"][1 if log["sender"]=="relay" else 2]
                        giver=card["roles"][1+bit]
                        recipient=card["roles"][0 if log["recipient"]=="chair" else 1]
                        intended=log["intended_mask"]
                        carried=log["delivered_mask"]
                        if intended:
                            assert labels[bit][intended]==world["cards"][bit]
                            spoken.setdefault(sender, set()).add((giver,labels[bit][intended]))
                        if carried:
                            assert intended==carried
                            if recipient==card["roles"][0]:
                                visible.add((giver,labels[bit][carried]))
                        content=f"{giver}: {labels[bit][intended]}" if intended else ""
                        if intended:
                            process.append({"round":log["round"],"sender":sender,"recipient":recipient,
                                            "owner":giver,"display":content,"delivered":bool(carried)})
                    rendered={"world":world,"transcript":process,
                             "distinct_attributed_propositions_by_speaker":{k:len(v) for k,v in spoken.items()},
                             "distinct_propositions_at_chair":sorted(visible),
                             "chair_decision":score["choice"],"valid":score["valid"],"warranted":score["warranted"]}
                    assert len(visible)<=2 and (len(visible)==2)==score["both_sources"]
                    witnesses.append(rendered)
                transcripts[name][reward][arm]=witnesses
    return {"scope":"Mechanical readout from typed decisions. Sources stay attributed when the relay repeats them. This measures content-bearing actions and the exact public proof.",
            "cut_audit":tables,"rendered_episodes":transcripts}


if __name__=="__main__":
    training=json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(evaluate(training),indent=2))
