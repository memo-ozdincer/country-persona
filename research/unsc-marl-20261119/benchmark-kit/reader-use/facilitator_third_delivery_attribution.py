"""Attribute the remaining three-delivery gap to the opening or the request and reply."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_third_delivery as delivery

route = delivery.route


def exact_tail(left, right, prior, terminal):
    # For each chair map, optimize the responder separately at each
    # private inventory, intended opening action, and heard request.
    maps = np.asarray(list(product(*(np.flatnonzero(row) for row in delivery.CHAIR_LEGAL))))
    opening = np.einsum("lr,la,rb,abm->rbm", prior, delivery.one_hot(left), delivery.one_hot(right), delivery.FIRST)
    heard = (1 - delivery.LOSS) * delivery.one_hot(maps) + delivery.LOSS * np.eye(4)[0]
    payoff = delivery.LAST @ terminal - delivery.SEND_COST
    conditional = np.einsum("rbm,pmq,mc->prbqc", opening, heard, payoff)
    feasible = np.where(delivery.FINAL_LEGAL[None], conditional, -np.inf)
    values = feasible.max(-1).sum(axis=(1, 2, 3)) - delivery.QUERY_COST[maps] @ opening.sum(axis=(0, 1))
    best = int(values.argmax())
    tail = left, right, maps[best], feasible[best].argmax(-1)
    fee = prior.sum(1) @ delivery.SEND_COST[left] + prior.sum(0) @ delivery.SEND_COST[right]
    mass, actual_cost = delivery.distribution(tail, prior)
    assert abs(mass @ terminal - actual_cost - (values[best] - fee)) < 1e-9
    return tail, len(maps)


def direct_replay(policy, prior, erase=False):
    left, right, chair, reply = policy
    mass = np.zeros(8)
    cost = 0.
    loss = delivery.LOSS
    for a, b in product(range(8), repeat=2):
        send_left, send_right = left[a], right[b]
        assert route.SEND[a, send_left] and route.SEND[b, send_right]
        for seen_a, seen_b, heard, seen_c in product((0, 1), repeat=4):
            weight = prior[a, b] * np.prod([(1 - loss) if x else loss for x in (seen_a, seen_b, heard, seen_c)])
            mask = route.BITS[send_left] * seen_a | route.BITS[send_right] * seen_b
            q = chair[mask]
            assert delivery.CHAIR_LEGAL[mask, q]
            c = reply[b, send_right, q if heard and not erase else 0]
            assert route.SEND[b, c]
            mass[mask | route.BITS[c] * seen_c] += weight
            cost += weight * (delivery.SEND_COST[send_left] + delivery.SEND_COST[send_right]
                              + delivery.QUERY_COST[q] + delivery.SEND_COST[c])
    return mass, cost


def audit(policy, prior, erase=False):
    analytical, fee = delivery.distribution(policy, prior, erase)
    direct, direct_fee = direct_replay(policy, prior, erase)
    assert np.allclose(analytical, direct, atol=1e-12, rtol=0) and abs(fee - direct_fee) < 1e-12


def run(path):
    saved = json.loads(path.read_text())
    learned = tuple(np.array(a) for a in saved["training"]["learned_query"]["policy"])
    report = {}
    for name in ("unifil", "myanmar"):
        points = np.asarray(saved["held"][name]["guarded"])
        for prior_label, original in saved["results"][name].items():
            prior = route.TEST_PRIORS[prior_label]
            rows = []
            for cell in original["orders"]:
                actual = delivery.archive.unama.reordered(points, cell["order"])
                reward = actual + (actual == 70) * delivery.COMPLETE_BONUS
                control = delivery.exact_independent(prior, reward)
                specialized_tail, count = exact_tail(*learned[:2], prior, reward)
                independent_then_tail, _ = exact_tail(*control[:2], prior, reward)
                audit(learned, prior)
                audit(learned, prior, erase=True)
                audit(control, prior)
                audit(specialized_tail, prior)
                audit(independent_then_tail, prior)
                calibrated = {
                    "learned_opening_exact_tail": delivery.measure(specialized_tail, prior, actual),
                    "independent_opening_exact_tail": delivery.measure(independent_then_tail, prior, actual),
                }
                assert calibrated["learned_opening_exact_tail"]["net"] >= cell["arms"]["learned_query"]["net"] - 1e-9
                assert calibrated["independent_opening_exact_tail"]["net"] >= original["exact_independent"]["net"] - 1e-9
                assert max(r["net"] for r in calibrated.values()) <= original["centralized_ceiling"] + 1e-9
                rows.append({"order": cell["order"], "arms": calibrated})
            averages = {arm: {key: sum(r["arms"][arm][key] for r in rows) / len(rows)
                              for key in ("net", "strict_complete", "guarded_points", "cost")}
                        for arm in rows[0]["arms"]}
            report.setdefault(name, {})[prior_label] = {"chair_maps": count, "averages": averages, "orders": rows}
    return {"scope": "Hindsight diagnostic. Both backends optimize on the evaluation prior and bank with the two "
                     "opening policies fixed. Independent event enumeration checks each reported backend and the ablation.",
            "results": report, "sha256": {p.name: sha256(p.read_bytes()).hexdigest()
                                        for p in (Path(__file__), Path(delivery.__file__), path)}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit", type=Path)
    print(json.dumps(run(cli.parse_args().fit), indent=2, ensure_ascii=False))
