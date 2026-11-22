"""Joint team-return training for typed senders and a frozen-Qwen chair."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import torch
from torch import nn

import relay_compromise as ranked
import relay_compromise_language as language
from relay_compromise_language_audit import view
from relay_text_train import Adapter, enumerate_joint_action_paths

KIT = ranked.relay.KIT / "evidence"
SOURCE = KIT / "relay-compromise-language"
SEED = 61287
UPDATES = 100
SAFE_HOLD = .25
CHANNELS = ("peer", "one_round", "mute_near", "mute_far", "mute_both")
DELIVERY = ((True, True, .6), (True, False, .15), (False, True, .15), (False, False, .1))


def unpack():
    with language.inputs():
        scores = language.scorer.read(SOURCE)
    chair = {}
    for key, row in sorted(scores.items()):
        public, relay, far, *options = row["messages"][-1]["content"].splitlines()
        assert "highest lower grade" in public
        menu = tuple(x.split(". ", 1)[1] for x in options)
        names = menu[:-2]
        have_left, left = view(relay, names)
        have_right, right = view(far, names)
        assert (have_left, have_right) == tuple(bool(cd) for cd in key[2:4])
        # The policy gets only material present in the prompt. Missing values
        # are zeroed. A separate pair of flags distinguishes absence from veto.
        a = left[0] if have_left else (0,) * len(names)
        b = right[0] if have_right else (0,) * len(names)
        rows = [(float(have_left), float(have_right), x / 3, y / 3, 0., 0.)
                for x, y in zip(a, b, strict=True)]
        rows.extend(((float(have_left), float(have_right), 0., 0., 1., 0.),
                     (float(have_left), float(have_right), 0., 0., 0., 1.)))
        chair[key] = (torch.tensor(rows), torch.tensor(row["scores"]), menu)
    return chair


class Joint(nn.Module):
    def __init__(self, use_qwen):
        super().__init__()
        self.use_qwen = use_qwen
        self.relay = nn.Sequential(nn.Linear(10, 16), nn.Tanh(), nn.Linear(16, 1))
        self.chair = nn.Sequential(nn.Linear(6, 24), nn.Tanh(), nn.Linear(24, 1))

    def rank(self, features, frozen):
        return self.chair(features).squeeze(-1) + (frozen if self.use_qwen else 0.)


def acceptable(task, left, right):
    return {task.actions[i] for i in task.optimal_warrant(left, right)} or {"unresolved"}


def training_paths(tasks):
    paths = []
    for name, task in tasks.items():
        for world in task.worlds:
            # Final action in the old simulator is irrelevant for transport.
            for record, trace in enumerate_joint_action_paths(task, world, {}, name):
                route, (terminal, action) = trace[:-1], trace[-1]
                if action != 0:
                    continue
                received = ranked.delivered(record)
                assert terminal == (name, 3, *received, False)
                paths.append((task, world, route, terminal, record["messages"]))
    return paths


def coverage_paths(trajectories, classes):
    for task, world, route, key, messages in trajectories:
        name, phase, left, right, sent = key
        class_weight = 1 / (2 * classes[task.valid(*world) == {task.hold}])
        for keep_left, keep_right, probability in DELIVERY:
            yield task, world, route, (name, phase, left if keep_left else 0, right if keep_right else 0, sent), messages, probability * class_weight


def pad(tensors, length, value):
    return torch.stack([torch.cat((v, v.new_full((length - len(v), *v.shape[1:]), value))) for v in tensors])


def train(tasks, observations, use_qwen, coverage):
    nominal = training_paths(tasks)
    classes = Counter(task.valid(*world) == {task.hold} for task in tasks.values() for world in task.worlds)
    worlds = sum(classes.values())
    trajectories = (list(coverage_paths(nominal, classes)) if coverage else
                    [(*path, 1.) for path in nominal])
    relay_keys = sorted({key for _, _, route, _, _, _ in trajectories for key, _ in route})
    chair_keys = sorted({key for _, _, _, key, _, _ in trajectories})
    assert set(tasks) == {"synthetic-0", "synthetic-1"}
    relay_features = [torch.tensor(ranked.features(tasks[key[0]], key)) for key in relay_keys]
    chair_rows = [observations[k] for k in chair_keys]
    w = max(len(row[2]) for row in chair_rows)
    send = pad(relay_features, 3, 0.)
    send_mask = torch.arange(3)[None, :] < torch.tensor([len(f) for f in relay_features])[:, None]
    chair = pad([f for f, _, _ in chair_rows], w, 0.)
    frozen = pad([l for _, l, _ in chair_rows], w, 0.)
    chair_mask = torch.arange(w)[None, :] < torch.tensor([len(m) for _, _, m in chair_rows])[:, None]
    send_ids, acts, active, final_ids, costs, rewards, weights = [], [], [], [], [], [], []
    relay_ids = {k: i for i, k in enumerate(relay_keys)}
    chair_ids = {k: i for i, k in enumerate(chair_keys)}
    for task, _, route, key, messages, weight in trajectories:
        good = acceptable(task, key[2], key[3])
        choices = observations[key][2]
        reward = [((SAFE_HOLD if option == "unresolved" else 1.) if option in good else 0.)
                  for option in choices]
        send_ids.append([relay_ids[k] for k, _ in route] + [0] * (3 - len(route)))
        acts.append([a for _, a in route] + [0] * (3 - len(route)))
        active.append([True] * len(route) + [False] * (3 - len(route)))
        final_ids.append(chair_ids[key])
        costs.append(ranked.relay.MESSAGE_COST * messages)
        rewards.append(reward + [0.] * (w - len(reward)))
        weights.append(weight)
    send_ids, acts, active, final_ids, costs, rewards, weights = map(
        torch.tensor, (send_ids, acts, active, final_ids, costs, rewards, weights))
    torch.manual_seed(SEED)
    joint = Joint(use_qwen)
    optimizer = torch.optim.Adam(joint.parameters(), lr=.045)
    trace = []
    for step in range(UPDATES):
        relay_log = joint.relay(send).squeeze(-1).masked_fill(~send_mask, -torch.inf).log_softmax(-1)
        terminal_probs = joint.rank(chair, frozen).masked_fill(~chair_mask, -torch.inf).softmax(-1)
        route_prob = relay_log[send_ids, acts].masked_fill(~active, 0.).sum(-1).exp()
        if coverage:
            route_prob = route_prob * weights
        normalizer = 1 if coverage else worlds
        assert abs(float(route_prob.detach().sum()) - normalizer) < 1e-4
        payoff = (terminal_probs[final_ids] * rewards).sum(-1) - costs
        expected = (route_prob @ payoff) / normalizer
        optimizer.zero_grad()
        (-expected).backward()
        norms = {seat: float(nn.utils.clip_grad_norm_(network.parameters(), 1., error_if_nonfinite=True))
                 for seat, network in (("relay", joint.relay), ("chair", joint.chair))}
        optimizer.step()
        trace.append({"step": step + 1, "return": float(expected.detach()), "gradient_norms": norms})
    return joint, trace, len(trajectories)


def routed(task, joint, world, channel):
    class Delegate(Adapter):
        def distribution(self, kind, rows):
            phase, left, right, sent, legal = self.view
            if phase == 3:
                return torch.distributions.Categorical(logits=torch.zeros(len(legal)))
            if joint is None:
                action = ranked.relay.FORWARD if ranked.relay.FORWARD in legal else ranked.relay.OWN
                pick = action if action in legal else ranked.relay.PASS
                logits = torch.tensor([float(a == pick) for a in legal])
            else:
                key = (task.name, phase, left, right, sent)
                logits = joint.relay(torch.tensor(ranked.features(task, key))).squeeze(-1)
            return torch.distributions.Categorical(logits=logits)
    record, _ = Delegate(task.name, {}, None).play(task, world, channel)
    return record


def evaluate(tasks, observations, joint, send_policy, mode):
    results = {}
    with torch.no_grad():
        for name, task in tasks.items():
            results[name] = {}
            for channel in CHANNELS:
                rows = []
                for world in task.worlds:
                    record = routed(task, send_policy, world, channel)
                    left, right = ranked.delivered(record)
                    key = (name, 3, left, right, False)
                    features, frozen, menu = observations[key]
                    scores = frozen if joint is None else joint.rank(features, frozen)
                    good = acceptable(task, left, right)
                    if mode == "checked":
                        scores = torch.tensor([float(option in good) for option in menu])
                    selected = menu[int(scores.argmax())]
                    mass = sum(float(p) for a, p in zip(menu, scores.softmax(-1), strict=True) if a in good)
                    rows.append({"world": world, "received": [left, right], "choice": selected,
                                 "warranted_actions": sorted(good),
                                 "warranted": selected in good,
                                 "resolved": selected in good and selected != "unresolved",
                                 "scenario": "impasse" if task.valid(*world) == {task.hold} else "agreement",
                                 "turns": record["deliveries"], "probability_correct": mass})
                results[name][channel] = rows
    return results


def run(coverage=False):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    all_tasks = language.tasks()
    train_set = {name: task for name, task in all_tasks.items() if name.startswith("synthetic-")}
    test_set = {name: task for name, task in all_tasks.items() if name in language.OFFSETS}
    observations = unpack()
    learned = {name: train(train_set, observations, use, coverage)
               for name, use in (("qwen_joint", True), ("grades_joint", False))}
    qwen = learned["qwen_joint"][0]
    arms = {"qwen_frozen_with_full_transport": (None, None, "model"),
            "checked": (None, None, "checked"),
            "qwen_learned_chair_only": (qwen, None, "model"),
            "qwen_learned_senders_only": (None, qwen, "model")}
    arms.update({name: (joint, joint, "model") for name, (joint, _, _) in learned.items()})
    result = {
        "inputs_sha256": sha256((SOURCE / "actions.jsonl").read_bytes()).hexdigest(),
        "train_families": list(train_set), "test_families": list(test_set),
        "seed": SEED, "safe_unresolved_reward": SAFE_HOLD, "messages_cost": ranked.relay.MESSAGE_COST,
        "training": {name: {"updates": trace, "paths": n, "state": {k: v.tolist() for k, v in model.state_dict().items()}}
                     for name, (model, trace, n) in learned.items()},
        "test": {name: evaluate(test_set, observations, *arm) for name, arm in arms.items()},
    }
    if coverage:
        result["coverage"] = {"equal_class_weight": True, "chair_delivery_masks": DELIVERY}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.coverage), separators=(",", ":")))
