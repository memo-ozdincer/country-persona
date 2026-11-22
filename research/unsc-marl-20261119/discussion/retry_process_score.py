"""Audit the public interaction and final proof in the retry judge fixtures."""
from collections import Counter, defaultdict
import json

import retry_judge as fixture

ROLES=("INDIA","UNITED KINGDOM")


def owner_counts(trace):
    signed,visible=defaultdict(set),defaultdict(set)
    turns=Counter()
    phases=Counter()
    added_signed,added_public=set(),set()
    for event in trace:
        role=event["actor"]
        assert role in ROLES and set(event["delivered"])<=set(event["signed"])
        turns[role]+=1
        phases[event["event"]]+=1
        if event["event"]=="resend":
            added_signed=set(event["signed"])-signed[role]
            added_public=set(event["delivered"])-visible[role]
        signed[role].update(event["signed"])
        visible[role].update(event["delivered"])
    return {"turns":sum(turns.values()),"phases":dict(phases),"agents":{
        role:{"turns":turns[role],"unique_signed_ideas":len(signed[role]),
              "unique_public_ideas":len(visible[role])} for role in ROLES},
            "new_in_resend":sorted(added_signed),"first_public_delivery_in_resend":sorted(added_public)}


def proof(trace):
    delivered={}
    complete=None
    for event in trace:
        if "accept B" in event["delivered"]:
            delivered.setdefault(event["actor"],event["slot"])
        if complete is None and all(role in delivered for role in ROLES):
            complete=event["slot"]
    return {"delivered_B":delivered,"complete_at_slot":complete,"agreement":complete is not None}


def score():
    result={}
    for name,payload in fixture.case_forms():
        trace=payload["trace"]
        before=proof(trace)
        without=[e for e in trace if e["event"]!="resend"]
        after=proof(without)
        mechanics=owner_counts(trace)
        unfiltered=proof([{**e,"delivered":e["signed"]} for e in trace])
        resends=[r for r in trace if r["event"]=="resend"]
        assert len(resends)==1 and mechanics["turns"]==len(without)+1
        resend=resends[0]
        code=(
            "new" if mechanics["new_in_resend"] else "same",
            "received" if ROLES[1] in before["delivered_B"] else "none",
            "changed" if before["agreement"] and not after["agreement"] else "unchanged",
            "failed" if payload["final_discussion_record"].startswith("The Council adopted workshop") else "clear",
        )
        assert code==fixture.EXPECTED[name],(name,code)
        result[name]={"mechanics":mechanics,"actual":before,"without_resend":after,
                      "visibility_control":{"all_signatures_counted_as_public":unfiltered,
                                            "public_only_sender_novelty":"indeterminate_without_signed_history"},
                      "without_resend_counts":owner_counts(without),
                      "exact_resend":resend,"final_record":payload["final_discussion_record"],
                      "rubric_reference":dict(zip(fixture.FIELDS,code,strict=True))}
    return {"scope":"Deterministic checks on five authored trace fixtures. The base witness records delivered ordinary signs and intended reply/retry signs. Argument quality and independent judgment are outside this check.",
            "cases":result}


if __name__=="__main__":
    print(json.dumps(score(),indent=2))
