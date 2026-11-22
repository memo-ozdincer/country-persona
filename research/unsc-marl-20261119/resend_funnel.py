"""Measure why the fixed router offers few opportunities for same-turn repair."""
from collections import Counter
import json
from unittest.mock import patch

import ordinary_piggyback as payload
import ordinary_resend as core

fit, router = core.fit, core.router


def counts(rows):
    report = Counter()
    for item, terms, receipt in rows:
        pending = [(0,0),(0,0)]
        full = (1 << item[0][0])-1
        group = fit.world_label(item)
        report[group,"episodes"] += 1
        with fit.protocol(terms):
            execute = router.transition

            def transition(item,state,action,choices,regular,recorded=None):
                after,checked,event = execute(item,state,action,choices,regular,recorded)
                if action != core.ROUTINE:
                    return after,checked,event
                public, role, _, _ = state
                eligible = full & ~(public[1]|public[3])
                yes,no = pending[role]
                missing = yes&eligible&~public[2*role],no&eligible
                normal = core.intended(state,regular)
                if any(missing):
                    report[group,"ordinary_with_pending"] += 1
                    if not any(normal):
                        report[group,"no_new_ordinary_payload"] += 1
                    else:
                        report[group,"new_ordinary_payload"] += 1
                        if (normal[0]|normal[1]).bit_count()==2:
                            report[group,"both_claim_slots_used"] += 1
                        elif (normal[0] and missing[1]) or (normal[1] and missing[0]):
                            report[group,"opposite_polarity_spare"] += 1
                        else:
                            report[group,"only_same_polarity_spare"] += 1
                if any(normal):
                    index=2*role
                    pending[role] = normal[0]&~after[0][index],normal[1]&~after[0][index+1]
                return after,checked,event

            with patch.object(router,"transition",new=transition):
                router.play(item, fit.BASE, {}, recorded=receipt)
    return router.sp.flatten(report)


def run():
    result = {}
    with patch.object(fit,"SEEDS",new=payload.SEEDS):
        result["synthetic"] = {k:counts(rows) for k,rows in fit.synth("heldout",(7,8),440,3).items()}
    for family, panels in core.audit.samples():
        if family!="fresh_synthetic":
            result[family]={k:counts(rows) for k,rows in panels.items()}
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
