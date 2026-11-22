"""Fit a shared, order-equivariant disclosure policy and transfer it across workshops."""
from collections import defaultdict
from functools import lru_cache
from itertools import permutations, product
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

import three_seat_followup as protocol

HERE = Path(__file__).resolve().parent
base = protocol.base
NEW_GRIDS = {
    "mali": (("A", "E", "F"), ((3, 1, 0), (3, 2, 0), (0, 2, 3), (0, 1, 0)),
             ((2, 0, 3), (1, 3, 1), (0, 0, 3)), (2, 3, 1)),
    "myanmar": (("A", "B", "D"), ((3, 2, 0), (0, 3, 2), (2, 2, 0)),
                ((2, 3, 0), (0, 1, 3), (0, 0, 2), (3, 1, 0)), (1, 3, 2)),
}
MAX_ACTIONS = 7
FEATURES = 9
FIXTURES = {"space": (base.PACKAGES, base.CARDS_A, base.CARDS_B, base.PUBLIC), **NEW_GRIDS}


class Grid:
    def __init__(self, name, order=(0, 1, 2)):
        packages, left, right, public = FIXTURES[name]
        self.name = name
        self.packages = tuple(packages[i] for i in order)
        self.cards = tuple(tuple(tuple(card[i] for i in order) for card in deck) for deck in (left, right))
        self.public = tuple(public[i] for i in order)
        self.worlds = tuple(product(*(range(len(deck)) for deck in self.cards)))

    @lru_cache(None)
    def winners(self, world):
        left, right = (self.cards[seat][index] for seat, index in enumerate(world))
        scores = [(min(g), sum(g)) if min(g) else (0, 0) for g in zip(left, right, self.public, strict=True)]
        return frozenset({"impasse"}) if max(scores) == (0, 0) else frozenset(
            self.packages[i] for i, value in enumerate(scores) if value == max(scores))

    def claim(self, world, seat, col):
        return col, self.cards[seat][world[seat]][col]

    @lru_cache(None)
    def information(self, view, extra=None):
        possible = tuple(world for world in self.worlds
                         if all(claim is None or self.claim(world, seat, claim[0]) == claim
                                for seat, claim in enumerate(view))
                         and (extra is None or self.claim(world, *extra[:2])[1] == extra[2]))
        assert possible
        return possible, frozenset.intersection(*(self.winners(world) for world in possible))

    @lru_cache(None)
    def contact(self, receipts, q):
        worlds, certified = self.information(receipts)
        if q is None:
            return (float(bool(certified)), 0., 0., 0., 0., 0., 0., 0., 0.)
        seat, col = q
        proof = [self.information(receipts, (*q, grade)) for grade in
                 sorted({self.claim(w, seat, col)[1] for w in worlds})]
        success = sum(len(survivors) for survivors, choices in proof if choices) / len(worlds)
        weighted_remaining = sum(len(survivors) ** 2 for survivors, _ in proof) / len(worlds) ** 2
        return (protocol.REPLY * success, 1., 1 - weighted_remaining, len(proof) / 4.,
                self.public[col] / 3., float(receipts[seat] is None),
                sum(len(survivors) for survivors, choices in proof if "impasse" in choices) / len(worlds),
                float(seat), (1 - weighted_remaining) * success)

    @lru_cache(None)
    def counsel(self, seat, private, col, seen, pay=False):
        grade = self.cards[seat][private][col]
        included = len([card for card in self.cards[seat] if card[col] == grade]) / len(self.cards[seat])
        own = (col, grade)
        state_candidates = [w for w in self.worlds if w[seat] == private
                            and (seen is None or self.claim(w, 1 - seat, seen[0]) == seen)]
        peer_cases = []
        for world in state_candidates:
            others = [seen] if seen is not None else [self.claim(world, 1 - seat, i) for i in range(3)]
            for other in others:
                view = (own, other) if seat == 0 else (other, own)
                possible, certified = self.information(view)
                peer_cases.append((bool(certified), len(possible) / len(self.worlds)))
        predicted_cert = sum(case[0] for case in peer_cases) / len(peer_cases)
        remainder = sum(case[1] for case in peer_cases) / len(peer_cases)
        return (grade / 3., self.public[col] / 3., 1 - included, predicted_cert, 1 - remainder,
                float(pay), predicted_cert * pay, float(seen is not None), float(grade == 0))

    def prior(self, balanced):
        impasses = sum("impasse" in self.winners(world) for world in self.worlds)
        assert 0 < impasses < len(self.worlds)
        if not balanced:
            return {world: 1 / len(self.worlds) for world in self.worlds}
        return {world: .5 / (impasses if "impasse" in self.winners(world) else len(self.worlds) - impasses)
                for world in self.worlds}


