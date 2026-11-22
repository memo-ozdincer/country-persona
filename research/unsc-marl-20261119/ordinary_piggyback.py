"""Test putting one acknowledged missing sign into a spare ordinary packet slot."""
from collections import Counter
import json
from unittest.mock import patch

import ordinary_resend as prior

fit, gate, router = prior.fit, prior.gate, prior.router
SEEDS = {"train": 210299, "dev": 404833, "heldout": 869521, "archive": fit.SEEDS["archive"]}
FEATURES = (
    "added_acceptance", "added_exclusion", "added_would_complete_agreement",
    "combined_would_certify", "ordinary_would_certify", "few_live",
    "ordinary_includes_peer_offer", "own_receipt_cached", "has_at_least_three_slots",
    "request_credit_available",
)


def play(item, terms, receipt, decide, events=None):
    observations, addons = [], []
    pending = [(0,0), (0,0)]
    full = (1<<item[0][0])-1
    with fit.protocol(terms):
        execute = router.transition

        def send(item, state, action, choices, regular, recorded=None):
            if action != prior.ROUTINE:
                return execute(item, state, action, choices, regular, recorded)
            normal = prior.intended(state, regular)
            if not any(normal):
                return execute(item, state, action, choices, regular, recorded)
            public, role, turn, credit = state
            peer, index = 1-role, 2*role
            viable = full & ~(public[1] | public[3])
            sent = normal
            added = (0,0)
            if not observations and (normal[0]|normal[1]).bit_count()==1:
                missing_yes, missing_no = pending[role]
                candidate = (0,missing_no&viable) if normal[0] else (
                    missing_yes&viable&~public[index],0)
                assert (candidate[0]|candidate[1]).bit_count()<=1
                if any(candidate):
                    combined = normal[0]|candidate[0], normal[1]|candidate[1]
                    ordinary_proof = router.sp.record(
                        router.sp.record(public,role,normal[0],True),role,normal[1],False)
                    combined_proof = router.sp.record(
                        router.sp.record(public,role,combined[0],True),role,combined[1],False)
                    view = (bool(candidate[0]),bool(candidate[1]), bool(candidate[0]&public[2*peer]),
                            router.sp.terminal(combined_proof,full),router.sp.terminal(ordinary_proof,full),
                            viable.bit_count()<=3,bool(normal[0]&public[2*peer]),
                            bool(credit & (fit.selection.reuse.CACHE<<role)),item[0][0]+1-turn>=3,
                            bool(credit & fit.selection.reuse.ROUTER.CREDIT))
                    observations.append(view)
                    if decide(view):
                        sent, added = combined, candidate
            if any(added):
                frame, coded, ordinary, _, _ = regular
                _, following, last, remaining = router.routing.step(frame[0],coded,*ordinary,1)
                assert following==peer and last==turn+1 and remaining==credit
                assert not (sent[0]&~item[0][1][role] or sent[1]&item[0][1][role])
                after, delivered = fit.episode.delay.authorized_retry(
                    item,(public,peer,turn,credit),role,*sent)
                assert after[1:] == (following,last,remaining)
                checked, event = False,None
                addons.append({"slot":turn,"role":role,"normal":normal,"resend":added,
                               "received":((added[0]&delivered[0])|(added[1]&delivered[1])).bit_count()})
            else:
                after,checked,event = execute(item,state,action,choices,regular,recorded)
            pending[role] = sent[0]&~after[0][index],sent[1]&~after[0][index+1]
            return after,checked,event

        with patch.object(router,"transition",new=send):
            result = router.play(item,fit.BASE,{},events=events,recorded=receipt)
    return observations[0] if observations else None,result,addons


def paired(rows):
    for item, terms, receipt in rows:
        view, fixed, _ = play(item, terms, receipt, lambda _:False)
        retry, counts = fixed, (0,0,0)
        if view is not None:
            check, retry, added = play(item,terms,receipt,lambda _:True)
            assert check==view and len(added)==1
            counts = 1,1,added[0]["received"]
        yield fit.world_label(item),view,fixed,retry,counts


def evidence(items, rules):
    result = {}
    for regime, rows in items.items():
        result[regime] = {}
        for arm, policy in (
                ("fixed", lambda _:True),
                ("always_add",lambda _:False),
                ("add_if_only_combined_certifies",lambda obs:not(obs[3] and not obs[4])),
                ("learned",lambda obs: gate.choose(obs,rules))):
            counts = Counter()
            for case, view, _, _, added in rows:
                if view is not None and not policy(view):
                    counts[case,"extra_signs_attempted"] += added[0]
                    counts[case,"extra_signs_admitted"] += added[2]
            result[regime][arm] = {**gate.score(prior.select_rows(rows),policy),
                                   "added":router.sp.flatten(counts)}
    return result


def run():
    with patch.object(fit,"SEEDS",new=SEEDS), patch.object(gate,"FEATURES",new=FEATURES):
        train = {k:list(paired(v)) for k,v in fit.synth("train",(5,6),520,2).items()}
        dev = {k:list(paired(v)) for k,v in fit.synth("dev",(6,),400,3).items()}
        rules, journal = gate.fit({k:prior.select_rows(v) for k,v in train.items()},
                                  {k:prior.select_rows(v) for k,v in dev.items()})
        test = {k:list(paired(v)) for k,v in fit.synth("heldout",(7,8),440,3).items()}
        archives = {family:{k:list(paired(v)) for k,v in parts.items()}
                    for family,parts in prior.audit.samples() if family!="fresh_synthetic"}
    return {"scope":"Add at most one prior missing sign to a planned one-sign message of the opposite polarity. Both travel on the same tape and consume the same ordinary slot. At most one policy decision per episode.",
            "seeds":SEEDS,"features":FEATURES,"rules":rules,"fit":journal,
            "development":evidence(dev,rules),"heldout":evidence(test,rules),
            "workshops":{f:evidence(parts,rules) for f,parts in archives.items()}}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
