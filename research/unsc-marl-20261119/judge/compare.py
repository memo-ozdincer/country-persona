"""Pair scored final records at the negotiation-family level."""
from collections import defaultdict
import json
from pathlib import Path
import sys

from score import score


def compare(pairs):
    families = defaultdict(list)
    ids = set()
    for pair in pairs:
        left, right = pair["control"], pair["candidate"]
        check_ids = {x["packet"]["id"] for x in (left, right)}
        if len(check_ids) != 2 or ids & check_ids:
            raise ValueError("Final records require distinct opaque IDs")
        ids.update(check_ids)
        if any(left["packet"][key] != right["packet"][key] for key in ("task", "rubric", "evidence")):
            raise ValueError("Comparison requires common task, rubric and evidence")
        a, b = (score(item["packet"], item["verdict"]) for item in (left, right))
        families[pair["family"]].append({
            "case": pair["case"], "control": a, "candidate": b,
            "final_delta_bounds": [b["final"]["lower"] - a["final"]["upper"],
                                   b["final"]["upper"] - a["final"]["lower"]],
            "strict_delta": int(b["strict"]) - int(a["strict"]),
        })
    if not families:
        raise ValueError("No scored comparisons")
    means = {family: [sum(e["final_delta_bounds"][i] for e in rows) / len(rows) for i in (0, 1)]
             for family, rows in families.items()}
    return {
        "unit": "rubric points out of 70, candidate minus control",
        "family_macro_delta_bounds": [sum(v[i] for v in means.values()) / len(means) for i in (0, 1)],
        "family_delta_bounds": means, "family_cases": dict(families),
    }


if __name__ == "__main__":
    print(json.dumps(compare(json.loads(Path(sys.argv[1]).read_text())["pairs"]), indent=2))
