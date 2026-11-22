"""Fit coordinated disclosure with three delegates and verified public receipts."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np
import torch

import trained_warrant as two

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "warrant-three-evidence"
TYPES = np.asarray(list(product(range(4), repeat=3)))
SLOTS = np.asarray(list(product(range(3), repeat=3)))
LINKS = np.asarray(list(product((False, True), repeat=3)))
P_LINKS = np.prod(np.where(LINKS, 1 - two.LOSS, two.LOSS), axis=1)
LOCAL_TABLES = np.asarray(list(product(range(3), repeat=4)))
ACTIONS = ((-1, -1), *tuple(product(range(3), repeat=2)))
ALL = (1 << len(TYPES)) - 1
SEED = 30917
N_TRAIN = 16
N_TEST = 12
INITIAL = np.array([[1., 0., 0., 0., 0.]] * 3)


def domains():
    rng = np.random.default_rng(SEED)
    seen = set()
    for _ in range(N_TRAIN + N_TEST):
        codes = np.asarray([rng.choice(64, size=4, replace=False) for _ in range(3)])
        cards = np.stack((codes // 16, codes // 4 % 4, codes % 4), axis=-1)
        signature = {tuple(tuple(sorted(map(tuple, side[:, order]))) for side in cards)
                     for order in two.ORDERINGS}
        assert not signature & seen
        seen.update(signature)
        yield cards


def prior(correlated):
    p = np.full(64, 1. / 64)
    if correlated:
        coupled = (TYPES[:, 0] == TYPES[:, 1]) & (TYPES[:, 0] == TYPES[:, 2])
        p = .55 * p + .45 * coupled / 4.
    return p


class Workshop:

    def __init__(self, cards):
        self.cards = cards
        self.world = cards[np.arange(3), TYPES]
        self.bit_reports = {(role, slot, grade): sum(1 << i for i, world in enumerate(self.world)
                                                    if world[role, slot] == grade)
                            for role, slot, grade in product(range(3), range(3), range(4))}
        winners = np.zeros((64, 4), dtype=bool)
        for i, w in enumerate(self.world):
            # One ordinal encoding implements lexicographic (minimum, sum).
            min_grade = w.min(0)
            values = np.where(min_grade > 0, 10 * min_grade + w.sum(0), 0)
            if values.max():
                winners[i, :3] = values == values.max()
            else:
                winners[i, 3] = True
            exact = [(min(col), sum(col)) if min(col) else (-1, -1) for col in w.T]
            check = {k for k, value in enumerate(exact) if value == max(exact)} if max(exact)[0] > 0 else {3}
            assert set(np.flatnonzero(winners[i])) == check
        self.winner_masks = tuple(sum(1 << i for i in range(64) if winners[i, k]) for k in range(4))

        shape = (64, 27, 8)
        self.state = np.empty(shape, dtype=int)
        self.recommend = np.zeros((*shape, 10))
        self.impasse = np.zeros_like(self.recommend)
        query_legal = {}
        states = {}
        for w, s, l in product(range(64), range(27), range(8)):
            observed = tuple((side, pos, int(self.world[w, side, pos]))
                             for side, pos in enumerate(SLOTS[s]) if LINKS[l, side])
            state = states.setdefault(observed, len(states))
            self.state[w, s, l] = state
            support = ALL
            for fact in observed:
                support &= self.bit_reports[fact]
            assert support & (1 << w)
            available = tuple((side, slot) not in {fact[:2] for fact in observed} for side, slot in ACTIONS)
            query_legal[state] = available
            previous = self.certificate(support)
            for q in range(10):
                if not available[q]:
                    continue
                if q:
                    side, slot = ACTIONS[q]
                    fact = side, slot, int(self.world[w, side, slot])
                    after = self.certificate(support & self.bit_reports[fact])
                    ok = two.REPLY_DELIVERY
                else:
                    after, ok = previous, 0.
                self.recommend[w, s, l, q] = (1 - ok) * (previous == 1) + ok * (after == 1)
                self.impasse[w, s, l, q] = (1 - ok) * (previous == 2) + ok * (after == 2)
        self.legal = np.asarray([query_legal[i] for i in range(len(states))])
        self.pay = self.recommend + self.impasse - two.REPLY_COST * (np.arange(10) != 0)
        self.pay *= self.legal[self.state]
        self.num_states = len(states)

    def certificate(self, worlds):
        allowed = tuple(k for k, labels in enumerate(self.winner_masks) if worlds & ~labels == 0)
        return 2 if allowed == (3,) else int(bool(allowed))

    def weights(self, actions, p):
        return np.prod(actions[np.arange(3), TYPES[:, None, :], SLOTS[None, :, :]], axis=-1) * p[:, None]

    def requests(self, mass):
        result = np.zeros((self.num_states, 10))
        np.add.at(result, self.state.ravel(), (mass[:, :, None, None] * P_LINKS[None, None, :, None] * self.pay).reshape(-1, 10))
        return np.where(self.legal, result, -np.inf).argmax(1)

    def metrics(self, mass, request):
        w, s, l = np.ix_(np.arange(64), np.arange(27), np.arange(8))
        chosen = request[self.state]
        p = mass[:, :, None] * P_LINKS
        recommendation = float((p * self.recommend[w, s, l, chosen]).sum())
        impasse = float((p * self.impasse[w, s, l, chosen]).sum())
        requests = float((p * (chosen != 0)).sum())
        assert abs(p.sum() - 1.) < 1e-12
        return {"net": recommendation + impasse - two.REPLY_COST * requests, "recommend": recommendation,
                "impasse": impasse, "unresolved": 1 - recommendation - impasse, "requests": requests}

    def features(self, p):
        ref = self.weights(np.full((3, 4, 3), 1 / 3.), p)
        q = self.requests(ref)
        w, s, l = np.ix_(np.arange(64), np.arange(27), np.arange(8))
        outcomes = (self.pay[w, s, l, q[self.state]] * P_LINKS).sum(-1)
        features = []
        for role in range(3):
            expected = np.zeros((4, 3))
            for typ, slot in product(range(4), range(3)):
                rows = TYPES[:, role] == typ
                cols = SLOTS[:, role] == slot
                expected[typ, slot] = (p[rows] @ outcomes[rows][:, cols]).sum() / (9 * p[rows].sum())
            grades = self.cards[role]
            rarity = 1. - (grades[:, None, :] == grades[None, :, :]).mean(1)
            features.append(np.stack((expected, grades / 3., grades == 0,
                                      grades == grades.max(1, keepdims=True), rarity), axis=-1))
        return np.asarray(features)

    def score_tables(self, tables, p):
        # Evaluate many deterministic opening tables together. Only one
        # joint opening action is executed for each possible complete world.
        acts = tables[:, np.arange(3), TYPES]
        chosen = acts @ np.array([9, 3, 1])
        w = np.arange(64)[None, :]
        states = self.state[w, chosen]
        values = self.pay[w, chosen] * p[None, :, None, None] * P_LINKS[None, None, :, None]
        offset = self.num_states * 10 * np.arange(len(tables))[:, None, None, None]
        buckets = offset + 10 * states[..., None] + np.arange(10)
        rows = np.bincount(buckets.ravel(), weights=values.ravel(), minlength=len(tables) * self.num_states * 10)
        optimal = np.where(self.legal, rows.reshape(len(tables), self.num_states, 10), -np.inf).max(-1)
        return optimal.sum(-1)

    def evaluate(self, table, p):
        mass = self.weights(np.eye(3)[table], p)
        result = self.metrics(mass, self.requests(mass))
        result["opening_only_net"] = self.metrics(mass, np.zeros(self.num_states, dtype=int))["net"]
        result["opening_table"] = table.tolist()
        return result

    def upper(self, p):
        best = np.where(self.legal[self.state], self.pay, -np.inf).max(-1)
        return float(p @ (best * P_LINKS).sum(-1).max(-1))


def train(bank):
    torch.set_num_threads(1)
    w = torch.nn.Parameter(torch.as_tensor(INITIAL.copy()))
    opt = torch.optim.Adam([w], lr=.04)
    p = prior(False)
    fields = torch.as_tensor(np.stack([workshop.features(p) for workshop in bank]))
    worlds = torch.as_tensor(TYPES)
    slots = torch.as_tensor(SLOTS)
    fee_rows = [torch.as_tensor(task.pay * p[:, None, None, None] * P_LINKS[None, None, :, None]) for task in bank]
    indexes = [torch.as_tensor(task.state.ravel()) for task in bank]
    legal = [torch.as_tensor(task.legal) for task in bank]
    history = []
    for _ in range(two.UPDATES):
        action_prob = ((fields * w[:, None, None, :]).sum(-1) * 6).softmax(-1)
        joint = action_prob[:, np.arange(3), worlds[:, None, :], slots[None, :, :]].prod(-1)
        scores = []
        for i, (matrix, idx, mask) in enumerate(zip(fee_rows, indexes, legal, strict=True)):
            returns = (matrix * joint[i, :, :, None, None]).reshape(-1, 10)
            gathered = torch.zeros((len(mask), 10), dtype=torch.float64).index_add(0, idx, returns)
            scores.append(gathered.masked_fill(~mask, -torch.inf).max(-1).values.sum())
        reward = torch.stack(scores).mean()
        opt.zero_grad()
        (-reward).backward()
        assert torch.isfinite(w.grad).all()
        opt.step()
        history.append(float(reward.detach()))
    return w.detach().numpy(), history


def coordinate(task, starts, p):
    winners = []
    for seed in starts:
        incumbent = seed.copy()
        current = float(task.score_tables(incumbent[None], p)[0])
        for _ in range(6):
            changed = False
            for role in range(3):
                candidates = np.broadcast_to(incumbent, (len(LOCAL_TABLES), 3, 4)).copy()
                candidates[:, role] = LOCAL_TABLES
                scores = task.score_tables(candidates, p)
                best = int(scores.argmax())
                if scores[best] > current + 1e-12:
                    incumbent, current = candidates[best], float(scores[best])
                    changed = True
            if not changed:
                break
        winners.append((current, incumbent))
    return max(winners, key=lambda x: x[0])[1]


def evaluate(task, weights, p):
    feature = task.features(p)
    tables = {name: (feature * value[:, None, None]).sum(-1).argmax(-1)
              for name, value in (("initial", INITIAL), ("fitted", weights))}
    constant = np.broadcast_to(SLOTS[..., None], (27, 3, 4))
    tables["constant"] = constant[int(task.score_tables(constant, p).argmax())]
    tables["coordinate"] = coordinate(task, (tables["initial"], tables["constant"]), p)
    results = {name: task.evaluate(table, p) for name, table in tables.items()}
    mass = task.weights(np.full((3, 4, 3), 1 / 3.), p)
    results["uniform"] = task.metrics(mass, task.requests(mass))
    upper = task.upper(p)
    assert all(row["net"] <= upper + 1e-12 for row in results.values())
    assert results["coordinate"]["net"] >= max(results[n]["net"] for n in ("initial", "constant")) - 1e-12
    return {"upper": upper, "arms": results}


def run():
    cards = list(domains())
    models = [Workshop(bank) for bank in cards[:N_TRAIN]]
    weights, state = train(models)
    result = []
    for i, profile in enumerate(cards[N_TRAIN:]):
        task = Workshop(profile)
        result.append({"i": i, "cards": profile.tolist(), "priors": {label: evaluate(task, weights, prior(corr))
                       for label, corr in (("uniform", False), ("correlated", True))}})
    return {"seed": SEED, "training_domains": N_TRAIN, "held_domains": N_TEST, "updates": len(state),
            "fitted_weights": weights.tolist(), "history": state, "results": result,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in
                       (Path(__file__), Path(two.__file__), EVIDENCE / "protocol.md")}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
