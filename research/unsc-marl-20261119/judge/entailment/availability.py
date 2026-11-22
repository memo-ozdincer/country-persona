"""Audit which mandate mistakes destroy the public proof before routing."""
import argparse
from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path

from package_panel import inputs, project


def audit(metrics):
    classify = Counter()
    ceilings = {}
    minimal_pairs = []
    for family, case, item in inputs():
        options = case["options"]
        signs = []
        gold = []
        for i, card in enumerate(item["cards"]):
            requirements = card["expected"]
            menu = project(options, requirements)
            gold.append(menu)
            known = {}
            for j, opt in enumerate(options):
                row = metrics["decisions"][f"{family}/{i}/{opt['id']}"]
                actual = bool(menu & (1 << j))
                assert row["expected"] == actual
                signed = row["accept"]
                if signed is not None and signed == actual:
                    known[opt["id"]] = signed
                overlap = sum(opt[key] == value for key, value in requirements.items())
                group = ("eligible" if actual else
                         "partially_matches" if overlap else "matches_no_requirement")
                kind = ("abstain" if signed is None else "correct" if actual == signed else "wrong")
                classify[family, group, kind] += 1
            signs.append(known)
            for (j,left),(k,right) in combinations(enumerate(options),2):
                left_ok, right_ok = (bool(menu & (1<<index)) for index in (j,k))
                diff = [field for field in left if field != "id" and left[field] != right[field]]
                if left_ok==right_ok or len(diff)!=1:
                    continue
                accepted, refused = (left,right) if left_ok else (right,left)
                minimal_pairs.append({"family":family,"role_index":i,"changed_field":diff[0],
                    "eligible":accepted["id"],"ineligible":refused["id"],
                    "both_correct":known.get(accepted["id"]) is True and known.get(refused["id"]) is False})
        joint = [o["id"] for o in options if all(signs[i].get(o["id"]) is True for i in (0, 1))]
        open_ = [o["id"] for o in options if not any(signs[i].get(o["id"]) is False for i in (0, 1))]
        firsts = product(*([o["id"] for j, o in enumerate(options) if mask & (1 << j)] for mask in gold))
        ceilings[family] = {
            "typed_outcome": item["outcome"],
            "potential_joint_from_all_correct_signs": joint,
            "unexcluded_after_all_correct_signs": open_,
            "qualifying_openings": sum(1 for _ in firsts),
            "evidence_is_sufficient_in_principle": bool(joint) if item["outcome"] == "agreement" else not open_,
        }
    return {"threshold": "Use all correct nonabstained per-option signs from these predictions. Ignore role sequencing and call costs.",
            "classification": {"/".join(k): v for k, v in classify.items()},
            "evidence_ceiling": ceilings, "one_field_switches":minimal_pairs}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics", type=Path)
    print(json.dumps(audit(json.loads(p.parse_args().metrics.read_text())), indent=2))
