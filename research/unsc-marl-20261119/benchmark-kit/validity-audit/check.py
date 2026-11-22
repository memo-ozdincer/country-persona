"""Independent, standard-library replay of the three reported action panels."""
from collections import Counter, defaultdict
import hashlib
from itertools import product
import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "evidence"
BASE = DIR / "relay-compromise-language/actions.jsonl"
PARTIAL = DIR / "relay-compromise-public/actions.jsonl"
FIT = DIR / "relay-compromise-public/completions.json"
GRADES = {"acceptable": 1, "preferred": 2, "strongly preferred": 3}


def observation(row):
    _, first, second, *options = row["messages"][-1]["content"].splitlines()
    names = tuple(line.split(". ")[1] for line in options)
    def domain(line):
        text = line.split("Delivered card. ")[1] if "Delivered card." in line else line.split("public possibilities are ")[1]
        cards = []
        for description in text.rstrip(".").split(" / "):
            grades = dict.fromkeys(names[:-2], 0)
            for claim in description.split("; "):
                name, degree = claim.split(" is ")
                grades[name] = GRADES[degree]
            cards.append(tuple(grades.values()))
        return cards
    return names, list(product(domain(first), domain(second)))


def winners(names, cards, mode):
    a, b = cards
    values = {}
    for name, x, y in zip(names[:-2], a, b, strict=True):
        if min(x, y):
            if mode == "sum": values[name] = x+y
            elif mode == "minimum": values[name] = min(x,y)
            elif mode == "first feasible": return {name}
            else: values[name] = (min(x,y), x+y)
    return {k for k,v in values.items() if v == max(values.values())} or {"impasse"}


def warrant(sets):
    return set.intersection(*sets) or {"unresolved"}


def run():
    fitted = json.loads(FIT.read_text())["rows"]
    archive = {}
    full = {}
    for path in (BASE, PARTIAL):
        for line in path.read_text().splitlines():
            r = json.loads(line)
            label, _, left, right, _ = r["observation"]
            family, _, condition = label.partition("/")
            if family not in {"venezuela","space"}: continue
            names, completions = observation(r)
            answer = names[max(range(len(names)), key=r["scores"].__getitem__)]
            key = (family, condition or ("complete" if left and right else "incomplete"), left, right)
            assert key not in archive
            archive[key] = names, completions, answer
            if left and right: full[family, completions[0]] = answer
    counts = defaultdict(Counter)
    differences = []
    seen = set()
    for row in fitted:
        f, c = row["family"], row["condition"]
        key = f,c,*row["visible_cards"]
        assert key not in seen
        seen.add(key)
        names, worlds, direct = archive[key]
        gold = warrant([winners(names,w,"full") for w in worlds])
        assert gold == set(row["warranted_choices"])
        group = c if c in ("complete","incomplete") else "narrowed"
        results = {"direct frozen": direct, "completion frozen": next(iter(warrant([{full[f,w]} for w in worlds]))),
                   "completion fitted": row["answers"]["top_1"], "always unresolved": "unresolved"}
        for mode in ("minimum","sum","first feasible","full"):
            result = warrant([winners(names,w,mode) for w in worlds])
            results[mode] = next(name for name in names if name in result)
            if result != gold:
                differences.append({"case":key,"rule":mode,"allows":sorted(result),"gold":sorted(gold)})
        counts[group]["views"] += 1
        for mode, value in results.items(): counts[group][mode] += int(value in gold)
    assert seen == archive.keys()
    return {"source_sha256":{p.name+":"+p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE,PARTIAL,FIT]},
            "scores":counts, "set_disagreements":differences}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
