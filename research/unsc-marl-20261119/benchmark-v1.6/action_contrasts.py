"""Author-labeled development contrasts, separate public tasks from answer keys."""
import argparse
from itertools import permutations

import json
from pathlib import Path

def winners(menu, cards, mode):
    feasible = {name: (min(left, right), left + right)
                for name, left, right in zip(menu[:-2], *cards, strict=True) if min(left, right)}
    if not feasible:
        return {"impasse"}
    if mode == "first feasible":
        return {next(iter(feasible))}
    if mode in {"minimum", "sum"}:
        feasible = {name: score[int(mode == "sum")] for name, score in feasible.items()}
    best = max(feasible.values())
    return {name for name, score in feasible.items() if score == best}


def warrant(sets):
    return set.intersection(*sets) or {"unresolved"}


# One known delegate and a public domain for the other. A singleton is complete.
CASES = [
    ("priority", (1, 2), [(3, 2)], {"B"}),
    ("tiebreak", (1, 1), [(2, 3)], {"B"}),
    ("exact_tie", (1, 2), [(2, 1)], {"A", "B"}),
    ("zero_excludes", (0, 1), [(3, 1)], {"B"}),
    ("impasse", (0, 1), [(3, 0)], {"impasse"}),
    ("tie_with_common_choice", (2, 2, 2), [(2, 2, 1), (1, 2, 2)], {"B"}),
    ("no_common_choice", (2, 2, 2), [(2, 2, 1), (1, 2, 2), (2, 1, 2)], {"unresolved"}),
]


def build():
    inputs, keys, summaries = [], [], {}
    for name, known, possibilities, authored in CASES:
        letters = tuple("ABC"[:len(known)])
        for order in permutations(range(len(known))):
            menu = [*letters, "impasse", "unresolved"]
            first = [known[i] for i in order]
            second = [[card[i] for i in order] for card in possibilities]
            expected = {letters[j] for j,i in enumerate(order) if letters[i] in authored} | (authored - set(letters))
            domain = [(first, other) for other in second]
            rule_sets = {mode:warrant([winners(menu,world,mode) for world in domain])
                         for mode in ("full","minimum","sum","first feasible")}
            assert rule_sets["full"] == expected
            index = len(inputs)
            inputs.append({"id":index,"menu":menu,"known_grades":first,"other_public_possibilities":second})
            keys.append({"id":index,"contrast":name,"correct":sorted(expected)})
            for mode, allowed in rule_sets.items():
                single, exact = summaries.get(mode, (0,0))
                chosen = next(a for a in menu if a in allowed)
                summaries[mode] = single + (chosen in expected), exact + (allowed == expected)
    return {"tasks":inputs,"key":keys,"checks":{"presentations":len(inputs),"contrasts":len(CASES),
            "single_choice_and_exact_set":summaries}}


def score(rows):
    gold = {row["id"]: row for row in build()["key"]}
    tasks = {row["id"]: row for row in build()["tasks"]}
    if not isinstance(rows, list) or len(rows) != len(gold):
        raise ValueError("Exactly one response per presentation is required")
    seen = set()
    totals = {}
    for row in rows:
        key = row["id"]
        if (set(row) != {"id", "choice", "choices"} or type(key) is not int
                or key not in gold or key in seen):
            raise ValueError("Missing, duplicate or unexpected presentation")
        seen.add(key)
        menu = tasks[key]["menu"]
        choices = row["choices"]
        if (not isinstance(choices, list) or not choices or any(choice not in menu for choice in choices)
                or len(set(choices)) != len(choices) or row["choice"] not in choices):
            raise ValueError("Provide a nonempty set of legal choices containing the selected action")
        target = gold[key]
        counts = totals.setdefault(target["contrast"], {"n": 0, "selected_correct": 0, "set_correct": 0})
        counts["n"] += 1
        counts["selected_correct"] += row["choice"] in target["correct"]
        counts["set_correct"] += sorted(choices) == target["correct"]
    return {"contrasts": totals,
            "total": {name: sum(r[name] for r in totals.values())
                      for name in ("n", "selected_correct", "set_correct")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", choices=("tasks", "key", "checks", "score"))
    parser.add_argument("--responses", type=Path)
    args = parser.parse_args()
    if args.output == "score":
        if args.responses is None:
            parser.error("score requires --responses")
        result = score(json.loads(args.responses.read_text()))
    else:
        result = build()[args.output]
    print(json.dumps(result, indent=2))
