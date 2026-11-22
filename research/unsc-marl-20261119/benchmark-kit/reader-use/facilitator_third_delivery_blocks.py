"""Improve opening and reply policies in alternating exact blocks on fitting cases only."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_third_delivery_attribution as audit

delivery = audit.delivery
route = delivery.route
MAX_STEPS = 12


def opening_optimum(chair, reply, prior, terminal):
    legal = [np.flatnonzero(row) for row in route.SEND]
    maps = np.asarray(list(product(*legal)))
    heard = (1 - delivery.LOSS) * delivery.one_hot(chair) + delivery.LOSS * np.eye(4)[0]
    tail = delivery.LAST @ terminal - delivery.SEND_COST
    value = np.einsum("abm,mq,rbqc,mc->rab", delivery.FIRST, heard, delivery.one_hot(reply), tail)
    value -= np.einsum("abm,m->ab", delivery.FIRST, delivery.QUERY_COST[chair])
    value -= delivery.SEND_COST[:, None] + delivery.SEND_COST[None, :]
    outcomes = np.einsum("rlb,lr->rb", value[:, maps[0]], prior)
    compared = np.einsum("rplb,lr->prb", value[:, maps], prior)
    assert np.allclose(outcomes, compared[0])
    allowed = np.where(route.SEND[None, :, :], compared, -np.inf)
    best = int(allowed.max(-1).sum(-1).argmax())
    return maps[best], allowed[best].argmax(-1), chair, reply


def value(policy, prior, terminal):
    mass, fee = delivery.distribution(policy, prior)
    return float(mass @ terminal - fee)


def optimize(start, prior, terminal):
    state = start
    trace = []
    for _ in range(MAX_STEPS):
        before = value(state, prior, terminal)
        tail, _ = audit.exact_tail(*state[:2], prior, terminal)
        after_tail = value(tail, prior, terminal)
        candidate = opening_optimum(*tail[2:], prior, terminal)
        after_opening = value(candidate, prior, terminal)
        assert before <= after_tail + 1e-9 and after_tail <= after_opening + 1e-9
        trace.append({"before": before, "after_tail": after_tail, "after_opening": after_opening})
        if after_opening <= after_tail + 1e-10:
            # Keep the already optimized tail if an equally valued opening
            # update would arbitrarily move it to a new state.
            return tail, trace
        state = candidate
    return state, trace


def run(path):
    saved = json.loads(path.read_text())
    fitting, held = delivery.data()
    terminal = np.zeros(8)
    for case in fitting.values():
        scores = np.array(case["guarded"])
        orders = delivery.archive.calibrated_orders(scores)
        weighted = scores + (scores == 70) * delivery.COMPLETE_BONUS
        terminal += np.mean([delivery.archive.unama.reordered(weighted, o) for o in orders], axis=0) / len(fitting)
    train_prior = route.TEST_PRIORS["uniform"]
    learned = tuple(np.asarray(p) for p in saved["training"]["learned_query"]["policy"])
    independent = delivery.exact_independent(train_prior, terminal)
    result = {}
    for key, starting in (("gradient_start", learned), ("independent_start", independent)):
        policy, trace = optimize(starting, train_prior, terminal)
        result[key] = {"trace": trace, "policy": [a.tolist() for a in policy],
                       "fit_net": value(policy, train_prior, terminal)}
    selection = max(result, key=lambda name: result[name]["fit_net"])
    chosen = tuple(np.asarray(p) for p in result[selection]["policy"])
    testing = {}
    for name, row in held.items():
        points = np.array(row["guarded"])
        orders = delivery.archive.calibrated_orders(points)
        testing[name] = {}
        for label in ("uniform", "correlated_duplicates"):
            prior = route.TEST_PRIORS[label]
            audit.audit(chosen, prior)
            cells = []
            for order in orders:
                target = delivery.archive.unama.reordered(points, order)
                cells.append({"order": order, "chosen": delivery.measure(chosen, prior, target),
                              "erased": delivery.measure(chosen, prior, target, erase=True)})
            means = {arm: {metric: sum(c[arm][metric] for c in cells) / len(cells)
                           for metric in ("net", "strict_complete", "guarded_points", "cost")}
                     for arm in ("chosen", "erased")}
            testing[name][label] = {"means": means, "orders": cells,
                                    "exact_independent": saved["results"][name][label]["exact_independent"]["net"],
                                    "gradient_fit": saved["results"][name][label]["means"]["learned_query"]["net"]}
    return {"scope": "Follow-up after inspecting the original fit. Optimize blocks on the same fitting bank. "
                     "Select initialization by fitting return. The test dockets are known and no test values enter either optimizer.",
            "fitting_terminal_reward": terminal.tolist(), "fit": result, "selected": selection, "tests": testing,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (
                Path(__file__), Path(delivery.__file__), Path(audit.__file__), path)}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fit", type=Path)
    print(json.dumps(run(p.parse_args().fit), indent=2, ensure_ascii=False))
