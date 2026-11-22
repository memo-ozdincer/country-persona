"""Expand model choices to packages with the same supported grade comparison."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


def expand(menu, left, right, choice):
    packages = dict(zip(menu[:-2], zip(left, right, strict=True), strict=True))
    values = packages.get(choice)
    if values is None or not all(values):
        return {choice}
    signature = min(values), sum(values)
    return {name for name, grades in packages.items() if all(grades) and (min(grades), sum(grades)) == signature}


def run(path):
    source = json.loads(path.read_text())
    results, totals = [], {}
    for panel in source["panels"]:
        choices, traces = {}, {}
        for index, name in enumerate(("frozen", "fitted")):
            tied = [expand(panel["menu"], panel["known_grades"], other, conclusions[index])
                    for other, conclusions in zip(panel["other_public_possibilities"], panel["completion_choices"], strict=True)]
            common = set.intersection(*tied) - {"unresolved"}
            chosen = next((a for a in panel["menu"] if a in common), "unresolved")
            allowed = set(panel["correct"])
            choices[name] = {"action": chosen, "correct": chosen in allowed,
                             "full_set_exact": (common or {"unresolved"}) == allowed}
            traces[name] = [sorted(v) for v in tied]
        results.append({"id": panel["id"], "contrast": panel["contrast"], "truth": panel["correct"],
                        "predictions": choices, "completion_sets": traces})
        tally = totals.setdefault(panel["contrast"], Counter())
        tally["presentations"] += 1
        for arm, row in choices.items():
            tally[arm + "_correct"] += row["correct"]
            tally[arm + "_full_set_exact"] += row["full_set_exact"]
    return {"source_sha256": sha256(path.read_bytes()).hexdigest(), "totals": totals, "presentations": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("report", type=Path)
    print(json.dumps(run(cli.parse_args().report), indent=2))
