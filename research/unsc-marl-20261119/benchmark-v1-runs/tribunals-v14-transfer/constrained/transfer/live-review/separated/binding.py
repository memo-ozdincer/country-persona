"""Audit source-tag binding without regenerating or repairing any reply."""
import json
from pathlib import Path
import re
from statistics import mean

from pair_separation import HERE, READ, records, old


def bind(record, review):
    result = dict(review)
    if "met" not in review:
        return result
    paragraphs = dict(record["paragraphs"])
    rejected = []
    for criterion, cites in zip(record["criteria"], review["coverage"], strict=True):
        key = criterion["id"]
        tag = re.match(r"^(S[0-9]+)-", key)
        if tag and key in review["met"] and not any(paragraphs[i].startswith(f"[{tag[1]}] ") for i in cites):
            rejected.append(key)
    result["binding_rejections"] = rejected
    result["met"] = [criterion for criterion in review["met"] if criterion not in rejected]
    if review["guard"] == "clear":
        result["grade"] = record["public_base"] + sum(c["weight"] for c in record["criteria"]
                                                     if c["id"] in result["met"])
    if result["accepted"]:
        result["exact"] = (result["grade"] == record["expected_score"]
                           and result["guard"] == record["expected_guard"])
    return result


def run():
    original = READ(HERE / "results.json")
    gold = records()
    bound = {key: bind(gold[key], grade) for key, grade in original["grades"].items()}
    rows = []
    for row in original["rows"]:
        case = row["case"]
        new = bound[case + "/pair"]
        prior = original["grades"][case + "/pair"]
        if new["accepted"] and new["grade"] != prior["grade"]:
            # A grade matching a previously evaluated context can be replayed directly.
            assert new["grade"] == new["expected_score"]
            after = row["exact_counterfactual"]
        else:
            after = row["separated"]
        rows.append({k: row[k] for k in ("case", "law", "prior_information", "offset")} |
                    {"original": row["original"], "separated": row["separated"], "bound": after})
    net = [row["bound"]["net"] - row["original"]["net"] for row in rows]
    pins = (Path(__file__).resolve(), HERE / "binding-protocol.md", HERE / "results.json", HERE / "plan.json")
    return {"grades": bound, "summary": {"net_mean_over_original": mean(net),
                                        "wins": sum(x > 1e-7 for x in net),
                                        "ties": sum(abs(x) <= 1e-7 for x in net),
                                        "losses": sum(x < -1e-7 for x in net),
                                        "below_informed_silence": sum(row["bound"]["over_informed_silence_quality"] < -1e-7 for row in rows)},
            "rows": rows, "sha256": {file.name: old.digest(file) for file in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
