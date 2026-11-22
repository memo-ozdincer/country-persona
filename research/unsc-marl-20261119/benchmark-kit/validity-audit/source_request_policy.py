"""Train two decentralized agents to request and deliver typed source evidence."""
import argparse
import json
from itertools import product
from pathlib import Path

import numpy as np

from source_request_cases import cases, hashes
from source_record_run import digest

STATES = np.arange(8)
ACTIONS = np.arange(4)
BITS = np.array([0, 1, 2, 4])
SEND = (ACTIONS == 0) | ((STATES[:, None] & BITS) != 0)
ASK = (ACTIONS == 0) | ~SEND
JOINT = ASK[:, :, None] & SEND[:, None, :]
SIGNAL_COST, DELIVERY_COST = .05, .2
SEED, UPDATES = 784152, 280
TRAIN_IDS = ("western_sahara", "dprk")
HELD = "mali"
TRAIN_LOSS = .10

# Predeclared simulated inventory priors. These are private copies of source
# fields, rather than claims about what the historical delegations knew.
def product_prior(left, right):
    have = (STATES[:, None] & BITS[1:]) != 0
    marginals = [np.where(have, p, 1 - np.asarray(p)).prod(axis=1) for p in (left, right)]
    return np.outer(*marginals)


TRAIN_PRIORS = {
    "western_sahara": product_prior((.65, .45, .5), (.6, .55, .42)),
    "dprk": product_prior((.52, .68, .47), (.56, .50, .62)),
}
TEST_PRIORS = {
    "uniform": np.full((8, 8), 1 / 64),
    "asymmetric": product_prior((.7, .32, .66), (.45, .67, .30)),
    "correlated_duplicates": .55 * np.eye(8) / 8 + .45 * np.full((8, 8), 1 / 64),
}


def points(family):
    values = ((STATES[:, None] & BITS[1:]) != 0) @ family["weights"]
    need, extra = family["joint"]
    return values + ((STATES & need) == need) * extra


def receipt_matrix(payoffs, loss):
    earned = np.zeros((4, 4))
    for left, right in product((0, 1), repeat=2):
        p = (1 - loss if left else loss) * (1 - loss if right else loss)
        earned += p * payoffs[np.bitwise_or.outer(BITS * left, BITS * right)]
    return earned - DELIVERY_COST * np.add.outer(ACTIONS != 0, ACTIONS != 0).astype(int) - (
        DELIVERY_COST * np.logical_and.outer(ACTIONS != 0, ACTIONS != 0)
    )


def train(fixtures):
    import torch

    torch.set_num_threads(1)
    generator = torch.Generator().manual_seed(SEED)
    setup = [
        (torch.as_tensor(TRAIN_PRIORS[key]), torch.as_tensor(receipt_matrix(points(fixtures[key]), TRAIN_LOSS)))
        for key in TRAIN_IDS
    ]
    available = torch.as_tensor(JOINT)
    legal_reply = torch.as_tensor(SEND[:, None, :])
    left = torch.nn.Parameter(torch.randn((8, 4, 4), generator=generator, dtype=torch.float64) * .04)
    right = torch.nn.Parameter(torch.randn((8, 4, 4), generator=generator, dtype=torch.float64) * .04)
    optimizer = torch.optim.Adam([left, right], lr=.13)
    fees = torch.as_tensor(SIGNAL_COST * (ACTIONS > 0), dtype=torch.float64)
    trace = []
    for _ in range(UPDATES):
        a = left.flatten(1).masked_fill(~available.flatten(1), -torch.inf).softmax(dim=1).reshape(8, 4, 4)
        b = right.masked_fill(~legal_reply, -torch.inf).softmax(dim=2)
        delivered = (1 - TRAIN_LOSS) * b + TRAIN_LOSS * b[:, :1, :]
        expected = torch.stack([torch.einsum("lqa,rqb,ab,lr->", a, delivered, reward, prior)
                                - torch.einsum("lqa,q,l->", a, fees, prior.sum(dim=1))
                                for prior, reward in setup]).mean()
        optimizer.zero_grad()
        (-expected).backward()
        norms = [float(p.grad.norm()) for p in (left, right)]
        assert all(np.isfinite(norms))
        optimizer.step()
        trace.append({"expected_net": float(expected.detach()), "gradient_norms": norms})
    greedy = left.detach().flatten(1).masked_fill(~available.flatten(1), -torch.inf).argmax(axis=1).numpy()
    return greedy // 4, greedy % 4, right.detach().masked_fill(~legal_reply, -torch.inf).argmax(axis=2).numpy(), trace


