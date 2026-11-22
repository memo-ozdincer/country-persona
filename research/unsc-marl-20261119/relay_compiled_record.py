"""Compile a sourced memo from the delivered ledger and a warranted action."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import relay_raw_signs as evaluation

relay=evaluation.baseline
HERE=relay.HERE
MANIFEST=relay.KIT/"compiled-record-sources.json"
TYPED=relay.KIT/"evidence/relay-marl/balanced.json"
TEXT=relay.KIT/"evidence/relay-text/context.json"
FRAMES=((1,"far delegate","relay"),(1,"relay","chair"),(2,"relay","chair"))
CAP=100


def load(path):
    return json.loads(path.read_text())


def read_authority(spec):
    source=load(HERE/spec["file"])
    blocks=(source["numbered_evidence"] if "numbered_evidence" in source else
            {part["id"]:part["text"] for part in source["evidence"]})
    result=[]
    for key,label,quote in spec["authority"]:
        if label not in blocks[key] or quote not in blocks[key]:
            raise ValueError(f"Source span mismatch for {key}")
        result.append({"id":key,"label":label,"quote":quote})
    return result


def received(task, transcript):
    """Validate the trace's routing, ownership and value continuity."""
    if len(transcript)!=len(FRAMES):
        raise ValueError("Wrong number of relay opportunities")
    masks=(tuple(task.first),tuple(task.second))
    public=[0,0]
    heard=0
    for i,(event,frame) in enumerate(zip(transcript,FRAMES,strict=True)):
        if tuple(event[k] for k in ("round","sender","recipient"))!=frame:
            raise ValueError("Wrong round or route")
        claimed=event["owner"]
        if claimed not in ("relay","far delegate"):
            raise ValueError("Unknown owner")
        owner=int(claimed=="far delegate")
        if (i==0 and owner!=1) or (i==1 and owner!=0):
            raise ValueError("Role swapped its owned card")
        sent,arrival=event["intended_mask"],event["delivered_mask"]
        if (type(sent) is not int or type(arrival) is not int or
                (sent and sent not in masks[owner]) or arrival not in (0,sent)):
            raise ValueError("Card value or delivery is invalid")
        if i==0:
            heard=arrival
            continue
        if i==2 and owner==1 and sent!=heard:
            raise ValueError("Relay forwarded a card it did not receive")
        if public[owner] and sent and sent!=public[owner]:
            raise ValueError("Previously delivered card has changed")
        public[owner]=public[owner] or arrival
    return tuple(public)


def options(task,mask):
    return "/".join(a for i,a in enumerate(task.actions[:-1]) if mask&(1<<i))


def compile_record(task, spec, transcript, proposal):
    left,right=received(task,transcript)
    warranted=task.warrant(left,right)
    if proposal not in task.actions:
        raise ValueError("Unknown action")
    chosen=task.actions.index(proposal)
    status=proposal.upper() if chosen in warranted else "UNRESOLVED"
    roles=spec["roles"]
    kind=spec["workshop_action"]
    claims=[f"The {role} workshop card permits only {options(task,mask)}." if mask else f"{role}'s workshop card is missing."
            for role,mask in zip(roles,(left,right),strict=True)]
    if status=="UNRESOLVED":
        missing=[role for role,mask in zip(roles,(left,right),strict=True) if not mask]
        if not warranted and missing:
            cards=" and ".join(f"{name}'s card" for name in missing)
            action=f"The chair should request {cards} and keep the decision pending."
        else:
            action="The chair should review the available evidence before making a recommendation."
    elif chosen==task.hold:
        action=(f"The public rule and delivered evidence establish no common {kind}. "
                f"The chair should {spec['no_overlap_step']}.")
    else:
        why="Both delivered cards" if left and right else "The visible evidence and public rule"
        action=f"{why} permit {kind} {proposal}. The chair should recommend it."
    authority=read_authority(spec)
    history=" ".join(f'{x["label"]} records “{x["quote"]}”' for x in authority)
    memo=f"Workshop status: {status}\n{' '.join(claims)} {action} This workshop recommendation has no official authority.\n{history}"
    options_left=(left,) if left else task.first
    options_right=(right,) if right else task.second
    return {"memo":memo,"candidate_action":proposal,"checked_status":status,
            "warranted_actions":[task.actions[i] for i in sorted(warranted)],
            "compatible_worlds":len(options_left)*len(options_right),
            "delivered_cards":dict(zip(roles,(left,right),strict=True)),
            "source_receipts":authority,"words":len(memo.split()),"word_cap":len(memo.split())<=CAP}


