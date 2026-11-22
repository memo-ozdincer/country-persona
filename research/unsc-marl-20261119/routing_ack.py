"""Gate learned routing changes with acknowledgements from the actor's own sends."""
from collections import Counter
from contextlib import contextmanager
import json
from pathlib import Path
import sys
from unittest.mock import patch

import routing_audit as audit
import routing_fit as fit

router = fit.router
ROUTINE = fit.selection.reuse.ROUTER.ROUTINE
PROTOCOL = fit.protocol
ACK_RULES = ("last_send_missing", "any_missing", "missing_live")
SHARED_ACK_RULES = ("public_ack", "public_ack_set_deferral", "peer_ack_set_deferral")
BASE = fit.VENEZUELA/"evidence/sequential-routing/results.json"


def play(item, terms, receipt, actor, rule):
    history = [[], []]
    local_acknowledgements = Counter()
    acting = 0
    eligible = 0

    @contextmanager
    def observe_protocol(terms):
        nonlocal acting
        with PROTOCOL(terms):
            available, transition = router.available, router.transition

            def observe(item, state):
                nonlocal acting
                acting = state[1]
                return available(item, state)

            def send(item, state, action, legal, bundle, recorded=None):
                after, checked, event = transition(item, state, action, legal, bundle, recorded)
                if action != ROUTINE:
                    return after, checked, event
                frame, current, ordinary, _, decode = bundle
                if ordinary[0] == fit.episode.delay.CHECK:
                    return after, checked, event
                role = state[1]
                planned = router.routing.step(frame[0], current, *ordinary, 1)[0]
                index = role * 2
                wanted = tuple(decode(planned[i]) & ~state[0][i] for i in (index,index+1))
                if any(wanted):
                    missing = (wanted[0]&~after[0][index]) | (wanted[1]&~after[0][index+1])
                    history[role].append(missing)
                    local_acknowledgements["sent"] += 1
                    local_acknowledgements["missing"] += bool(missing)
                return after, checked, event

            with patch.object(router, "available", new=observe), patch.object(router, "transition", new=send):
                yield

    def decision(x, legal, default):
        nonlocal eligible
        picked = actor(x, legal, default)
        if picked == default:
            return default
        past = history[acting]
        if callable(rule):
            allow = rule(x, default, picked, bool(any(past)), bool(any(history[1-acting])))
        elif rule == "unfiltered":
            allow = True
        elif rule == "last_send_missing":
            allow = bool(past and past[-1])
        elif rule == "missing_live":
            # Temporary silence after a failure is informative only if the
            # public state still has multiple packages to resolve.
            allow = any(past) and not bool(x[fit.FEATURES.index("few_live")])
        elif rule in SHARED_ACK_RULES:
            peer_failed = any(history[1-acting])
            status = bool(peer_failed or (rule != "peer_ack_set_deferral" and any(past)))
            allow = status and (rule == "public_ack" or
                                (default, picked) in audit.RULES["set_deferral"])
        else:
            allow = any(past)
        eligible += allow
        return picked if allow else default

    with patch.object(fit, "protocol", new=observe_protocol):
        result, changes = fit.simulate(item, terms, receipt, decision)
    assert eligible == len(changes)
    return result, changes, local_acknowledgements


def compare(rows, actor, shared=False):
    names = ("fixed", "unfiltered", *(SHARED_ACK_RULES if shared else ACK_RULES))
    metrics = {name: Counter() for name in names}
    changes = {name: Counter() for name in names}
    for item, terms, receipt in rows:
        baseline = None
        kind = fit.world_label(item)
        for name in names:
            active = fit.no_override if name == "fixed" else actor
            result, overrides, counts = play(item, terms, receipt, active, name)
            if baseline is None:
                baseline = result[0]
            changes[name][kind,str(baseline),str(result[0])] += 1
            for field, value in zip(("certificate","slots","checks","queries","answers","scope"),
                                    result, strict=True):
                metrics[name][kind,field] += value
            metrics[name][kind,"presentations"] += 1
            metrics[name][kind,"overrides"] += len(overrides)
            metrics[name][kind,"missing_sends"] += counts["missing"]
            metrics[name][kind,"ordinary_sends"] += counts["sent"]
    flatten = router.sp.flatten
    return {name: {"counts": flatten(metrics[name]), "paired": flatten(changes[name])} for name in names}


def evaluate(results, shared=False):
    actor = audit.actors(results)["full_actor"]
    comparisons = {}
    for family, panels in audit.samples():
        comparisons[family] = {kind: compare(rows, actor, shared) for kind, rows in panels.items()}
        assert all(r["counts"][k] == 0 for name, r in comparisons[family]["clean"].items()
                   if name in (*ACK_RULES, *SHARED_ACK_RULES)
                   for k in ("agreement/overrides","impasse/overrides"))
    return {
        "scope": ("Post-hoc safeguards with one public complete/incomplete status bit per signed ordinary send. Schedules learn no new weights."
                  if shared else "Post-hoc safeguards on the frozen shared actor. Ordinary signed sends have role-local acknowledgements. Neither the other role's intention nor the fault regime is given to the actor."),
        "comparisons": comparisons,
    }


if __name__ == "__main__":
    shared = "--shared" in sys.argv
    print(json.dumps(evaluate(json.loads(BASE.read_text()), shared), indent=2))
