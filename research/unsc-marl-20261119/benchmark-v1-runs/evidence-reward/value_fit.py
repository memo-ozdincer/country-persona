"""Fit and replay the chair and responder counterfactual value margins."""
from collections import Counter
from hashlib import sha256
from pathlib import Path

import calibrate as c
import environment as env
import followup as f

HERE = Path(__file__).resolve().parent
TRAIN_COSTS = ((.04, .10), (.02, .07), (.08, .13))
HELD_COSTS = ((.04, .10), (.01, .055), (.07, .145), (.11, .035))
TOLERANCE = 1e-10


def components(state, role, rate, ask, send):
    feature = f.features(state, role, rate)
    finish = bool(feature[3])
    signal = rate * finish
    # A no-answer question costs the chair the question fee regardless of state.
    return (1., signal, send), (1., signal, send, ask)


def least_squares(rows):
    width = len(rows[0][0])
    matrix = [[sum(weight * xs[i] * xs[j] for xs, _, weight in rows)
               for j in range(width)] + [sum(weight * xs[i] * target for xs, target, weight in rows)]
              for i in range(width)]
    for i in range(width):
        pivot = max(range(i, width), key=lambda k: abs(matrix[k][i]))
        matrix[i], matrix[pivot] = matrix[pivot], matrix[i]
        assert abs(matrix[i][i]) > 1e-12
        divisor = matrix[i][i]
        matrix[i] = [v/divisor for v in matrix[i]]
        for k, row in enumerate(matrix):
            if k != i:
                scale = row[i]
                matrix[k] = [v - scale * a for v, a in zip(row, matrix[i], strict=True)]
    return [r[-1] for r in matrix]


def dot(xs, weights):
    return sum(a*b for a,b in zip(xs, weights, strict=True))


def fit(paths):
    replies, queries = [], []
    for state, weight in paths:
        for rate in c.TRAIN_RATES:
            for ask, send in TRAIN_COSTS:
                for role in env.ROLES:
                    r, q = components(state, role, rate, ask, send)
                    finish = f.features(state, role, rate)[3]
                    # Compare delivered and lost transition payoffs at fixed sending cost.
                    before = float(state["known"] == 2)
                    delivered = float(before or finish)
                    response_value = ((rate*delivered + (1-rate)*before) - before)*env.BONUS - send
                    replies.append((r, response_value, weight))
                    queries.append((q, response_value-ask, weight))
    heads = {"response": least_squares(replies), "chair": least_squares(queries)}
    residual = {
        name: max(abs(dot(xs, heads[name]) - target) for xs, target, _ in rows)
        for name, rows in (("response", replies), ("chair", queries))
    }
    return heads, residual, len(queries)


def choose(state, rate, ask, send, heads):
    best = None
    best_margin = TOLERANCE
    for role in env.ROLES:
        r, q = components(state, role, rate, ask, send)
        margin = dot(q, heads["chair"])
        if dot(r, heads["response"]) > TOLERANCE and margin > best_margin:
            best, best_margin = role, margin
    return best


def replay(held, rate, ask, send, heads):
    scores = {mode: Counter(ready=0., proof=0., cost=0., queries=0., sends=0.)
              for mode in ("value", "exact")}
    errors = 0.
    for row in held:
        for state, weight, _, first_cost in f.start_states(row, False):
            before = env.outcome(state, first_cost)
            policies = {"value": None, "exact": None}
            if before[0]:
                policies["value"] = choose(state, rate, ask, send, heads)
                exact = [role for role in env.ROLES if f.features(state, role, rate)[3]
                         and rate * env.BONUS - ask - send > TOLERANCE]
                assert len(exact) <= 1
                policies["exact"] = exact[0] if exact else None
                errors += weight * (policies["value"] != policies["exact"])
            for mode, role in policies.items():
                s = scores[mode]
                s["proof"] += weight * before[0]
                s["ready"] += weight * (before[1] + (rate*f.features(state, role, rate)[3] if role else 0.))
                s["cost"] += weight * (first_cost + (ask+send if role else 0.))
                s["queries"] += weight * bool(role)
                s["sends"] += weight * bool(role)
    for s in scores.values():
        s["net"] = s["proof"] + env.BONUS*s["ready"] - s["cost"]
    return {"arms": scores, "weighted_action_errors": errors,
            "regret": scores["exact"]["net"] - scores["value"]["net"]}


def run():
    train, held = c.train_and_held()
    heads, residual, count = fit(train)
    regimes = {f"{ask}/{send}": {str(rate): replay(held, rate, ask, send, heads)
                                for rate in c.TEST_RATES} for ask, send in HELD_COSTS}
    assert all(r["regret"] >= -TOLERANCE for rates in regimes.values() for r in rates.values())
    files = (Path(__file__), HERE / "value-protocol.md", HERE / "calibration.json", HERE / "followup.py")
    return {"heads": heads, "max_fit_residual": residual, "training_rows_per_head": count,
            "training_costs": TRAIN_COSTS, "evaluation": regimes,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    env.E.emit(run())
