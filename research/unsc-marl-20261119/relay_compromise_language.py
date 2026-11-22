"""Score a frozen Qwen chair on prose preference cards and matched views."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import relay_compromise as ranked
import relay_text as scorer

HERE = Path(__file__).resolve().parent
GRADES = {1: "acceptable", 2: "preferred", 3: "strongly preferred"}
OFFSETS = {"venezuela": 2, "space": 4}


def describe(names, card):
    return "; ".join(f"{name} is {GRADES[grade]}" for name, grade in zip(names, card, strict=True) if grade)


def tasks():
    result = ranked.fixtures()
    # Isolated synthetic scenes provide an independent development reference.
    for name, task in list(ranked.training().items())[:2]:
        result[name] = task
    return result


def menu(name, task):
    options = task.actions[:-1]
    shift = OFFSETS.get(name, 0)
    return (*options[shift:], *options[:shift], "impasse", "unresolved")


def scene(name, task, left, right):
    names = task.actions[:-1]
    listing = menu(name, task)
    role_views = []
    for i, (role, code) in enumerate(zip(("Relay delegate", "Far delegate"), (left, right), strict=True)):
        if code:
            status = "Delivered card. " + describe(names, task.card(i, code)) + "."
        else:
            possibilities = [describe(names, card) for card in task.cards[i]]
            status = "Card absent. Its public possibilities are " + " / ".join(possibilities) + "."
        role_views.append(f"{role}. {status}")
    public = (
        f"Fictional {name} drafting workshop. "
        "On each card, unlisted packages are unacceptable. "
        "Acceptable earns 1, preferred earns 2, and strongly preferred earns 3. "
        "Among packages acceptable to both, favor the highest lower grade of the two "
        "delegates, breaking ties by the highest sum of grades. Either exact tie is valid. "
        "Choose impasse if there is no mutually acceptable package. "
        "If a missing card leaves no single choice top-ranked in every public possibility, "
        "choose unresolved. Treat all rankings as fictional workshop information."
    )
    choices = [f"{label}. {choice}" for label, choice in zip("ABCDEFGHI", listing)]
    messages = [
        {"role": "system", "content": "You are the workshop chair. Return only one listed answer letter."},
        {"role": "user", "content": "\n".join((public, *role_views, *choices))},
    ]
    return {"observation": (name, 3, left, right, False),
            "legal": tuple(range(len(listing))), "messages": messages}


def observations():
    for name, task in tasks().items():
        for left, right in product((0, *task.first), (0, *task.second)):
            yield scene(name, task, left, right)


def hashes():
    return {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__).resolve(), Path(ranked.__file__), Path(scorer.__file__), *ranked.FILES)}


@contextmanager
def inputs():
    with patch.object(scorer, "observations", new=observations), patch.object(scorer, "hashes", new=hashes), \
         patch.object(scorer, "LETTERS", new="ABCDEFGHI"):
        yield


def evaluate(directory):
    with inputs():
        scores = scorer.read(directory)
    fixtures = tasks()
    groups = {}
    for (name, _, left, right, _), row in sorted(scores.items()):
        task = fixtures[name]
        listing = menu(name, task)
        allowed = {task.actions[i] for i in task.optimal_warrant(left, right)} or {"unresolved"}
        best = listing[max(range(len(listing)), key=row["scores"].__getitem__)]
        partial = "both" if left and right else "left" if left else "right" if right else "neither"
        summary = {"visible_cards": [left, right], "choice": best, "warranted_choices": sorted(allowed),
                   "pass": best in allowed, "legal_mass": row["legal_mass"]}
        if left and right:
            valid = {task.actions[i] for i in task.valid(left, right)}
            summary.update({"scenario": "impasse" if valid == {"impasse"} else "agreement",
                            "feasible": best in valid, "feasible_options": sorted(valid)})
        groups.setdefault(name, {}).setdefault(partial, []).append(summary)
    return {"groups": groups, "observations": len(scores),
            "family_split": {"evaluation": list(OFFSETS), "synthetic": [k for k in groups if k not in OFFSETS]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "replay"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        if args.model is None:
            parser.error("--model is required for run")
        with inputs():
            scorer.score(args.model, args.directory)
    else:
        print(json.dumps(evaluate(args.directory), ensure_ascii=False, indent=2))
