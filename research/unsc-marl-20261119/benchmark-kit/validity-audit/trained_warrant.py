"""Fit both delegates' openings for a jointly warranted package decision."""
import argparse
from hashlib import sha256
from itertools import permutations, product
import json
from pathlib import Path

import numpy as np
import torch

from check import winners

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "trained-warrant-evidence"
LOSS = .1
REPLY_COST = .05 + (1 - LOSS) * .1
REPLY_DELIVERY = (1 - LOSS) ** 2
UPDATES = 96
WORLDS = tuple(product(range(4), repeat=2))
PACKAGES = ("A", "B", "C")
MENU = (*PACKAGES, "impasse", "unresolved")
TABLES = np.asarray(list(product(range(3), repeat=4)))
ORDERINGS = tuple(permutations(range(3)))
PANELS = {
    "mali_review": (
        ((1, 2, 0), (2, 1, 0), (0, 2, 3), (2, 3, 1)),
        ((3, 2, 0), (0, 1, 3), (2, 1, 1), (1, 3, 0)),
    ),
    "briefing_procedure": (
        ((2, 2, 2), (0, 2, 1), (2, 0, 1), (1, 2, 0)),
        ((2, 2, 1), (1, 2, 2), (2, 1, 2), (0, 0, 1)),
    ),
    "reporting_scope": (
        ((0, 3, 2), (0, 0, 3), (3, 1, 0), (1, 2, 0)),
        ((2, 2, 0), (1, 3, 2), (0, 2, 2), (2, 0, 0)),
    ),
}


def winner(a, b):
    options = {k: (min(x, y), x + y) for k, (x, y) in enumerate(zip(a, b, strict=True)) if x and y}
    if not options:
        return frozenset({3})
    maximum = max(options.values())
    return frozenset(k for k, v in options.items() if v == maximum)


def prior(correlated):
    uniform = np.full((4, 4), 1. / 16)
    return .55 * uniform + .45 * np.eye(4) / 4 if correlated else uniform


