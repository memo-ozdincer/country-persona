"""Jointly select query timing and who speaks next after a delivery failure."""
from contextlib import contextmanager
import json
from unittest.mock import patch

import delivery_handoff as floor
import joint_repair_fit as paired
import query_gate as query

fit, core, router = paired.fit, paired.core, paired.router
SEEDS = {"train": 347341,"dev": 646267,"heldout": 856763,"archive": 881017}
ASK = fit.selection.group.OFFER_SET
FEATURES = {"query":query.FEATURES,"handoff":floor.FEATURES}
PROTOCOL = fit.protocol


def play(item,terms,receipt,defer,transfer):
    history=[False,False]
    chronicle=[]
    query_view=None
    current=None

    @contextmanager
    def observe(terms):
        nonlocal current, query_view
        with PROTOCOL(terms):
            available,default,transition=router.available,router.default,router.transition

            def see(item,state):
                nonlocal current
                obs,legal,routine=available(item,state)
                current = item,state,legal,routine
                return obs,legal,routine

            def get(obs,mode):
                nonlocal query_view
                planned=default(obs,mode)
                item,state,legal,routine=current
                owner,slot=state[1:3]
                if planned!=ASK or query_view is not None or not history[1-owner]:
                    return planned
                query_view=query.local_view(item,state,legal,routine)
                intervention=defer(query_view)
                chronicle.append(("query",slot,owner,intervention))
                return core.ROUTINE if intervention else planned

            def mark(item,state,action,choices,regular,recorded=None):
                after,checked,event=transition(item,state,action,choices,regular,recorded)
                if action==core.ROUTINE:
                    yes,no=core.intended(state,regular)
                    owner=state[1]
                    ledger=after[0]
                    history[owner] |= bool((yes&~ledger[2*owner])|(no&~ledger[2*owner+1]))
                return after,checked,event

            with patch.object(router,"available",new=see),patch.object(router,"default",new=get),patch.object(
                    router,"transition",new=mark):
                yield

    def handoff(view):
        applied=transfer(view)
        owner,slot=current[1][1:3]
        chronicle.append(("handoff",slot,owner,applied))
        return applied

    with patch.object(fit,"protocol",new=observe):
        floor_view, outcome, _ = floor.play(item,terms,receipt,handoff)
    return outcome,[query_view,floor_view],chronicle


def prepare(panels):
    results={}
    for regime, rows in panels.items():
        results[regime]=[]
        for item,terms,receipt in rows:
            paths=[play(item,terms,receipt,lambda _:a,lambda _:b) for a,b in paired.OPTIONS]
            results[regime].append((fit.world_label(item),paths))
    return results


def rename_fit(results):
    return {("query_only" if k=="packet_only" else k):v for k,v in results.items()}


def report(results, selected):
    measured=paired.report(results,selected)
    for row in measured.values():
        row["arms"]["always_defer"]=row["arms"].pop("always_packet")
        row["arms"]["query_only"]=row["arms"].pop("packet_only")
    return measured


def run():
    with patch.object(fit,"SEEDS",new=SEEDS),patch.object(paired,"FEATURES",new=FEATURES):
        train=prepare(fit.synth("train",(5,6),600,2))
        dev=prepare(fit.synth("dev",(6,),510,3))
        selected=paired.optimize(train,dev)
        test=prepare(fit.synth("heldout",(7,8),470,3))
        linked={name:prepare(panels) for name,panels in core.audit.samples() if name!="fresh_synthetic"}
    return {"scope":"Joint search over local query deferral and handoff rules. The query choice can see one public prior peer failure bit; the handoff choice uses its own latest delivery. Each intervention is available once.",
            "seeds":SEEDS,"features":FEATURES,"fit":rename_fit(selected),
            "heldout":report(test,selected),"development":report(dev,selected),
            "workshops":{name:report(rows,selected) for name,rows in linked.items()}}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
