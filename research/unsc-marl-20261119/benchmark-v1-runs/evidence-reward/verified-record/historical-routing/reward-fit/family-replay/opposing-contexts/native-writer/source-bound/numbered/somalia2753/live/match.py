"""Select a Somalia stress witness against fixed routing with a matched responder."""
from hashlib import sha256
from itertools import combinations, product
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import evaluate_somalia as q

n, t, a, o, r = q.n, q.t, q.a, q.o, q.route
e, D = t.e, r.D
BITS = n.BITS
TOL = 1e-10


def best_fixed(bank, holder, prior_send, states):
    candidates = {}
    for constant in range(4):
        targets = [constant if D.CHAIR_LEGAL[state, constant] else 0 for state in states]
        replies = {}
        for heard in set(targets):
            group = [mask for mask, emitted in zip(states, targets) if emitted == heard]
            options = np.flatnonzero(D.FINAL_LEGAL[holder, 0, 0])
            value, first = max((sum(bank[state | BITS[a]] - D.SEND_COST[a] for state in group), -int(a))
                               for a in options)
            replies[heard] = -first
        actions = [replies[h] for h in targets]
        end = [state | BITS[action] for state, action in zip(states, actions)]
        cost = sum(D.QUERY_COST[ask] + D.SEND_COST[action] for ask, action in zip(targets, actions))
        candidates[str(constant)] = {"query": targets, "reply": actions, "receipt": end,
                                     "points": sum(bank[m] for m in end), "net": float(sum(bank[m] for m in end) - cost)}
    return candidates


def run():
    pinned = t.HERE / "numeric-results.json"
    bank = np.array(n.read(pinned)["score_banks"]["native"])
    calibrations = {i: bank[i] for i in range(7) if i != 3}
    singles = r.f.views(bank)["4"]
    original = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    matches = []
    simple = {}
    for label, (law, _) in a.laws().items():
        opening = o.replan.study.opening(singles, law, original)
        mass = o.opening(*opening, law)
        rows = r.evaluate_locked(calibrations, bank[3], law, opening, mass, {})
        (index, kind), adaptive = rows["interval_team"]
        if label == "asymmetric":
            witness = n.read(pinned)["dispatcher_witnesses"]["asymmetric"]
            simple = {k: witness[k] for k in ("world", "delivery")}
            simple["routes"] = {k: v for k, v in witness["routes"].items()
                                if k in ("interval_team", "interval_fixed")}
            for output in simple["routes"].values():
                del output["record"]
        chair, reply = adaptive
        for left, right in np.ndindex(law.shape):
            if law[left, right] <= 0:
                continue
            attempt = [int(v[k]) for v, k in zip(opening, (left, right))]
            if not all(attempt) or attempt[0] == attempt[1]:
                continue
            for delivery in combinations(product((0, 1), repeat=2), 3):
                states = [(BITS[attempt[0]] if flags[0] else 0) | (BITS[attempt[1]] if flags[1] else 0)
                          for flags in delivery]
                query = [int(chair[state]) for state in states]
                answers = [int(reply[right, attempt[1], heard]) for heard in query]
                if len(set(query)) < 2:
                    continue
                end = [state | BITS[answer] for state, answer in zip(states, answers)]
                points = sum(bank[k] for k in end)
                net = points - sum(D.QUERY_COST[a] + D.SEND_COST[b] for a, b in zip(query, answers))
                controls = best_fixed(bank, right, attempt[1], states)
                high = max(controls, key=lambda key: (controls[key]["net"], -int(key)))
                if net > controls[high]["net"] + TOL and points > controls[high]["points"]:
                    matches.append({"prior": label, "selector": (index - 1, kind), "world": [left, right],
                                    "opening_actions": attempt, "opening_delivery": delivery, "public_masks": states,
                                    "learned": {"query": query, "reply": answers, "receipt": end, "points": points, "net": net},
                                    "best_fixed_target": high, "fixed": controls})
    return {"simple": simple, "matched": matches[:1], "qualifying_triplets": len(matches),
            "sha256": {f.name: sha256(f.read_bytes()).hexdigest() for f in (Path(__file__), pinned, Path(r.__file__))}}


if __name__ == "__main__":
    e.emit(run())
