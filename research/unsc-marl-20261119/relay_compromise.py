"""Exact team-return training for a relay choosing among feasible compromises."""
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import random

import torch
from torch import nn

import relay_marl as relay
from relay_text_train import Adapter, enumerate_joint_action_paths

SEED = 191227
STEPS = 100
SOURCE = relay.HERE / "crossbench"
FILES = (SOURCE / "venezuela/case.json", SOURCE / "space/case.json")


@dataclass(frozen=True)
class Workshop(relay.Task):
    cards: tuple

    def card(self, role, identity):
        domain = (self.first, self.second)[role]
        return self.cards[role][domain.index(identity)] if identity else (0,) * self.hold

    def quality(self, left, right, action):
        if action == self.hold:
            return (0, 0)
        a, b = self.card(0, left)[action], self.card(1, right)[action]
        return (min(a, b), a + b) if a and b else (0, 0)

    def valid(self, left, right):
        return {i for i in range(self.hold) if self.quality(left, right, i)[0]} or {self.hold}

    def optimal(self, left, right):
        scores = {i: self.quality(left, right, i) for i in self.valid(left, right)}
        return {i for i, score in scores.items() if score == max(scores.values())}

    def completions(self, left, right):
        return product((left,) if left else self.first, (right,) if right else self.second)

    def optimal_warrant(self, left, right):
        return set.intersection(*(self.optimal(a, b) for a, b in self.completions(left, right)))


def workshop(name, actions, cards):
    assert all(len(set(group)) == len(group) for group in cards)
    first, second = (tuple(1 << (i + 4 * role) for i in range(len(group)))
                     for role, group in enumerate(cards))
    return Workshop(name, (*actions, "impasse"), first, second, ((), ()), cards)


def fixtures():
    panels = {
        "venezuela": (
            ({"B": 3, "D": 2, "F": 1}, {"B": 1, "D": 2, "F": 3}, {"C": 3, "E": 2}),
            ({"B": 1, "D": 3}, {"B": 3, "D": 1}, {"C": 2, "E": 3}),
        ),
        "space": (
            ({"A": 2, "D": 3, "F": 1}, {"A": 1, "D": 2, "F": 3}, {"B": 2, "G": 3}),
            ({"A": 1, "D": 3, "F": 2}, {"A": 3, "D": 1, "F": 2}, {"B": 3, "G": 2}),
        ),
    }
    result = {}
    for (family, panel), path in zip(panels.items(), FILES, strict=True):
        actions = tuple(x["id"] for x in json.loads(path.read_text())["options"])
        cards = tuple(tuple(tuple(card.get(a, 0) for a in actions) for card in role) for role in panel)
        task = workshop(family, actions, cards)
        assert any(len(task.valid(*w)) > 1 for w in task.worlds)
        assert any(task.valid(*w) == {task.hold} for w in task.worlds)
        assert any(task.valid(*a) == task.valid(*b) and task.optimal(*a).isdisjoint(task.optimal(*b))
                   for a, b in product(task.worlds, repeat=2))
        result[family] = task
    return result


def training():
    rng = random.Random(SEED)
    sets = {}
    for index in range(24):
        width = 3 + index % 2
        candidates = tuple(v for v in product(range(4), repeat=width) if 1 <= sum(bool(x) for x in v) < width)
        roles = tuple(tuple(rng.sample(candidates, 3)) for _ in range(2))
        name = f"synthetic-{index}"
        sets[name] = workshop(name, tuple(str(i) for i in range(width)), roles)
    return sets


def features(task, key):
    _, phase, left, right, sent = key
    if phase == 3:
        a, b = task.card(0, left), task.card(1, right)
        return [(0., 0., 0., float(bool(left)), float(bool(right)), 0., 0.,
                 float(i == task.hold), x / 3, y / 3)
                for i, (x, y) in enumerate(zip((*a, 0), (*b, 0), strict=True))]
    legal, _ = relay.message_rows(phase, left, right, sent)
    return [(float(phase == 0), float(phase == 1), float(phase == 2),
             float(bool(right)), float(sent), float(action == relay.OWN),
             float(action == relay.FORWARD), 0., 0., 0.) for action in legal]


class Policy(nn.Module):
    def __init__(self):
        super().__init__()
        self.actor = nn.Sequential(nn.Linear(10, 16), nn.Tanh(), nn.Linear(16, 1))

    def forward(self, inputs, legal):
        return self.actor(inputs).squeeze(-1).masked_fill(~legal, -torch.inf)


def paths(tasks):
    result = []
    for name, task in tasks.items():
        for world in task.worlds:
            branches = enumerate_joint_action_paths(task, world, {}, name)
            result.append((task, world, branches))
    return result


