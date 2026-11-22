"""Train a delegate to spend one ordinary slot on resending verified evidence."""
from collections import Counter
import json
from unittest.mock import patch

import routing_audit as audit
import routing_fit as fit
import query_gate as gate

router, episode = fit.router, fit.episode
ROUTINE = fit.selection.reuse.ROUTER.ROUTINE
FEATURES = (
    "resend_would_certify", "has_acceptance", "has_exclusion", "peer_accepts_missing_positive",
    "already_planned_same_sign", "ordinary_would_verify", "multiple_missing", "few_live",
    "at_least_three_slots", "query_still_available", "ordinary_has_novel_sign",
)
SEEDS = {"train": 604387, "dev": 269233, "heldout": 617889, "archive": fit.SEEDS["archive"]}


def intended(state, observation):
    frame, coded_state, regular, _, decode = observation
    if regular[0] == episode.delay.CHECK:
        return 0,0
    proof = router.routing.step(frame[0], coded_state, *regular, 1)[0]
    index = 2*state[1]
    return tuple(decode(proof[k]) & ~state[0][k] for k in (index, index+1))


def observe(item, state, missing, regular, normal):
    public, actor, slot, credit = state
    width = item[0][0]
    full = (1<<width)-1
    live = full & ~(public[1] | public[3])
    yes,no = missing
    claimed = router.sp.record(router.sp.record(public, actor, yes, True), actor, no, False)
    return (router.sp.terminal(claimed, full), bool(yes), bool(no),
            bool(yes & public[2*(1-actor)]), bool((yes & normal[0]) | (no & normal[1])),
            regular[2][0] == episode.delay.CHECK, (yes|no).bit_count()>1,
            live.bit_count()<=3, width+1-slot>=3, bool(credit & fit.selection.reuse.ROUTER.CREDIT),
            bool((normal[0]&~yes) | (normal[1]&~no)))


def run_episode(item, terms, receipt, choose, trace=None):
    width, truth, local, opening, _ = item[0]
    full = (1 << width)-1
    state = router.sp.opened(opening, local), 1, 0, 7
    pending = [(0,0), (0,0)]
    checks = queries = answers = scoped = 0
    attempted = resends = added = 0
    first = None
    with fit.protocol(terms):
        while state[2] < width+1 and not router.sp.terminal(state[0], full):
            current, actor, slot, credit = state
            index = 2*actor
            alive = full & ~(current[1] | current[3])
            known_yes, known_no = pending[actor]
            missing = known_yes&alive&~current[index], known_no&alive
            obs, choices, regular = router.available(item, state)
            default = router.default(obs, fit.BASE)
            normal = intended(state, regular) if default == ROUTINE else (0,0)
            send_again = False
            if default == ROUTINE and any(missing) and first is None:
                first = observe(item, state, missing, regular, normal)
                send_again = choose(first)
            if send_again:
                yes,no = missing
                assert not (yes & ~truth[actor] or no & truth[actor])
                assert (yes|no).bit_count()<=2
                after, delivered = episode.delay.authorized_retry(
                    item, (current, 1-actor, slot, credit), actor, yes, no)
                assert after[1:] == (1-actor, slot+1, credit)
                checked, event = False, None
                pending[actor] = yes&~delivered[0], no&~delivered[1]
                resends += 1
                attempted += (yes|no).bit_count()
                added += (delivered[0]|delivered[1]).bit_count()
            else:
                after, checked, event = router.transition(item, state, default, choices, regular, receipt)
                if any(normal):
                    pending[actor] = normal[0]&~after[0][index], normal[1]&~after[0][index+1]
                scoped += default>=router.MATCH_SCOPE
            checks += checked
            queries += event is not None
            answers += bool(event and event["admitted"])
            if trace is not None:
                trace.append({"slot": slot, "role": actor, "default": default,
                              "resend": send_again, "pending_before": missing,
                              "ordinary_intent": normal, "ledger_after": after[0], "query": event})
            state = after
    assert all(not (state[0][2*r] & ~menu or state[0][2*r+1] & menu) for r,menu in enumerate(truth))
    return first, (router.sp.terminal(state[0], full),state[2],checks,queries,answers,scoped), (
        resends, attempted, added)


def paired(rows):
    for item, terms, receipt in rows:
        view, fixed, _ = run_episode(item, terms, receipt, lambda _: False)
        alternative, counts = fixed, (0,0,0)
        if view is not None:
            replay, alternative, counts = run_episode(item, terms, receipt, lambda _: True)
            assert replay == view and counts[0]==1
        yield fit.world_label(item), view, fixed, alternative, counts


def select_rows(rows):
    return [example[:4] for example in rows]


def outcomes(panels, rules):
    result = {}
    arms = {"fixed": lambda _: True, "always_resend": lambda _: False,
            "resend_if_certifies": lambda obs: not obs[0],
            "learned": lambda obs: gate.choose(obs, rules)}
    for condition, rows in panels.items():
        result[condition] = {}
        for name, decision in arms.items():
            metrics = gate.score(select_rows(rows), decision)
            resend_counts = Counter()
            for case, view, _, _, counts in rows:
                if view is not None and not decision(view):
                    for label,value in zip(("resends","propositions_attempted","propositions_admitted"),
                                           counts, strict=True):
                        resend_counts[case,label] += value
            result[condition][name] = {**metrics,"resend": router.sp.flatten(resend_counts)}
    return result


def run():
    with patch.object(fit,"SEEDS",new=SEEDS), patch.object(gate,"FEATURES",new=FEATURES):
        train = {k:list(paired(rows)) for k,rows in fit.synth("train",(5,6),450,2).items()}
        dev = {k:list(paired(rows)) for k,rows in fit.synth("dev",(6,),360,3).items()}
        rules, journal = gate.fit({k:select_rows(v) for k,v in train.items()},
                                  {k:select_rows(v) for k,v in dev.items()})
        test = {k:list(paired(rows)) for k,rows in fit.synth("heldout",(7,8),430,3).items()}
        archived = {family: {k:list(paired(rows)) for k,rows in panels.items()}
                    for family,panels in audit.samples() if family!="fresh_synthetic"}
    return {"scope": "One possible resend at the first eligible ordinary turn. The actor uses only its own undelivered signed evidence and public state. No extra turn, lookup, or metadata channel.",
            "seeds": SEEDS,"features": FEATURES,"rules": rules,"fit": journal,
            "development": outcomes(dev,rules),"heldout": outcomes(test,rules),
            "workshops": {family:outcomes(parts,rules) for family,parts in archived.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
