"""Separate permission from attribution and check matched reader comparisons."""
import argparse
from collections import Counter
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Author reading of the two speech acts, before mandate validation.
COMMIT = {"M1": (True, True), "M2": (True, False), "M3": (False, True),
          "M4": (True, True), "S1": (True, True), "S2": (True, True),
          "S3": (False, True), "S4": (False, False)}
MENUS = {"france-overlap": "AEG", "france-impasse": "AG", "japan": "ADF",
         "china-overlap": "BFG", "china-impasse": "BG"}


def analyze(report):
    count = Counter()
    details = {}
    for case in json.loads((HERE / "fixtures.json").read_text()):
        key = case["id"]
        menu = MENUS[case["card"]]
        support = (case["accept"] in menu, case["exclude"] not in menu)
        gold = [a and b for a,b in zip(COMMIT[key],support,strict=True)]
        assert case["expected"] == gold
        joint, split = (report["bundles"][key]["decoded"][mode] for mode in ("joint","split"))
        arm = {"joint": joint, "split": split,
               "corroborated": [a is True and b is True for a,b in zip(joint,split,strict=True)]}
        details[key] = {"commitment_in_message": COMMIT[key], "mandate_support": support,
                        "expected": gold, "admitted": arm}
        count["exact_pair_pattern",str(joint==gold),str(split==gold)] += 1
        for mode, predictions in arm.items():
            for speech, allowed, expected, label in zip(COMMIT[key], support, gold, predictions, strict=True):
                if label is True:
                    count[mode,"admitted"] += 1
                    count[mode,"true" if expected else "false"] += 1
                    if not speech:
                        count[mode,"false_attribution"] += 1
                    if not allowed:
                        count[mode,"incompatible_mandate"] += 1
                elif expected:
                    count[mode,"withheld_true"] += 1
    return {"scope":"Assistant-authored commitment and mandate decomposition. Attribution and mandate errors can overlap.",
            "totals":{"/".join(k):v for k,v in count.items()},"details":details}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics",type=Path)
    print(json.dumps(analyze(json.loads(parser.parse_args().metrics.read_text())),indent=2))