def fit(episodes, criterion):
    keys = sorted({key for _, _, branches in episodes for _, trace in branches for key, _ in trace})
    task_by_name = {task.name: task for task, _, _ in episodes}
    width = max(task.hold + 1 for task in task_by_name.values())
    inputs = torch.zeros((len(keys), width, 10))
    legal = torch.zeros((len(keys), width), dtype=torch.bool)
    for i, key in enumerate(keys):
        rows = torch.tensor(features(task_by_name[key[0]], key))
        inputs[i, :len(rows)] = rows
        legal[i, :len(rows)] = True
    key_ids = {key: i for i, key in enumerate(keys)}
    ids, actions, present, rewards, groups = [], [], [], [], []
    for index, (task, world, branches) in enumerate(episodes):
        best = task.optimal(*world)
        for record, trace in branches:
            chosen = task.actions.index(record["choice"])
            left, right = delivered(record)
            justified = chosen in task.optimal_warrant(left, right)
            value = record["warranted"] if criterion == "feasibility" else justified and chosen in best
            rewards.append(float(value) - relay.MESSAGE_COST * record["messages"])
            groups.append(index)
            ids.append([key_ids[k] for k, _ in trace] + [0] * (4 - len(trace)))
            actions.append([i for _, i in trace] + [0] * (4 - len(trace)))
            present.append([True] * len(trace) + [False] * (4 - len(trace)))
    ids, actions, present, rewards, groups = map(torch.tensor, (ids, actions, present, rewards, groups))
    torch.manual_seed(SEED)
    policy = Policy()
    optimizer = torch.optim.Adam(policy.parameters(), lr=.045)
    updates = []
    for index in range(STEPS):
        logits = policy(inputs, legal).log_softmax(-1)
        p = logits[ids, actions].masked_fill(~present, 0.).sum(-1).exp()
        mass = torch.zeros(len(episodes)).index_add_(0, groups, p.detach())
        assert torch.allclose(mass, torch.ones_like(mass), atol=2e-6)
        score = p @ rewards / len(episodes)
        optimizer.zero_grad()
        (-score).backward()
        gradient = float(nn.utils.clip_grad_norm_(policy.parameters(), 1., error_if_nonfinite=True))
        optimizer.step()
        updates.append({"step": index + 1, "expected_return": float(score.detach()), "gradient": gradient})
    return policy, updates


def delivered(record):
    left, right = 0, 0
    for event in record["deliveries"][1:]:
        if event["owner"] == "relay":
            left = event["delivered_mask"] or left
        else:
            right = event["delivered_mask"]
    return left, right


def choose(task, policy, message_policy, world, channel):
    class LocalActor(Adapter):
        def distribution(self, kind, rows):
            phase, left, right, sent, legal = self.view
            rule = policy if phase == 3 else message_policy
            if rule == "optimal" or rule == "feasible":
                eligible = (task.optimal_warrant(left, right) if rule == "optimal"
                            else task.warrant(left, right))
                pick = min(eligible) if eligible else task.hold
                scores = torch.tensor([float(i == pick) for i in legal])
            elif rule == "send":
                pick = relay.FORWARD if relay.FORWARD in legal else relay.OWN if relay.OWN in legal else relay.PASS
                scores = torch.tensor([float(i == pick) for i in legal])
            else:
                values = torch.tensor(features(task, (task.name, phase, left, right, sent)))
                scores = rule(values, torch.ones(len(values), dtype=torch.bool))
            self.trace.append({"phase": phase, "legal": legal, "logits": scores.tolist()})
            return torch.distributions.Categorical(logits=scores)

    record, turns = LocalActor(task.name, {}, None).play(task, world, channel)
    left, right = delivered(record)
    selected = task.actions.index(record["choice"])
    actual = task.optimal(*world)
    warranted = task.optimal_warrant(left, right)
    return {**record, "turns": turns, "feasible_options": sorted(task.valid(*world)),
            "optimal_options": sorted(actual), "visible_optimal_options": sorted(warranted),
            "optimal": selected in actual, "warranted_optimal": selected in warranted,
            "quality": task.quality(*world, selected)}


def run():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    train, test = training(), fixtures()
    episodes = paths(train)
    trained = {criterion: fit(episodes, criterion) for criterion in ("feasibility", "optimality")}
    arms = {
        "fixed_feasibility": ("feasible", "send"),
        "fixed_optimality": ("optimal", "send"),
        "learned_feasibility": (trained["feasibility"][0],) * 2,
        "learned_optimality": (trained["optimality"][0],) * 2,
        "optimal_chair_full_delivery": (trained["optimality"][0], "send"),
        "checked_chair_learned_delivery": ("optimal", trained["optimality"][0]),
    }
    with torch.no_grad():
        results = {
            label: {name: {channel: [choose(task, policy, message_policy, w, channel)
                                    for w in task.worlds]
                           for channel in ("peer", "one_round", "mute_near", "mute_far", "mute_both")}
                    for name, task in test.items()}
            for label, (policy, message_policy) in arms.items()
        }
    return {
        "scope": "Typed simulation with private fictional scores. A feasible compromise maximizes the lower score, then the sum. All exact ties are accepted. No historical vote or actual national preference is used as utility.",
        "source_hashes": {str(p.relative_to(relay.HERE)): sha256(p.read_bytes()).hexdigest()
                          for p in (Path(__file__).resolve(), Path(relay.__file__),
                                    Path(relay.HERE / "relay_text_train.py"), *FILES)},
        "seed": SEED, "training_tasks": len(train), "training_worlds": len(episodes),
        "test_cards": {name: task.cards for name, task in test.items()},
        "test_options": {name: task.actions for name, task in test.items()},
        "training": {criterion: {"weights": {k: t.tolist() for k, t in p.state_dict().items()},
                                 "updates": trace} for criterion, (p, trace) in trained.items()},
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), separators=(",", ":")))