def training_domains():
    rng = np.random.default_rng(8391)
    seen = {tuple(tuple(sorted(roles)) for roles in values) for values in PANELS.values()}
    assert len(seen) == len(PANELS)
    for _ in range(16):
        directions = []
        for _ in range(2):
            ids = rng.choice(64, size=4, replace=False)
            directions.append(tuple((int(i // 16), int(i // 4 % 4), int(i % 4)) for i in ids))
        roles = tuple(directions)
        signature = tuple(tuple(sorted(role)) for role in roles)
        assert signature not in seen
        seen.add(signature)
        yield roles


def environment(roles, world_prior):
    world = [tuple(roles[side][index[side]] for side in range(2)) for index in WORLDS]
    outcome = []
    sum_errors = 0
    for a, b in world:
        result = winner(a, b)
        expected = winners(MENU, (a, b), "full")
        assert {MENU[k] for k in result} == expected
        sum_errors += winners(MENU, (a, b), "sum") != expected
        outcome.append(result)

    def proof(facts):
        compatible = [label for values, label in zip(world, outcome, strict=True)
                      if all(values[side][pos] == grade for side, pos, grade in facts)]
        assert compatible
        shared = set.intersection(*(set(labels) for labels in compatible))
        return 2 if shared == {3} else int(bool(shared))

    receipts = {}
    pay, rec, imp = {}, {}, {}
    for k, (a, b, send_a, send_b) in enumerate(product(range(4), range(4), range(3), range(3))):
        grades = world[4*a+b]
        for first, second in product((False, True), repeat=2):
            facts = tuple((i, pos, grades[i][pos]) for i, (seen, pos) in
                          enumerate(zip((first, second), (send_a, send_b), strict=True)) if seen)
            m = receipts.setdefault(facts, len(receipts))
            p = (1 - LOSS) ** (first + second) * LOSS ** (2 - first - second)
            old = proof(facts)
            for q in range(7):
                new = old
                if q:
                    side, slot = divmod(q - 1, 3)
                    if any(f[:2] == (side, slot) for f in facts):
                        continue
                    new = proof((*facts, (side, slot, grades[side][slot])))
                ok = REPLY_DELIVERY if q else 0.
                rec[(k, m, q)] = p * ((1 - ok) * (old == 1) + ok * (new == 1))
                imp[(k, m, q)] = p * ((1 - ok) * (old == 2) + ok * (new == 2))
                pay[(k, m, q)] = rec[k, m, q] + imp[k, m, q] - p * REPLY_COST * (q != 0)
    matrices = []
    for source in (pay, rec, imp):
        matrix = np.zeros((144, len(receipts), 7))
        for index, value in source.items():
            matrix[index] = value
        matrices.append(matrix)
    legal = np.ones((len(receipts), 7), dtype=bool)
    for facts, m in receipts.items():
        for i, pos, _ in facts:
            legal[m, i*3+pos+1] = False
    return (*matrices, legal, world_prior, sum_errors)


def combinations(left, right, world_prior):
    return (left[..., :, None, :, None] * right[..., None, :, None, :] * world_prior[..., :, :, None, None]).reshape(-1, 144)


def value(matrix, legal, weight):
    mixed = (weight @ matrix.reshape(144, -1)).reshape(-1, len(legal), 7)
    return np.where(legal, mixed, -np.inf)


def features(roles, env):
    pay, _, _, legal, world_prior, _ = env
    uniform = np.full((4, 3), 1. / 3)
    default = value(pay, legal, combinations(uniform, uniform, world_prior))[0].argmax(1)
    stage = pay[:, np.arange(len(legal)), default].sum(1).reshape(4, 4, 3, 3)
    conditional_a = np.divide(world_prior, world_prior.sum(1, keepdims=True))
    conditional_b = np.divide(world_prior, world_prior.sum(0, keepdims=True))
    first = np.einsum("abij,ab->ai", stage, conditional_a) / 3
    second = np.einsum("abij,ab->bj", stage, conditional_b) / 3
    arrays = []
    for side, local_fit in enumerate((first, second)):
        grades = np.asarray(roles[side])
        frequencies = np.stack([(grades[:, i, None] == grades[:, i]).mean(1) for i in range(3)], axis=1)
        arrays.append(np.stack((local_fit, grades / 3., grades == 0, grades == grades.max(1, keepdims=True),
                                1. - frequencies), axis=-1))
    return arrays


def train(records):
    torch.set_num_threads(1)
    initial = np.array([[1., 0., 0., 0., 0.]] * 2)
    weights = torch.nn.Parameter(torch.as_tensor(initial, dtype=torch.float64).clone())
    optimizer = torch.optim.Adam([weights], lr=.04)
    width = max(len(env[3]) for _, env in records)
    bank = np.zeros((len(records), 144, width, 7))
    legal = np.zeros((len(records), width, 7), dtype=bool)
    legal[:, :, 0] = True
    for idx, (_, env) in enumerate(records):
        n = len(env[3])
        bank[idx, :, :n] = env[0]
        legal[idx, :n] = env[3]
    bank, allowed = torch.as_tensor(bank), torch.as_tensor(legal)
    fields = torch.as_tensor(np.asarray([f for f, _ in records]))
    probabilities = torch.as_tensor(np.asarray([env[4] for _, env in records]))
    history = []
    for _ in range(UPDATES):
        actions = ((fields * weights[None, :, None, None, :]).sum(-1) * 6).softmax(-1)
        a, b = actions.unbind(1)
        joint = (a[:, :, None, :, None] * b[:, None, :, None, :] * probabilities[..., None, None]).reshape(-1, 144)
        request = torch.einsum("nk,nkmq->nmq", joint, bank).masked_fill(~allowed, -torch.inf)
        team = request.max(-1).values.sum(-1).mean()
        optimizer.zero_grad()
        (-team).backward()
        assert torch.isfinite(weights.grad).all()
        optimizer.step()
        history.append(float(team.detach()))
    return initial, weights.detach().numpy(), history


def extract(env, weights):
    pay, rec, imp, legal, _, _ = env
    request_values = value(pay, legal, weights)[0]
    requests = request_values.argmax(1)
    columns = np.arange(len(legal))
    net = float(request_values[columns, requests].sum())
    recommend = float((weights @ rec[:, columns, requests])[0].sum())
    impasse = float((weights @ imp[:, columns, requests])[0].sum())
    charge = recommend + impasse - net
    return {"net": net, "recommend": recommend, "impasse": impasse, "unresolved": 1 - recommend - impasse,
            "requests": charge / REPLY_COST, "request_cost": charge}


def choose(env, left, right):
    return extract(env, combinations(left, right, env[4]))


def optimized(env, actions):
    # Optimize the chair separately for each possible pair of local policies.
    left, right = (np.broadcast_to(actions[:, None], (len(actions), len(actions), 4)),
                   np.broadcast_to(actions[None, :], (len(actions), len(actions), 4)))
    identity = np.eye(3)
    weights = combinations(identity[left], identity[right], env[4])
    scores = value(env[0], env[3], weights).max(-1).sum(1)
    return extract(env, weights[[int(scores.argmax())]])


def evaluate(roles, env, initial, fitted):
    fx = np.asarray(features(roles, env))
    uniform = np.full((4, 3), 1. / 3)
    result = {}
    for name, params in (("initial", initial), ("fit", fitted)):
        a, b = np.eye(3)[(fx * params[:, None, None]).sum(-1).argmax(-1)]
        result[name] = choose(env, a, b)
    result["uniform"] = choose(env, uniform, uniform)
    result["constant_optimum"] = optimized(env, np.tile(np.arange(3)[:, None], (1, 4)))
    result["exact_local"] = optimized(env, TABLES)
    assert max(x["net"] for x in result.values()) <= result["exact_local"]["net"] + 1e-10
    return result


def run():
    training = []
    for domain in training_domains():
        env = environment(domain, prior(False))
        training.append((features(domain, env), env))
    initial, fitted, trace = train(training)
    results = {}
    for name, domain in PANELS.items():
        results[name] = {}
        for correlated in (False, True):
            rows = []
            for order in ORDERINGS:
                roles = tuple(tuple(tuple(option[i] for i in order) for option in side) for side in domain)
                env = environment(roles, prior(correlated))
                rows.append({"order": order, "sum_rule_disagrees_in_worlds": env[-1],
                             "arms": evaluate(roles, env, initial, fitted)})
            results[name]["correlated" if correlated else "uniform"] = rows
    return {"training_domains": len(training), "updates": UPDATES, "initial": initial.tolist(), "fit": fitted.tolist(),
            "history": trace, "test_panels": PANELS, "results": results,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in
                       (Path(__file__), HERE / "check.py", EVIDENCE / "protocol.md")}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
