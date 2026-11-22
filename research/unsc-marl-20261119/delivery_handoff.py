"""Learn floor handoff after an ordinary signed message loses a proposition."""
import json
from unittest.mock import patch

import ordinary_resend as core

fit, router, gate = core.fit, core.router, core.gate
SEEDS = {"train": 967993, "dev": 817229, "heldout": 456127, "archive": fit.SEEDS["archive"]}
FEATURES = (
    "nothing_arrived", "lost_acceptance", "lost_exclusion", "lost_multiple",
    "acceptance_matches_peer_offer", "sender_has_public_live_offer", "peer_has_public_live_offer",
    "at_most_three_live", "peer_has_check_credit", "sender_has_check_credit",
    "query_credit_left", "at_least_four_slots", "sender_prior_loss",
)


def play(item, terms, receipt, yield_floor, events=None):
    observations, alterations = [], []
    prior_loss = [False,False]
    full = (1<<item[0][0])-1
    with fit.protocol(terms):
        original = router.transition

        def transition(item,state,action,choices,regular,recorded=None):
            after,checked,event = original(item,state,action,choices,regular,recorded)
            if action != core.ROUTINE:
                return after,checked,event
            sent = core.intended(state,regular)
            if not any(sent):
                return after,checked,event
            _, owner, slot, _ = state
            peer = 1-owner
            ledger, next_role, finish, credit = after
            yes = sent[0]&~ledger[2*owner]
            no = sent[1]&~ledger[2*owner+1]
            if not (yes|no):
                return after,checked,event
            if (not observations and next_role==owner and finish < item[0][0]+1
                    and not router.sp.terminal(ledger,full)):
                live = full & ~(ledger[1] | ledger[3])
                x = (sent==(yes,no),bool(yes),bool(no),(yes|no).bit_count()>1,
                     bool(yes&ledger[2*peer]),bool(live&ledger[2*owner]),bool(live&ledger[2*peer]),
                     live.bit_count()<=3,bool(credit&(1<<peer)),bool(credit&(1<<owner)),
                     bool(credit&fit.selection.reuse.ROUTER.CREDIT),item[0][0]+1-finish>=4,
                     prior_loss[owner])
                observations.append(x)
                if yield_floor(x):
                    after = ledger,peer,finish,credit
                    alterations.append({"slot":slot,"old_next":next_role,"new_next":peer,
                                        "sent":sent,"missing": (yes,no),"ledger":ledger})
            prior_loss[owner] = True
            return after,checked,event

        with patch.object(router,"transition",new=transition):
            result = router.play(item,fit.BASE,{},recorded=receipt,events=events)
    return observations[0] if observations else None,result,alterations


def paired(rows):
    for item, terms, receipt in rows:
        obs,fixed,_ = play(item,terms,receipt,lambda _:False)
        other = fixed
        if obs is not None:
            matching,other,edits = play(item,terms,receipt,lambda _:True)
            assert obs==matching and len(edits)==1
        yield fit.world_label(item),obs,fixed,other


def compare(panels,rules):
    return {regime:{
        "fixed":gate.score(rows,lambda _:True),
        "always_handoff_on_loss":gate.score(rows,lambda _:False),
        "handoff_if_nothing_arrived":gate.score(rows,lambda obs:not obs[0]),
        "handoff_if_peer_affirms_missing_acceptance":gate.score(rows,lambda obs:not obs[4]),
        "learned":gate.score(rows,lambda obs:gate.choose(obs,rules)),
    } for regime,rows in panels.items()}


def cohort(panels):
    return {name:list(paired(rows)) for name,rows in panels.items()}


def run():
    with patch.object(fit,"SEEDS",new=SEEDS),patch.object(gate,"FEATURES",new=FEATURES):
        train=cohort(fit.synth("train",(5,6),560,2))
        dev=cohort(fit.synth("dev",(6,),410,3))
        rules,journal=gate.fit(train,dev)
        test=cohort(fit.synth("heldout",(7,8),470,3))
        families={name:cohort(rows) for name,rows in core.audit.samples() if name!="fresh_synthetic"}
    return {"scope":"At first eligible post-delivery decision, change only which role speaks next. Same actual payload, same admission, slot, local state and verification budgets. Clean cases are unaffected.",
            "seeds":SEEDS,"features":FEATURES,"rules":rules,"fit":journal,
            "development":compare(dev,rules),"heldout":compare(test,rules),
            "workshops":{name:compare(parts,rules) for name,parts in families.items()}}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
