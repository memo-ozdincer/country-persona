"""Find a two-context witness against pair-optimized fixed responders."""
from collections import defaultdict
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path

import numpy as np

import context_audit as first

HERE = Path(__file__).resolve().parent
o, D, e = first.o, first.D, first.e
data, selector = first.data, first.q
BITS = first.BITS


def best_response(points, states, openings, holder, targets):
    groups = defaultdict(list)
    for index, target in enumerate(targets):
        groups[holder, openings[1], target].append(index)
    responses = [None] * len(states)
    total = -float(sum(D.QUERY_COST[target] for target in targets))
    for (r, sent, heard), indices in groups.items():
        options = np.flatnonzero(D.FINAL_LEGAL[r, 0, 0])
        score, choice = max((sum(points[states[index] | BITS[answer]] - D.SEND_COST[answer]
                                 for index in indices), -int(answer)) for answer in options)
        for index in indices:
            responses[index] = -choice
        total += float(score)
    return {"targets": targets, "reply": responses, "tail_net": total}


def compare(points, law, params, open_model, count):
    estimate = data.singleton(points)
    openers = o.replan.study.opening(estimate, law, open_model)
    coords = tuple(points[i] for i in (0, 1, 2, 4))
    _, policies, forecast, _ = selector.choose(coords, openers, law, params)
    floor = forecast["quiet"]["released"]
    valid = [a for a in policies if forecast[a]["released"] >= floor - 1e-10]
    picked = max(valid, key=lambda a: (forecast[a]["net"], a == "quiet"))
    result = []
    for left, right in np.ndindex(law.shape):
        if law[left, right] <= 0:
            continue
        a, b = (int(openers[i][v]) for i, v in enumerate((left, right)))
        for delivery in combinations(product((0, 1), repeat=2), count):
            states = [(BITS[a] if sent[0] else 0) | (BITS[b] if sent[1] else 0)
                      for sent in delivery]
            if len(set(states)) != count:
                continue
            routes = [first.event(points, state, right, b, policies[picked]) for state in states]
            if len({row["ask"] for row in routes} - {0}) < 2:
                continue
            exact_fixed = {}
            for card in range(4):
                targets = [card if D.CHAIR_LEGAL[state, card] else 0 for state in states]
                exact_fixed[str(card)] = best_response(points, states, (a, b), right, targets)
            learned = sum(x["tail_net"] for x in routes)
            difference = learned - max(x["tail_net"] for x in exact_fixed.values())
            if difference <= 1e-10:
                continue
            oracle = max(best_response(points, states, (a, b), right, emitted)["tail_net"]
                         for emitted in product(*(np.flatnonzero(D.CHAIR_LEGAL[state]) for state in states)))
            assert learned <= oracle + 1e-10
            result.append({"inventory": [left, right], "openers": [a, b], "delivery": delivery,
                           "state": states, "learned": routes, "fixed": exact_fixed,
                           "pair_net_margin": difference, "exact_pair_net": oracle,
                           "modeled_inventory_mass": float(law[left, right])})
    return {"policy": picked, "paired_witnesses": len(result), "first": result[0] if result else None}


def run(count):
    params = tuple([np.array(a) for a in e.read(p)["parameters"]]
                   for p in (HERE.parents[1] / "fit.json", HERE.parent / "sparse-results.json"))
    open_model = e.read(o.replan.study.OLD)["training"]["budget_fit"]
    result = {name: {label: compare(points, prior, params, open_model, count) for label, prior in o.R.TEST_PRIORS.items()}
              for name, points in data.banks().items()}
    files = (Path(__file__), HERE / "matched-protocol.md", HERE / "triplet-protocol.md", Path(first.__file__), Path(selector.__file__),
             HERE.parents[1] / "fit.json", HERE.parent / "sparse-results.json", *data.FILES.values())
    return {"public_states_per_witness": count, "cases": result, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("states", type=int, choices=(2, 3))
    print(json.dumps(run(parser.parse_args().states), indent=2))
