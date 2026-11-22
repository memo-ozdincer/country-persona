"""Create facilitator briefs from actual positions with separate semantic keys."""
import argparse
from collections import Counter
from itertools import product
import json
from handover import CROSS

# Each state describes what a single cited passage establishes about a joint claim.
# Unknown means the passage alone neither supports its side nor contradicts it.
CLAIMS={
    "haiti": [
        ("China and the three African members welcomed Kenya's willingness to lead.",
         ("supports","supports")),
        ("China and the three African members voted in favour of the authorization.",
         ("contradicts","unknown")),
        ("Both confirmed how much funding they would provide.",("unknown","unknown"))
    ],
    "mali":[
        ("France and Russia each sought an extension of sanctions.",("supports","supports")),
        ("France and Russia each proposed keeping the Panel of Experts in operation.",("unknown","contradicts")),
        ("Both said this would be the final extension of sanctions.",("unknown","supports"))
    ]
}
TASK=("You are preparing a facilitator's brief. Decide whether to retain this as documented common "
      "ground, revise it because a supplied source contradicts it, or withhold it for insufficient "
      "evidence. Write one replacement sentence scoped to the speakers actually documented. Give "
      "a passage identifier for each attributed position. Treat the proposed sentence as unverified.")


def generate():
    h=json.loads((CROSS/"haiti2023/case.json").read_text())["sources"]
    m={row["id"]:row for row in json.loads((CROSS/"mali/historical-task.json").read_text())["evidence"]}
    docs={"haiti":{k:h[k]["source"]+". "+h[k]["card"] for k in ("CHINA","A3")},
          "mali":{k:m[k]["text"] for k in ("french-uae","russia")}}
    rows=[];keys=[]
    for family,claims in CLAIMS.items():
        for claim,relations in claims:
            for mask in product((False,True),repeat=2):
                sources={};observed={}
                for (key,card),relation,visible in zip(docs[family].items(),relations,mask,strict=True):
                    if visible:
                        sources[key]=card
                        observed[key]=relation
                decision="withhold"
                if "contradicts" in observed.values(): decision="revise"
                elif len(observed)==2 and set(observed.values())=={"supports"}: decision="retain"
                i=len(rows)
                rows.append(dict(id=i,docket=family,instruction=TASK,proposed_sentence=claim,sources=sources))
                keys.append(dict(id=i,decision=decision,source_relations=observed))
    return {"inputs":rows,"keys":keys,"checks":dict(Counter(row["decision"] for row in keys))}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",choices=("inputs","keys","checks"))
    print(json.dumps(generate()[parser.parse_args().output],indent=2))