def best_silent(prior, matrix):
    # Enumerate every sender submission map. For each, the responder's best
    # independent map can be optimized separately for each private view.
    tables = np.asarray(list(product(*(np.flatnonzero(row) for row in SEND))))
    values = np.einsum("plb,lr->prb", matrix[tables], prior)
    values = np.where(SEND[None, :, :], values, -np.inf)
    i = values.max(axis=-1).sum(axis=-1).argmax()
    return np.zeros(8, dtype=int), tables[i], np.repeat(values[i].argmax(axis=-1)[:, None], 4, axis=1)


def exact_optional(prior, matrix, loss):
    """Enumerate all requester policies and optimize each available reply."""
    local = [np.flatnonzero(row.ravel()) for row in JOINT]
    shape = tuple(map(len, local))
    count = int(np.prod(shape))
    best, answer = -np.inf, None
    for offset in range(0, count, 4096):
        coords = np.unravel_index(np.arange(offset, min(offset + 4096, count)), shape)
        joined = np.stack([entries[i] for entries, i in zip(local, coords, strict=True)], axis=-1)
        ask, send = joined // 4, joined % 4
        partial = matrix[send]
        total = -SIGNAL_COST * ((ask != 0) @ prior.sum(axis=1))
        reply = []
        for q in ACTIONS:
            arrival = (ask == q).astype(float) * (1 - loss) + (loss if q == 0 else 0.)
            value = np.einsum("plb,pl,lr->prb", partial, arrival, prior)
            value = np.where(SEND[None, :, :], value, -np.inf)
            reply.append(value.argmax(axis=-1))
            total += value.max(axis=-1).sum(axis=-1)
        i = total.argmax()
        if total[i] > best + 1e-10:
            best = float(total[i])
            answer = ask[i], send[i], np.stack(reply, axis=-1)[i]
    return answer, count


def scripted():
    request = ASK[:, 1:].argmax(axis=1) + 1
    request[STATES == 7] = 0
    priority = SEND[:, 1:].argmax(axis=1) + 1
    priority[STATES == 0] = 0
    reply = np.where(SEND, ACTIONS, priority[:, None])
    reply[:, 0] = priority
    return request, priority, reply


def evaluate(policy, prior, payoff, loss, force_missing=False):
    ask, send, reply = policy
    assert np.all(JOINT[STATES, ask, send]) and np.all(SEND[STATES[:, None], reply])
    receipt_mass = np.zeros(8)
    sends = queries = 0.
    for left, right in product(STATES, repeat=2):
        probability = prior[left, right]
        a, q = send[left], ask[left]
        queries += probability * bool(q)
        for signal, x, y in product((0, 1), repeat=3):
            mass = probability * np.prod([1 - loss if keep else loss for keep in (signal, x, y)])
            b = reply[right, q if signal and not force_missing else 0]
            sends += mass * (bool(a) + bool(b))
            receipt_mass[BITS[a] * x | BITS[b] * y] += mass
    assert np.isclose(receipt_mass.sum(), 1)
    points = receipt_mass @ payoff
    return {"net": float(points - SIGNAL_COST * queries - DELIVERY_COST * sends),
            "proof_points": float(points), "requests": float(queries), "deliveries": float(sends),
            "receipt_distribution": receipt_mass.tolist()}


