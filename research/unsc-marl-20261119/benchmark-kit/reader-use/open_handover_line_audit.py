"""Diagnose semantic decisions when another generated line breaks the strict format."""
import argparse
import json
from pathlib import Path
import re

import open_handover as trial

# Match only a uniquely identified field line. A malformed field cannot
# suppress inspection of an adjacent line, and duplicate fields are invalid.
LINE = re.compile(r"F([12])\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)")


def parse(text):
    grouped = {"1": [], "2": []}
    for value in text.splitlines():
        matched = LINE.fullmatch(value.strip())
        if matched:
            line, *columns = matched.groups()
            grouped[line].append(tuple(s.strip() for s in columns))
    return {key: values[0] for key, values in grouped.items() if len(values) == 1}


def run(directory):
    rows = trial.replay(directory)
    source = trial.prior.fixtures()
    result = {}
    for arm in (*trial.prior.ARMS, "field_receipt_with_gate", "field_receipt_compare_date"):
        gated = arm not in trial.prior.ARMS
        by_family = {}
        decisions = []
        for case, key in zip(source["inputs"], source["keys"], strict=True):
            raw = rows[f"{case['id']:02}/{'field_receipt' if gated else arm}"]
            fields = parse(raw["output"])
            measured = []
            for position, (field, _, sid) in enumerate(trial.prior.handover.CASES[case["family"]], 1):
                expected = (key["actions"][field], trial.as_iso(key["deliverable"][field]) or "-",
                            sid if key["deliverable"][field] is not None else "-")
                original = fields.get(str(position))
                proposed = original
                if proposed and proposed[0] == "verify" and proposed[1] in ("-", ""):
                    proposed = ("verify", "-", "-")
                if gated and case["holdings"][sid] is None:
                    proposed = ("verify", "-", "-")
                if arm == "field_receipt_compare_date" and proposed and proposed[0] in ("confirm", "correct") and proposed[2] == sid:
                    try:
                        valid_iso = trial.date.fromisoformat(proposed[1]).isoformat() == proposed[1]
                    except ValueError:
                        valid_iso = False
                    if valid_iso:
                        action = "confirm" if proposed[1] == trial.as_iso(case["draft"][field]) else "correct"
                        proposed = (action, proposed[1], proposed[2])
                correct = proposed == expected
                invalid_certification = bool(proposed and proposed[0] in ("confirm", "correct")
                                             and expected[0] == "verify")
                measured.append({"field": field, "exact": correct, "line": original,
                                 "normalized": proposed, "expected": expected,
                                 "unsupported_certification": invalid_certification})
            decisions.append({"case": case["id"], "family": case["family"], "fields": measured,
                              "exact_handover": all(r["exact"] for r in measured)})
        for family in trial.prior.handover.CASES:
            group = [case for case in decisions if case["family"] == family]
            by_family[family] = {"exact_fields": sum(f["exact"] for c in group for f in c["fields"]),
                                 "exact_handovers": sum(c["exact_handover"] for c in group),
                                 "unsupported_certifications": sum(f["unsupported_certification"] for c in group for f in c["fields"])}
        split = {}
        for inventory in ("overlap", "split"):
            split[inventory] = {}
            for peer in (True, False):
                masks = trial.prior.exact_receipt_probabilities(inventory, peer)
                usable = sum(masks[row["case"] % 4] / 8 for row in decisions
                             if row["case"] % 4 == 3 and row["exact_handover"])
                split[inventory]["visible" if peer else "erased"] = usable
        result[arm] = {"families": by_family, "replay_complete_usable": split, "decisions": decisions}
    return {"scope": "Post-hoc diagnostic. Accept independently interpretable lines and normalize only blank or "
                     "dash dates on explicit verification actions. The comparison variant derives the action from the draft and model date. No model date changes.",
            "arms": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory), indent=2))
