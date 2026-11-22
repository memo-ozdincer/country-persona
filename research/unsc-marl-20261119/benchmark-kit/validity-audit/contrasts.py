"""Author-labeled development contrasts, separate public tasks from answer keys."""
import argparse
from itertools import permutations

from check import warrant, winners
import json

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",choices=("tasks","key","checks"))
    print(json.dumps(build()[parser.parse_args().output],indent=2))
