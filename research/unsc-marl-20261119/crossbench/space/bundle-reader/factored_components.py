"""Check whether bitwise agreement rescues speech acts before applying the sign gate."""
import argparse
from collections import Counter
import json
from pathlib import Path


def evaluate(path):
    original = json.loads((path/"metrics.json").read_text())
    rows = {x["id"]:x for x in map(json.loads,(path/"predictions.jsonl").read_text().splitlines())}
    counts, cases = Counter(), {}
    for ident, details in original["bundles"].items():
        top, spans = [], []
        for order in range(2):
            row = rows[f"{ident}/joint/{order}"]
            best = max(row["label_logits"])
            top.extend(k for k,v in zip(row["values"],row["label_logits"],strict=True) if v==best)
        for bit in (1,2):
            possible = {bool(candidate & bit) for candidate in top}
            spans.append(possible.pop() if len(possible)==1 else None)
        yes,no = details["stable_package_signs"]
        projected = [spans[0] is True and yes is True, spans[1] is True and no is False]
        assert all(not old or new for old,new in zip(details["decoded"]["factored"],projected,strict=True))
        counts["exact_bundle"] += projected==details["expected"]
        for expected, decision in zip(details["expected"],projected,strict=True):
            counts["true_admissions"] += expected and decision
            counts["false_admissions"] += not expected and decision
        cases[ident] = {"invariant_speech":spans,"decoded":projected,"expected":details["expected"]}
    return {"scope":"No extra model calls. Admit an invariant component only after the same archived package-sign gate.",
            "totals":dict(counts),"bundles":cases}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    print(json.dumps(evaluate(parser.parse_args().directory),indent=2))