class Experiment:
    def __init__(self, grid, balanced):
        self.grid = grid
        self.prior = grid.prior(balanced)
        self.states = {}
        self.features = []
        self.roles = []
        paths = defaultdict(float)

        def slot(key, role, features, offset):
            if key not in self.states:
                self.states[key] = len(self.features)
                self.features.append(features)
                self.roles.append(role)
            return self.states[key] * MAX_ACTIONS + offset

        for world, p in self.prior.items():
            deadlock = "impasse" in grid.winners(world)
            for i, (a_col, pay) in enumerate(base.ACTIONS):
                first = grid.claim(world, 0, a_col)
                a = slot(("A", world[0]), 0, [grid.counsel(0, world[0], col, None, send)
                         for col, send in base.ACTIONS], i)
                for seen, seen_p in base.observations(first, pay):
                    for j in range(3):
                        second = grid.claim(world, 1, j)
                        b = slot(("B", world[1], seen), 1, [grid.counsel(1, world[1], col, seen)
                                 for col in range(3)], j)
                        for receive_a, receive_b in product((False, True), repeat=2):
                            receipts = (first if receive_a else None, second if receive_b else None)
                            p_received = (base.DELIVER if receive_a else 1 - base.DELIVER) * (
                                base.DELIVER if receive_b else 1 - base.DELIVER)
                            _, certified = grid.information(receipts)
                            mass = p * seen_p * p_received
                            charge = base.FEE * pay
                            if certified:
                                paths[(a, b, -1), float(charge), 1., deadlock, True, False, pay] += mass
                                continue
                            menu = protocol.actions(receipts)
                            for k, q in enumerate(menu):
                                c = slot(("C", receipts), 2, [grid.contact(receipts, ask) for ask in menu], k)
                                gain = (protocol.REPLY * bool(grid.information(
                                    receipts, (*q, grid.claim(world, *q)[1]))[1])) if q is not None else 0.
                                cost = charge + protocol.FEE * (q is not None)
                                paths[(a, b, c), float(cost), gain, deadlock, False, q is not None, pay] += mass
        self.path_ids = np.array([path for path, *_ in paths])
        self.outcomes = np.array([row[1:] for row in paths], dtype=float)
        self.mass = np.array(list(paths.values()))
        array = np.zeros((len(self.features), MAX_ACTIONS, FEATURES))
        mask = np.zeros((len(self.features), MAX_ACTIONS), dtype=bool)
        for i, options in enumerate(self.features):
            array[i, :len(options)] = options
            mask[i, :len(options)] = True
        self.arrays = torch.as_tensor(array)
        self.mask = torch.as_tensor(mask)
        self.role_ids = torch.as_tensor(self.roles)

    def probabilities(self, weights):
        logits = (self.arrays * weights[self.role_ids].unsqueeze(1)).sum(-1)
        return logits.masked_fill(~self.mask, -torch.inf).softmax(-1)

    def metrics(self, policy):
        mass = self.path_mass(policy)
        cost, success, deadlock, before, questions, peer = self.outcomes.T
        assert abs(mass.sum() - 1.) < 1e-9
        d = mass @ deadlock
        return {"net": float(mass @ (success - cost)), "confirmed_agreement": float(mass @ (success * (1 - deadlock)) / (1 - d)),
                "verified_impasse": float(mass @ (success * deadlock) / d),
                "before_followup": float(mass @ before), "after_followup": float(mass @ success),
                "question_rate": float(mass @ questions), "peer_rate": float(mass @ peer)}

    def path_mass(self, policy):
        flat = np.append(policy.ravel(), 1.)
        return flat[self.path_ids].prod(axis=1) * self.mass

    def switched(self, learned, choice):
        updated = learned.copy()
        path_a, path_b, chair = self.path_ids.T
        weights = learned.ravel()[path_a] * learned.ravel()[path_b] * self.mass
        rewards = self.outcomes[:, 1] - protocol.FEE * self.outcomes[:, 4]
        totals = np.bincount(chair[chair >= 0], weights=weights[chair >= 0] * rewards[chair >= 0],
                             minlength=learned.size).reshape(learned.shape)
        for i, role in enumerate(self.roles):
            if role != 2:
                continue
            if choice == "stop":
                option = 0
            elif choice == "public":
                option = max(range(len(self.features[i])), key=lambda j:
                             self.features[i][j][0] - protocol.FEE * self.features[i][j][1])
            else:
                option = int(np.argmax(totals[i, :len(self.features[i])]))
            updated[i] = base.onehot(option, MAX_ACTIONS)
        return updated

    def public_emitters(self, shape, send):
        scripted = np.zeros((len(self.features), MAX_ACTIONS))
        for state, role in enumerate(self.roles):
            if role == 2:
                scripted[state, 0] = 1.
                continue
            choices = [(index, features) for index, features in enumerate(self.features[state])
                       if role == 1 or bool(features[5]) == send]
            if shape == "information":
                priority = lambda pair: (pair[1][2], pair[1][4], pair[1][3])
            else:
                priority = lambda pair: (pair[1][3], pair[1][4], pair[1][2])
            best = max(map(priority, choices))
            winners = [index for index, values in choices if priority((index, values)) == best]
            scripted[state, winners] = 1. / len(winners)
        return scripted


