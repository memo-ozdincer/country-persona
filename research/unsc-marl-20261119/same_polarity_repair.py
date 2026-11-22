"""Add an owned missing sign without changing the scheduled speaker or slot."""
from collections import Counter
import json
from unittest.mock import patch

import ordinary_resend as prior

fit, gate, router = prior.fit, prior.gate, prior.router
SEEDS = {"train": 143531, "dev": 732829, "heldout": 247519, "archive": fit.SEEDS["archive"]}
FEATURES = (
    "same_polarity", "added_acceptance", "added_exclusion", "added_matches_peer_offer",
    "combined_certifies", "normal_certifies", "at_most_three_live",
    "four_or_more_slots", "query_credit", "retains_floor", "multiple_missing",
)


def select(item, terms, state, normal, missing):
    public, owner, _, _ = state
    full = (1<<item[0][0])-1
    live = full & ~(public[1] | public[3])
    pool = tuple(bits & live & ~public[2*owner+sign] & ~normal[sign]
                 for sign,bits in enumerate(missing))
    normal_state = router.sp.record(router.sp.record(public,owner,normal[0],True),owner,normal[1],False)
    ranked = []
    peer_offer = public[2*(1-owner)]
    for sign, candidates in enumerate(pool):
        for i, description in enumerate(terms):
            bit = 1<<i
            if candidates & bit:
                joined = router.sp.record(normal_state,owner,bit,sign==0)
                decisive = router.sp.terminal(joined,full) and not router.sp.terminal(normal_state,full)
                ranked.append(((not decisive, not (bit & peer_offer), description), sign, bit))
    if not ranked:
        return (0,0), None
    _, sign, bit = min(ranked)
    added = (bit,0) if sign == 0 else (0,bit)
    both = normal[0]|added[0],normal[1]|added[1]
    joined = router.sp.record(normal_state,owner,bit,sign==0)
    details = (bool(normal[sign]),sign==0,sign==1,bool(bit&peer_offer),
               router.sp.terminal(joined,full),router.sp.terminal(normal_state,full),
               live.bit_count()<=3,item[0][0]+1-state[2]>=4,
               bool(state[3]&fit.selection.reuse.ROUTER.CREDIT),
               (pool[0]|pool[1]).bit_count()>1)
    return added,(both,details)


def play(item, terms, receipt, decide, trace=None):
    observed, attempts = [], []
    pending = [(0,0),(0,0)]
    with fit.protocol(terms):
        original = router.transition

        def step(item,state,action,choices,routine,recorded=None):
            if action!=prior.ROUTINE:
                return original(item,state,action,choices,routine,recorded)
            normal = prior.intended(state,routine)
            if not any(normal):
                return original(item,state,action,choices,routine,recorded)
            public,actor,slot,credit = state
            index = 2*actor
            packet, resend = normal, (0,0)
            if not observed and (normal[0]|normal[1]).bit_count()==1:
                added, alternative = select(item,terms,state,normal,pending[actor])
                if alternative is not None:
                    combined, details = alternative
                    frame, coded, ordinary, _, _ = routine
                    _, next_role, finish, remains = router.routing.step(frame[0],coded,*ordinary,1)
                    assert finish==slot+1 and remains==credit
                    view = (*details[:-1],next_role==actor,details[-1])
                    observed.append(view)
                    if decide(view):
                        packet,resend = combined,added
            if any(resend):
                assert (packet[0]|packet[1]).bit_count()==2
                assert not (packet[0]&~item[0][1][actor] or packet[1]&item[0][1][actor])
                after, delivered = fit.episode.delay.authorized_retry(
                    item, (public,next_role,slot,credit),actor,*packet)
                assert after[1:] == (next_role,finish,remains)
                checked,event = False,None
                attempts.append({"role":actor,"slot":slot,"next_role":next_role,"original":normal,
                                 "added":resend,"delivered":delivered,
                                 "admitted":bool((delivered[0]&resend[0])|(delivered[1]&resend[1]))})
            else:
                after,checked,event = original(item,state,action,choices,routine,recorded)
            pending[actor] = packet[0]&~after[0][index],packet[1]&~after[0][index+1]
            return after,checked,event

        with patch.object(router,"transition",new=step):
            result = router.play(item,fit.BASE,{},events=trace,recorded=receipt)
    return observed[0] if observed else None,result,attempts


def paired(rows):
    for item, terms, receipt in rows:
        view, base, _ = play(item,terms,receipt,lambda _:False)
        extra = (0,0,0)
        nudge = base
        if view is not None:
            again,nudge,attempts = play(item,terms,receipt,lambda _:True)
            assert again == view and len(attempts)==1
            extra = 1,int(view[0]),int(attempts[0]["admitted"])
        yield fit.world_label(item),view,base,nudge,extra


def compare(parts, rules):
    all_arms = {
        "fixed":lambda _:True,"append_any_polarity":lambda _:False,
        "append_same_polarity_only":lambda x:not x[0],
        "append_only_if_certifies":lambda x:not (x[4] and not x[5]),
        "learned":lambda x:gate.choose(x,rules),
    }
    result={}
    for mode, rows in parts.items():
        result[mode]={}
        for name, actor in all_arms.items():
            telemetry=Counter()
            for kind,view,_,_,extra in rows:
                if view is not None and not actor(view):
                    for field,value in zip(("attempts","same_polarity","admitted"),extra,strict=True):
                        telemetry[kind,field]+=value
            result[mode][name]={**gate.score(prior.select_rows(rows),actor),
                                "repair":router.sp.flatten(telemetry)}
    return result


def run():
    with patch.object(fit,"SEEDS",new=SEEDS),patch.object(gate,"FEATURES",new=FEATURES):
        train={k:list(paired(v)) for k,v in fit.synth("train",(5,6),510,2).items()}
        dev={k:list(paired(v)) for k,v in fit.synth("dev",(6,),390,3).items()}
        outcome,journal=gate.fit({k:prior.select_rows(v) for k,v in train.items()},
                                 {k:prior.select_rows(v) for k,v in dev.items()})
        test={k:list(paired(v)) for k,v in fit.synth("heldout",(7,8),460,3).items()}
        linked={f:{k:list(paired(v)) for k,v in p.items()} for f,p in prior.audit.samples()
                if f!="fresh_synthetic"}
    return {
        "scope":"Keep both claims within the original two-sign cap, admit one missing claim in addition to the planned claim, and preserve the normal next speaker, slot and verification credits. Abstract status from actual delivered signatures. One choice per episode.",
        "seed":SEEDS,"features":FEATURES,"rules":outcome,"fit":journal,
        "dev":compare(dev,outcome),"heldout":compare(test,outcome),
        "linked":{f:compare(p,outcome) for f,p in linked.items()},
    }


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
