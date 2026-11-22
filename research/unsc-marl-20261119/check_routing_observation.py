"""Check router observations under changes to hidden peer state and future delivery."""
import json
from collections import Counter

import numpy as np

import routing_fit as fit


def alternate(item, state):
    row, tape = item
    width, truth, local, opening, scope = row
    public, actor, _, _ = state
    peer = 1-actor
    full = (1 << width)-1
    signed_yes, signed_no = public[2*peer:2*peer+2]
    unknown = full&~(signed_yes|signed_no)
    inverted = signed_yes | (unknown&~truth[peer])
    changed_truth, changed_local, changed_scope = list(truth), list(local), list(scope)
    changed_truth[peer] = inverted
    visible = local[peer][0] | local[peer][1] | signed_yes | signed_no
    changed_local[peer] = inverted&visible, (full^inverted)&visible
    changed_scope[peer] = 0
    return (width, tuple(changed_truth), tuple(changed_local), opening, tuple(changed_scope)), {
        k: tuple(full^mask for mask in bits) for k, bits in tape.items()
    }


def verify():
    counts = Counter()
    for regime, cohort in fit.synth("heldout", (7,), 40, 3).items():
        for item, terms, receipt in cohort:
            width, _, local, opening, _ = item[0]
            world = fit.router.sp.opened(opening, local), 1, 0, 7
            with fit.protocol(terms):
                while fit.terminal_record(item, world) is None:
                    obs, legal, ordinary = fit.router.available(item, world)
                    default = fit.router.default(obs, fit.BASE)
                    changed = alternate(item, world)
                    other_obs, other_legal, other_ordinary = fit.router.available(changed, world)
                    other_default = fit.router.default(other_obs, fit.BASE)
                    assert (obs, legal, default) == (other_obs, other_legal, other_default)
                    assert np.array_equal(fit.vector(item, world, legal, ordinary, default),
                                          fit.vector(changed, world, other_legal, other_ordinary, other_default))
                    counts[regime,"states"] += 1
                    counts[regime,"multiple_legal"] += len(legal)>1
                    counts[regime,"changed_peer_truth"] += item[0][1]!=changed[0][1]
                    world, _, _ = fit.router.transition(item, world, default, legal, ordinary, receipt)
    return {"scope": "Actor views in sampled fixed-policy trajectories; keep each current public ledger and acting role state fixed while changing hidden observations, peer mandate, and fault tape.",
            "counts": fit.router.sp.flatten(counts)}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