def cases():
    record=load(TYPED)
    typed=record["results"]["arms"]["warranted"]["after"]
    for family in ("mali","myanmar"):
        for arm in ("peer","mute_far","mute_near","mute_both"):
            yield "typed",family,arm,typed[family][arm]
    for family in ("venezuela","outer_space"):
        for arm,values in record["large_transfer"]["warranted"][family].items():
            yield "typed",family,arm,values
    for family in ("mali","myanmar"):
        for arm in ("peer","mute_far","mute_near","mute_both"):
            yield "qwen_head",family,arm,load(TEXT)["after"][family][arm]


def mutations(task,spec,trace,proposal):
    errors=[]
    for i,key,replacement in ((1,"owner","far delegate"),(2,"round",1),
                              (2,"sender","far delegate"),(1,"delivered_mask",999)):
        changed=deepcopy(trace)
        changed[i][key]=replacement
        try:
            compile_record(task,spec,changed,proposal)
        except ValueError as failure:
            errors.append(str(failure))
        else:
            raise AssertionError(f"Mutation {key} escaped")
    forged=deepcopy(trace)
    forged[0]["delivered_mask"]=0
    try:
        compile_record(task,spec,forged,proposal)
    except ValueError as failure:
        errors.append(str(failure))
    else:
        raise AssertionError("The undelivered peer card was forwarded")
    bad_source=deepcopy(spec)
    bad_source["authority"][0][2]="The simulated workshop adopted the resolution."
    try:
        compile_record(task,bad_source,trace,proposal)
    except ValueError as failure:
        errors.append(str(failure))
    else:
        raise AssertionError("A newly invented official quotation was accepted")
    return errors


def run():
    specs=load(MANIFEST)
    tasks=evaluation.test_families()
    records,stats,checks={},Counter(),[]
    for policy,family,arm,episode in cases():
        task=tasks[family]
        for world_index,(world,trace) in enumerate(zip(task.worlds,episode,strict=True)):
            result=compile_record(task,specs[family],trace["deliveries"],trace["choice"])
            decided=result["checked_status"]!="UNRESOLVED"
            assert decided==trace["warranted"]
            if decided:
                assert task.actions.index(result["candidate_action"]) in task.valid(*world)
            visible=result["delivered_cards"].values()
            assert all(not mask or mask==gold for mask,gold in zip(visible,world,strict=True))
            # Recheck the proof by enumerating candidate actions, independently
            # from the set-intersection implementation used by the policy.
            left,right=visible
            possible=tuple(product((left,) if left else task.first,(right,) if right else task.second))
            independent=[
                choice for i,choice in enumerate(task.actions)
                if all((a&b)==0 if i==task.hold else bool((a&b)&(1<<i)) for a,b in possible)
            ]
            assert independent==result["warranted_actions"]
            assert len(possible)==result["compatible_worlds"]
            assert result["memo"].splitlines()[0]==f"Workshop status: {result['checked_status']}"
            stats[policy,family,arm,"records"]+=1
            stats[policy,family,arm,"decisions"]+=decided
            stats[policy,family,arm,"within_cap"]+=result["word_cap"]
            records[f"{policy}/{family}/{arm}/{world_index}"]=result
            if policy=="qwen_head" and arm=="peer" and world_index==0:
                checks.append({"family":family,"rejected":mutations(
                    task,specs[family],trace["deliveries"],trace["choice"])})
    dependencies=(Path(__file__),MANIFEST,TYPED,TEXT,HERE/"relay_marl.py",HERE/"relay_raw_signs.py",
                  *(HERE/spec["file"] for spec in specs.values()))
    return {"scope":"Reuse frozen action traces. The compiler receives delivered masks and the proposed action. The public domain defines warrant. Curated exact source spans provide official history. Scores are mechanical trace and format checks.",
            "inputs":{str(k.relative_to(HERE)):sha256(k.read_bytes()).hexdigest() for k in dependencies},
            "metrics":{"/".join(k):v for k,v in sorted(stats.items())},"mutations":checks,"records":records}


if __name__=="__main__":
    print(json.dumps(run(),indent=2,ensure_ascii=False))
