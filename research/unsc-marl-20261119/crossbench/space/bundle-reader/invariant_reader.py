"""Recover components that agree across top joint choices without new calls."""
import argparse
from collections import Counter
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def evaluate(directory):
    cases = json.loads((HERE / "fixtures.json").read_text())
    rows = {r["id"]: r for r in map(json.loads, (directory / "predictions.jsonl").read_text().splitlines())}
    original = json.loads((directory / "metrics.json").read_text())
    totals, interpretations = Counter(), {}
    for case in cases:
        key = case["id"]
        highest = []
        for order in range(2):
            row = rows[f"{key}/joint/{order}"]
            peak = max(row["label_logits"])
            highest.append([value for value, logits in zip(row["values"],row["label_logits"],strict=True) if logits==peak])
        signs = []
        for bit in (1,2):
            possibilities = {bool(value & bit) for order in highest for value in order}
            signs.append(possibilities.pop() if len(possibilities)==1 else None)
        old = original["bundles"][key]["decoded"]["joint"]
        assert all(before is None or before == after for before,after in zip(old,signs,strict=True))
        for value, actual in zip(signs,case["expected"],strict=True):
            totals["correct" if value is actual else "abstain" if value is None else "wrong"] += 1
            totals["true_admissions"] += value is True and actual
            totals["false_admissions"] += value is True and not actual
        totals["exact_bundle"] += signs == case["expected"]
        interpretations[key] = {"top_choices":highest,"stable_components":signs,"expected":case["expected"]}
    return {"scope":"Same joint predictions. A component is invariant only if all top answer masks in both orders agree on it.",
            "totals":dict(totals),"bundles":interpretations}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path)
    print(json.dumps(evaluate(p.parse_args().output),indent=2))
