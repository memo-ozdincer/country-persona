"""Intervene on one role-local field and replay the original routing policies."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
VENEZUELA = HERE / "crossbench/venezuela"
sys.path.insert(0, str(VENEZUELA))

import model_receipt as receipt


def compare(reference, changed):
    counts = Counter()
    assert reference.keys() == changed.keys()
    for key, before in reference.items():
        after = changed[key]
        _, variant, _, mode = key.split("/")
        group = "agreement" if variant == "ru-overlap" else "impasse"
        counts[group, mode, f"{int(before['counts'][0])}-{int(after['counts'][0])}"] += 1
        for i, metric in enumerate(("slots_delta", "checks_delta"), start=1):
            counts[group, mode, metric] += after["counts"][i]-before["counts"][i]
    return receipt.transfer.router.sp.flatten(counts)


def intervene(metrics):
    options = receipt.transfer.load(VENEZUELA/"case.json")["options"]
    results = {}
    for label in ("stable", "pooled"):
        condition = metrics["conditions"][label]
        fields = condition["fields"]
        deltas, verified_control, strict_timing = {}, {}, {}
        for name, original in fields.items():
            for index, field in enumerate(receipt.FIELDS):
                if original[index] == receipt.ANCHORS[name][index]:
                    continue
                repaired = {role: list(values) for role, values in fields.items()}
                repaired[name][index] = receipt.ANCHORS[name][index]
                signs = {role: {opt["id"]: receipt.projected(values, opt) for opt in options}
                         for role, values in repaired.items()}
                exclusions = {
                    role: [opt["id"] for opt in options
                           if values[0] is not None and opt["scope"] not in receipt.SCOPE_ALLOW[values[0]]]
                    for role, values in repaired.items()
                }
                for initial in ("authored", "modeled"):
                    result = receipt.policies(receipt.input_rows(signs, exclusions, initial))
                    baseline = condition["routing"][initial]["paths"]
                    deltas[f"{initial}/{name}/{field}"] = compare(baseline, result["paths"])
        for initial in ("authored", "modeled"):
            verified_control[initial] = compare(condition["routing"][initial]["paths"],
                                                metrics["conditions"]["authored"]["routing"][initial]["paths"])
            # A package may truly be disallowed for another reason. That
            # does not verify an incorrectly extracted timing restriction.
            defensible_scope = {
                name: options if fields[name][0] == receipt.ANCHORS[name][0] else []
                for name, options in condition["scope_before_admission"].items()
            }
            checked = receipt.policies(receipt.input_rows(
                condition["signs_before_admission"], defensible_scope, initial))
            strict_timing[initial] = compare(condition["routing"][initial]["paths"], checked["paths"])
        results[label] = {"single_field_interventions": deltas, "all_fields_authored": verified_control,
                          "require_exact_timing_for_scope_message": strict_timing}
    return {"scope": "Counterfactual attribution using authored field replacements. Every unedited field, opening, policy, and clean delivery trace stays fixed. Field corrections are retrospective and outside actual model results.",
            "conditions": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics", type=Path)
    args = parser.parse_args()
    print(json.dumps(intervene(json.loads(args.metrics.read_text())), indent=2))
