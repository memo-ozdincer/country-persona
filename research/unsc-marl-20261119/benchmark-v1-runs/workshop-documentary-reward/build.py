"""Construct and score public workshop records under partial disclosure."""
from itertools import product
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
RELEASE=HERE.parents[1]/"benchmark-v1.7"
sys.path.insert(0,str(RELEASE))
import evaluate as e

VALUES={"term":{"retain":"retention of the adopted mandate term","shorten":"a recommendation for a shorter mandate term"},
        "documentation":{"public":"public consultation summary without an annex",
                         "annex":"a public summary and a confidential annex"},
        "duration":{"six":"six months","nine":"nine months"},
        "checkpoint":{"additional":"an extra formal review checkpoint","ordinary":"ordinary reporting"}}


def match(options, mandates):
    return {row["id"] for row in options if all(row.get(key)==value for card in mandates
                                                for key,value in card.items())} or {"IMPASSE"}


def physical_card(role, claim):
    key,value=next(iter(claim.items()))
    return f"The {role} requires {VALUES[key][value]}."


def render(case,received,domains):
    family=case["family"]
    public={row["id"]:row["text"] for row in case["public"]}
    blocks=[row["id"] for row in case["public"] if "source" in row]
    worlds=[match(case["options"],pair) for pair in product(*domains)
            if all(pair[side]==claim for side,claim in received.items())]
    assert worlds
    choices=set.intersection(*worlds)
    chosen=sorted(choices)[0] if choices else "UNRESOLVED"
    history=" ".join(public[key] for key in blocks)
    declarations=" ".join(physical_card(case["roles"][i],claim) for i,claim in sorted(received.items()))
    absent=" ".join(f"The {role}'s mandate was unavailable." for i,role in enumerate(case["roles"])
                    if i not in received)
    if chosen=="UNRESOLVED":
        resolution="The disclosed mandates do not establish an agreement or impasse."
    elif chosen=="IMPASSE":
        field="mandate term" if family=="iraq" else "duration"
        alternate="Consultation documentation" if family=="iraq" else "An oversight change"
        resolution=f"The two {field} requirements conflict. {alternate} cannot resolve the conflict."
    else:
        option=next(row["text"] for row in case["options"] if row["id"]==chosen)
        option=option.replace("both access modalities","cross-border and cross-line access")
        resolution=f"Package {chosen} satisfies the possible mandates. {option}"
        if family=="iraq" and "annex" not in option:
            resolution+=" Consultation documentation is a workshop choice."
    authority="The fictional workshop establishes no official vote, authority or commitment."
    if family=="iraq":
        authority+=" A new annex or shorter term would require Council authorization."
    answer=f"Decision: {chosen}\n\n{history}\n\n{declarations} {resolution} {absent}\n\n{authority}"
    reply={"text":answer,"termination":"complete"}
    historical=[{"block":key,"quote":public[key]} for key in blocks]
    public_justification=historical+[{"block":key,"quote":public[key]} for key in ("menu","scope")]
    disclosed=[{"block":block["id"],"quote":block["text"]}
               for i in received for block in case["owned"][i]]
    packet=e.final_packet(case,[None,None,reply])
    units=[]
    for row in case["rubric"]:
        unit=row["id"]
        complete=len(received)==2
        active=chosen!="UNRESOLVED"
        status="met" if unit=="authority" or (active and (complete or unit!="positions")) else "unmet"
        response={"authority":authority,"positions":history+"\n\n"+declarations,
                  "open_issues":resolution,"action":history+"\n\n"+declarations+" "+resolution,
                  "disposition":f"Decision: {chosen}\n\n{history}"}[unit]
        units.append({"id":unit,"status":status,"response":response if status=="met" else "",
                      "source":public_justification+disclosed if status=="met" else [],
                      "reason":"The rendered evidence states or certifies the required distinction." if status=="met"
                               else "A missing mandate or an unresolved option leaves the criterion incomplete."})
    mark={"id":packet["id"],"units":units,"guard":{"status":"clear","source":[],"response":"",
                    "reason":"Published facts and fictional commitments are attributed and kept separate."}}
    score=e.final_score(case,[None,None,reply],mark)
    assert score["words"]<=case["word_cap"], (case["id"],received,score["words"])
    return {"score":score,"verdict":mark,"answer":answer,"options":sorted(choices)}


def run():
    cells={}
    for family in ("iraq","syria"):
        cases=[c for c in e.cases().values() if c["family"]==family]
        domains=[[json.loads(s) for s in sorted({json.dumps(c["membership"][i],sort_keys=True) for c in cases})]
                  for i in (0,1)]
        variants={}
        for case in cases:
            true=case["membership"]
            assert match(case["options"],true)==set(case["gold"])
            local=[domains[i].index(true[i]) for i in (0,1)]
            views={}
            for x,y in product((0,1),repeat=2):
                disclosed={index:true[index] for index,value in enumerate((x,y)) if value}
                views[f"{x}{y}"]=render(case,disclosed,domains)
            assert views["11"]["score"]["strict"]
            variants[case["id"]]={"local_keys":local,"views":views}
        cells[family]={"domains":domains,"cases":variants}
    return cells


if __name__=="__main__":
    e.emit(run())
