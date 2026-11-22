"""Check whether the earlier Myanmar win survives a speaker-only edit."""
import json
from pathlib import Path
import sys

import delivery_handoff as handoff


def summarize(item, result, events, change):
    role_claims = [0,0]
    initial = handoff.router.sp.opened(item[0][3],item[0][2])
    for position, bits in enumerate(initial):
        role_claims[position//2] += bits.bit_count()
    for event in events:
        for owner, _, bits in event["disclosed"]:
            role_claims[owner] += bits.bit_count()
    return {"result":result,"events":events,"handoff":change,"distinct_admitted_per_role":role_claims}


def witnesses(old, fitted):
    output={}
    rules=fitted["rules"]
    for family, panels in handoff.core.audit.samples():
        if family not in ("myanmar","venezuela_model_receipts"):
            continue
        rows=panels["independent"]
        indices = (old["myanmar"]["source_row"],*range(len(rows))) if family=="myanmar" else range(len(rows))
        for index in indices:
            item,terms,receipt=rows[index]
            before,after,chosen=[],[],[]
            see, base, original=handoff.play(item,terms,receipt,lambda _:False,before)
            if see is None or base[0]:
                continue
            again, changed, actions=handoff.play(item,terms,receipt,lambda _:True,after)
            if not changed[0]:
                continue
            assert see==again and len(actions)==1
            _,actual,applied=handoff.play(item,terms,receipt,lambda x:not handoff.gate.choose(x,rules),chosen)
            slot=actions[0]["slot"]
            # At the intervention point itself the actual disclosures and
            # official ledger coincide. Speaker ownership changes afterward.
            index_in_trace=next(i for i,e in enumerate(before) if e["slot"]==slot)
            assert before[:index_in_trace+1]==after[:index_in_trace+1]
            output[family]={"row":index,"world":handoff.fit.world_label(item),"terms":terms,
                            "view":dict(zip(handoff.FEATURES,see,strict=True)),
                            "fixed":summarize(item,base,before,original),
                            "forced_switch":summarize(item,changed,after,actions),
                            "learned":summarize(item,actual,chosen,applied)}
            break
    assert output["myanmar"]["row"]==old["myanmar"]["source_row"]
    return output


if __name__ == "__main__":
    folder=Path(sys.argv[1])
    old=json.loads((folder/"witnesses.json").read_text())
    fitted=json.loads((folder/"handoff.json").read_text())
    print(json.dumps(witnesses(old,fitted),indent=2))
