"""Apply exactly the same archived sign gate to the existing joint and split outputs."""
from collections import Counter
import json

import factored
import reader


def evaluate():
    directory = reader.HERE / "evidence"
    report = reader.load(directory / "metrics.json")
    mali, space = reader.load(factored.MALI)["package_predictions"], reader.load(factored.SPACE)["decisions"]
    counts, bundles = Counter(), {}
    for case in reader.load(reader.FIXTURES):
        key, card = case["id"], case["card"]
        labels = (case["accept"], case["exclude"])
        signs = [mali[card][label]["sign"] if case["family"] == "mali" else space[f"{card}/{label}"]["sign"]
                 for label in labels]
        permit = [signs[0] is True, signs[1] is False]
        gated = {}
        for mode, claims in report["bundles"][key]["decoded"].items():
            outcome = [q is True and a for q,a in zip(claims,permit,strict=True)]
            gated[mode] = outcome
            counts[mode,"exact_bundle"] += outcome == case["expected"]
            for actual, predicted in zip(case["expected"],outcome,strict=True):
                counts[mode,"true_admissions"] += actual and predicted
                counts[mode,"false_admissions"] += not actual and predicted
        bundles[key] = {"expected":case["expected"],"archived_signs":signs,"gated":gated}
    return {"scope":"Offline guard control. No new model calls.", "totals":{
        "/".join(key):value for key,value in counts.items()}, "bundles":bundles}


if __name__ == "__main__":
    print(json.dumps(evaluate(),indent=2))
