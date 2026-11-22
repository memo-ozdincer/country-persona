"""Exact feasibility bounds for local source-selection policies."""
from itertools import combinations, product
import json

import bank


def slates(actions, keep):
    result=[]
    total=1-(1-keep)**len(actions)
    for n in range(1,len(actions)+1):
        for subset in combinations(actions,n):
            result.append((subset,keep**n*(1-keep)**(len(actions)-n)/total))
    assert abs(sum(weight for _,weight in result)-1)<1e-10
    return result


def optimize(reward, a_options, b_options, order):
    a_actions=next(slate for slate,_ in a_options if len(slate)==2)

    def independent():
        candidates=[]
        for intended in a_actions:
            peru={slate:intended if intended in slate else slate[0] for slate,_ in a_options}
            russia={slate:max(slate,key=lambda action:sum(
                p*reward[(peru[a],action)] for a,p in a_options)) for slate,_ in b_options}
            candidates.append((peru,russia))
        return max(candidates,key=lambda pair:sum(
            pa*pb*reward[pair[0][a],pair[1][b]] for (a,pa),(b,pb) in product(a_options,b_options)))

    peru,russia=independent()
    blind=sum(pa*pb*reward[peru[a],russia[b]] for (a,pa),(b,pb) in product(a_options,b_options))
    send_options, reply_options=(a_options,b_options) if order==0 else (b_options,a_options)

    def value(first, second):
        return reward[(first,second) if order==0 else (second,first)]

    observed=sum(p*max(sum(q*max(value(x,y) for y in b) for b,q in reply_options) for x in a)
                 for a,p in send_options)
    return {"independent":round(blind,8),"peer":round(observed,8),"peer_headroom":round(observed-blind,8)}


def run():
    case=bank.e.cases()[bank.CASE]
    a,b=([row["id"] for row in side] for side in case["owned"])
    outcome=bank.e.read(bank.HERE/"results.json")["by_order"]
    rows=[]
    for order,keep in product((0,1),(.45,.65,.85)):
        scores=outcome[str(order)]
        limits={}
        measures={
            "released_70":lambda score:score["released_70"],
            "mapped_evidence_coverage":lambda score:score["mapped_evidence_coverage"],
            "raw_lower_70":lambda score:score["raw_70"][0],
            "ignore_word_cap":lambda score:score["raw_70"][0] if not (
                set(score["release_blockers"])-{"final_word_cap"}
            ) else 0,
        }
        for attr,measure in measures.items():
            reward={tuple(key.split("/")):measure(score) for key,score in scores.items()}
            limits[attr]=optimize(reward,slates(a,keep),slates(b,keep),order)
        rows.append({"order":order,"keep_probability":keep,**limits})
    return rows


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