def train(data):
    weights = torch.zeros((3, FEATURES), dtype=torch.float64, requires_grad=True)
    adam = torch.optim.Adam([weights], lr=.08)
    paths = torch.as_tensor(data.path_ids)
    outcomes = torch.as_tensor(data.mass * (data.outcomes[:, 1] - data.outcomes[:, 0]))
    history = []
    for step in range(base.STEPS + 1):
        values = torch.cat((data.probabilities(weights).flatten(), torch.ones(1, dtype=weights.dtype)))
        reward = (values[paths].prod(dim=1) * outcomes).sum()
        if step in (0, 30, 90, base.STEPS):
            history.append({"update": step, "return": float(reward.detach())})
        if step < base.STEPS:
            adam.zero_grad()
            (-reward).backward()
            adam.step()
    return weights.detach(), history


def check(data, weights):
    learned = data.probabilities(weights).double().numpy()
    hidden = learned.copy()
    scripted_openings = data.public_emitters("information", False)
    with_scripted_openings = learned.copy()
    for state, index in data.states.items():
        if state[0] == "B" and state[2] is not None:
            hidden[index] = learned[data.states[("B", state[1], None)]]
        if state[0] != "C":
            with_scripted_openings[index] = scripted_openings[index]
    return {"joint": data.metrics(learned),
            "joint_hidden_peer_message": data.metrics(hidden),
            "public_information_emitters_learned_chair": data.metrics(with_scripted_openings),
            **{option: data.metrics(data.switched(learned, choice)) for option, choice in (
                ("same_emitters_no_query", "stop"), ("same_emitters_public_completion_model", "public"),
                ("same_emitters_true_prior_chair", "true"))},
            **{f"public_{criterion}_{'peer' if send else 'independent'}": data.metrics(
                data.switched(data.public_emitters(criterion, send), "public"))
               for criterion, send in product(("information", "forecast"), (False, True))}}


def run():
    torch.set_num_threads(1)
    training = Experiment(Grid("space"), True)
    weights, history = train(training)
    measured = {"space_balanced_fit": check(training, weights)}
    assert abs(history[-1]["return"] - measured["space_balanced_fit"]["joint"]["net"]) < 1e-8
    for name in NEW_GRIDS:
        reference = check(Experiment(Grid(name), False), weights)
        checks = []
        for perm in permutations(range(3)):
            permuted = check(Experiment(Grid(name, perm), False), weights)
            deviation = abs(permuted["joint"]["net"] - reference["joint"]["net"])
            assert deviation < 1e-9
            checks.append({"order": perm, "joint_net_difference": deviation})
        measured[name] = reference | {"package_order_checks": checks}
    inputs = {}
    for name, (keys, a, b, public) in FIXTURES.items():
        source = HERE.parent / name / "case.json"
        case = json.loads(source.read_text())
        grid = Grid(name)
        options = {row["id"]: row for row in case["options"] if row["id"] in keys}
        assert set(options) == set(keys)
        inputs[name] = {"packages_in_order": keys, "options": options, "domains": [a, b], "public": public,
                        "input_sha256": sha256(source.read_bytes()).hexdigest(),
                        "impasse_worlds": [w for w in grid.worlds if "impasse" in grid.winners(w)]}
    return {"scope": "One exact analytic policy-gradient fit on space's fictional scorecards. Shared action "
                     "features use only local cards, visible receipts and declared public completions. "
                     "Mali and Myanmar use new fictional grids compiled from their existing workshop menus.",
            "training": history, "train_paths": len(training.path_ids), "shared_weights": weights.tolist(),
            "workshops": inputs, "results": measured}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