def witness(family, learned, silent):
    out = []
    for left, right in product(STATES, repeat=2):
        def show(policy):
            ask, to_chair, reply = policy
            return int(ask[left]), int(to_chair[left]), int(reply[right, ask[left]])
        q, a, b = show(learned)
        _, c, d = show(silent)
        inter, quiet = BITS[a] | BITS[b], BITS[c] | BITS[d]
        if q and points(family)[inter] > points(family)[quiet] and b != learned[2][right, 0]:
            out.append({"local_availability": [int(left), int(right)], "asked_field": q,
                        "reply_changed_from": int(learned[2][right, 0]), "reply_changed_to": b,
                        "earned": int(points(family)[inter]), "silent_points": int(points(family)[quiet]),
                        "learned_receipts": [j for j, bit in enumerate(BITS[1:], 1) if inter & bit],
                        "silent_receipts": [j for j, bit in enumerate(BITS[1:], 1) if quiet & bit],
                        "compiled_evidence": [family["fields"][j] for j, bit in enumerate(BITS[1:]) if inter & bit]})
    return out


def report(include_bound=False):
    fixtures = cases()
    assert all(points(v)[-1] == 28 for v in fixtures.values())
    *learned, trace = train(fixtures)
    history = {}
    for key, prior in TRAIN_PRIORS.items():
        payoff = points(fixtures[key])
        history[key] = evaluate(learned, prior, payoff, TRAIN_LOSS)
    held = fixtures[HELD]
    values = points(held)
    test = []
    for name, prior in TEST_PRIORS.items():
        for loss in (0., .1, .25):
            matrix = receipt_matrix(values, loss)
            silent = best_silent(prior, matrix)
            arms = {
                "learned_request": evaluate(learned, prior, values, loss),
                "learned_no_delivery_of_request": evaluate(learned, prior, values, loss, force_missing=True),
                "scripted_request": evaluate(scripted(), prior, values, loss),
                "optimal_independent": evaluate(silent, prior, values, loss),
            }
            # Independently verify that the fast score matrix and the
            # transport replay agree for every reported operating condition.
            for policy, key in ((silent, "optimal_independent"), (learned, "learned_request")):
                q, a, b = policy
                expected = (1 - loss) * matrix[a[:, None], b[:, q].T] + loss * matrix[a[:, None], b[None, :, 0]]
                assert np.isclose(arms[key]["net"], np.sum(prior * (expected - SIGNAL_COST * (q[:, None] != 0))))
            row = {"prior": name, "loss": loss, "arms": arms}
            if include_bound and name == "uniform" and loss == .1:
                top, count = exact_optional(prior, matrix, loss)
                top_score = evaluate(top, prior, values, loss)
                assert all(a["net"] <= top_score["net"] + 1e-8 for a in arms.values())
                row["exact_optional"] = {**top_score, "enumerated_requester_maps": count}
            test.append(row)
    pair = best_silent(TEST_PRIORS["uniform"], receipt_matrix(values, 0.))
    return {
        "scope": "Two differentiable table policies share a team reward. Observations carry verified field IDs. "
                 "Mali uses a different reward profile and previously unseen simulated inventory distributions. "
                 "The same three-field interface and authored source wrappers are shared across dockets.",
        "source_hashes": {**hashes(), Path(__file__).name: digest(Path(__file__))},
        "fields": fixtures,
        "training": {"seed": SEED, "updates": UPDATES, "trace": trace, "greedy": history,
                     "inventory_priors": {k: v.tolist() for k, v in TRAIN_PRIORS.items()},
                     "request": learned[0].tolist(), "left_delivery": learned[1].tolist(), "reply": learned[2].tolist()},
        "held_out": {"family": HELD, "conditions": test, "worked_witnesses": witness(held, learned, pair)},
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--exact", action="store_true")
    print(json.dumps(report(cli.parse_args().exact), ensure_ascii=False, indent=2))
