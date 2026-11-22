"""Test public grade bounds as an input to the ranked MARL policy."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import torch
from torch import nn

import relay_compromise_joint as joint
import relay_compromise_language as language
from relay_compromise_audit import oracle
from relay_compromise_language_audit import view
import relay_compromise_public as public


class WiderChair(joint.Joint):
    def __init__(self, use_qwen):
        super().__init__(use_qwen)
        self.chair = nn.Sequential(nn.Linear(10, 24), nn.Tanh(), nn.Linear(24, 1))


def read(directory, inputs):
    with inputs():
        return language.scorer.read(directory)


def features(raw, bounds):
    observations = {}
    for key, row in sorted(raw.items()):
        _, relay, far, *options = row["messages"][-1]["content"].splitlines()
        menu = tuple(x.split(". ", 1)[1] for x in options)
        names = menu[:-2]
        seen_left, left = view(relay, names)
        seen_right, right = view(far, names)
        assert (seen_left, seen_right) == tuple(bool(x) for x in key[2:4])
        rows = []
        for i in range(len(names)):
            a = tuple(card[i] for card in left)
            b = tuple(card[i] for card in right)
            known = (a[0] / 3 if seen_left else 0., b[0] / 3 if seen_right else 0.)
            limits = tuple(x / 3 for x in (min(a), max(a), min(b), max(b))) if bounds else (0.,) * 4
            rows.append((float(seen_left), float(seen_right), *known, 0., 0., *limits))
        for impasse, unresolved in ((1., 0.), (0., 1.)):
            rows.append((float(seen_left), float(seen_right), 0., 0., impasse, unresolved, 0., 0., 0., 0.))
        observations[key] = (torch.tensor(rows), torch.tensor(row["scores"]), menu)
    return observations


def edge_cases(raw, models):
    scores = {"public_bounds": features(raw, True), "capacity_control": features(raw, False)}
    rows = []
    with torch.no_grad():
        for name, condition, task, left, right in public.panels():
            label = f"{name}/{condition}"
            key = (label, 3, left, right, False)
            good = set.intersection(*(oracle(task.actions[:-1], task.card(0, a), task.card(1, b))
                                      for a, b in task.completions(left, right))) or {"unresolved"}
            assert good == joint.acceptable(task, left, right)
            assert (good == {"impasse"} if condition == "impasse" else
                    good == {"unresolved"} if condition.startswith("ambiguous") else
                    not ({"impasse", "unresolved"} & good))
            guesses = {}
            for lab, model in models.items():
                f, frozen, menu = scores[lab][key]
                logits = model.rank(f, frozen)
                guesses[lab] = menu[int(logits.argmax())]
            _, frozen, menu = scores["public_bounds"][key]
            guesses["frozen_qwen"] = menu[int(frozen.argmax())]
            a, b = "relay", "far"
            rows.append({"family": name, "condition": condition, "visible": a if left else b,
                         "warranted_actions": sorted(good), "predictions": guesses,
                         "correct": {k: v in good for k, v in guesses.items()}})
    return rows


def run(challenge=None):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    tasks = language.tasks()
    train = {name: tasks[name] for name in ("synthetic-0", "synthetic-1")}
    test = {name: tasks[name] for name in language.OFFSETS}
    raw = read(joint.SOURCE, language.inputs)
    report, learned = {}, {}
    for mode, bounds in (("capacity_control", False), ("public_bounds", True)):
        table = features(raw, bounds)
        with patch.object(joint, "Joint", new=WiderChair):
            policy, updates, n = joint.train(train, table, True, True)
        learned[mode] = policy
        report[mode] = {"updates": updates, "training_paths": n,
                        "state": {k: v.tolist() for k, v in policy.state_dict().items()},
                        "synthetic": joint.evaluate(train, table, policy, policy, "model"),
                        "linked": joint.evaluate(test, table, policy, policy, "model")}
    result = {"training_families": list(train), "linked_families": list(test), "arms": report,
              "original_prompts_sha256": sha256((joint.SOURCE / "actions.jsonl").read_bytes()).hexdigest()}
    if challenge is not None:
        result["public_domain_changes"] = edge_cases(read(challenge, public.inputs), learned)
        result["challenge_prompts_sha256"] = sha256((challenge / "actions.jsonl").read_bytes()).hexdigest()
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--challenge", type=Path)
    args = cli.parse_args()
    print(json.dumps(run(args.challenge), separators=(",", ":")))
