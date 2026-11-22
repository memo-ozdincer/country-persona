"""Run the validity-audit contrasts through frozen and fitted Qwen chairs."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import torch

import relay_compromise_joint as joint
import relay_compromise_language as language
from relay_compromise_completions import FIT
from relay_compromise_language_audit import view

AUDIT = Path(__file__).resolve().parent / "benchmark-kit/validity-audit"
sys.path.insert(0, str(AUDIT))
from contrasts import build
sys.path.pop(0)


def prepared():
    panels = build()
    pool, rows, mapping = {}, [], []
    for item, gold in zip(panels["tasks"], panels["key"], strict=True):
        cards = ((tuple(item["known_grades"]),), tuple(map(tuple, item["other_public_possibilities"])))
        task = language.ranked.workshop("ordinal drafting", tuple(item["menu"][:-2]), cards)
        left, = task.first
        def add(right):
            candidate = language.scene(task.name, task, left, right)
            msg = candidate["messages"][-1]["content"]
            if msg not in pool:
                key = (f"contrast-{len(rows):02d}", 3, bool(left), bool(right), False)
                rows.append({**candidate, "observation": key})
                pool[msg] = key
            return pool[msg]
        complete = [add(right) for right in task.second]
        direct = complete[0] if len(complete) == 1 else add(0)
        mapping.append({**item, **gold, "direct": direct, "completions": complete})
    return rows, mapping


def observations():
    return iter(prepared()[0])


def hashes():
    files = (Path(__file__).resolve(), AUDIT / "contrasts.py", AUDIT / "check.py", FIT)
    return {**language.hashes(), **{str(p.relative_to(language.HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


@contextmanager
def inputs():
    scorer = language.scorer
    with language.inputs(), patch.object(scorer, "observations", new=observations), \
         patch.object(scorer, "hashes", new=hashes):
        yield


def unanimous(values):
    return values[0] if len(set(values)) == 1 else "unresolved"


def evaluate(directory):
    torch.set_num_threads(1)
    with inputs():
        scores = language.scorer.read(directory)
    policy = joint.Joint(True)
    model = json.loads(FIT.read_text())["training"]["qwen_joint"]["state"]
    policy.load_state_dict({k: torch.tensor(v) for k, v in model.items()})
    decisions = {}
    with torch.no_grad():
        for key, row in scores.items():
            _, left_card, right_card, *options = row["messages"][-1]["content"].splitlines()
            menu = [part.split(". ", 1)[1] for part in options]
            known, a = view(left_card, menu[:-2])
            delivered, b = view(right_card, menu[:-2])
            features = [(float(known), float(delivered), x / 3, y / 3, 0., 0.) for x, y in zip(
                a[0] if known else [0] * (len(menu) - 2), b[0] if delivered else [0] * (len(menu) - 2), strict=True)]
            features.extend(((float(known), float(delivered), 0., 0., 1., 0.),
                             (float(known), float(delivered), 0., 0., 0., 1.)))
            frozen = torch.tensor(row["scores"])
            trained = policy.rank(torch.tensor(features), frozen)
            decisions[key] = (menu[int(frozen.argmax())], menu[int(trained.argmax())])
    panels = []
    for row in prepared()[1]:
        direct = decisions[row["direct"]]
        completions = [decisions[key] for key in row["completions"]]
        choices = {
            "frozen_direct": direct[0], "fitted_direct": direct[1],
            "frozen_completion": unanimous([a for a, _ in completions]),
            "fitted_completion": unanimous([b for _, b in completions]),
        }
        panels.append({**row, "choices": choices, "correct_by_policy": {k: v in row["correct"] for k, v in choices.items()},
                       "completion_choices": completions})
    return {"prompt_count": len(decisions), "frozen_fit_sha256": sha256(FIT.read_bytes()).hexdigest(), "panels": panels}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("score", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "score":
        if args.model is None:
            cli.error("--model is required for score")
        with inputs():
            language.scorer.score(args.model, args.directory)
    else:
        print(json.dumps(evaluate(args.directory), indent=2))
