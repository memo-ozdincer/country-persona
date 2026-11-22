"""Score blind revisions and their criterion-by-criterion deltas."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import facilitator_matched_2593_score as previous
import facilitator_revise_2593 as study

EVIDENCE = study.EVIDENCE


def blind(rows):
    ordered = sorted(rows, key=lambda key: sha256(("2593-revision-review/" + key).encode()).hexdigest())
    return {f"V{i + 1}": rows[key] for i, key in enumerate(ordered)}


def candidates(rows):
    return {alias: {"ended": row["ended"], "response": row["output"], "words": len(row["output"].split())}
            for alias, row in blind(rows).items()}


def assess(row, review, rubric):
    assert review.keys() == rubric.keys()
    met, uncertain = set(), set()
    for criterion, (label, evidence) in review.items():
        accepted = ("fail", "uncertain", "clean") if criterion == "G" else ("met", "unmet", "uncertain")
        assert label in accepted and isinstance(evidence, list)
        assert all(span and span in row["output"] for span in evidence)
        assert evidence or label in ("clean", "unmet", "uncertain")
        if label == "met":
            met.add(criterion)
        if label == "uncertain" and criterion != "G":
            uncertain.add(criterion)
    words = len(row["output"].split())
    guard = review["G"][0]
    released = row["ended"] and words <= 210 and guard == "clean"
    return {"met": sorted(met), "uncertain": sorted(uncertain), "coverage_lower": 7 * len(met),
            "coverage_upper": 7 * len(met | uncertain), "words": words, "guard": guard,
            "ended": row["ended"], "released": released, "release_points": 7 * len(met) if released else 0}


def score(rows):
    review = previous.load(EVIDENCE / "review.json")
    rubric = previous.load(previous.RUBRIC)
    original = {r["alias"]: r for r in previous.load(study.base.EVIDENCE / "results.json").values()}
    aliases = blind(rows)
    assert aliases.keys() == review.keys()
    results = {}
    for alias, row in aliases.items():
        group, variant = row["id"].split("/")
        starting = original[group]
        base_met = {c for c, (label, _) in starting["criteria"].items() if label == "met"}
        result = assess(row, review[alias], rubric)
        current_met = set(result["met"])
        results.setdefault(group, {})[variant] = {"alias": alias, **result,
            "retained": sorted(base_met & current_met), "gained": sorted(current_met - base_met),
            "lost": sorted(base_met - current_met),
            "release_delta": result["release_points"] - starting["release_points"],
            "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
    reference = {"output": (EVIDENCE / "feasibility-reference.txt").read_text(), "ended": True}
    ceiling = assess(reference, previous.load(EVIDENCE / "feasibility-review.json"), rubric)
    assert ceiling["release_points"] == 70
    return {"revisions": results, "authored_feasibility": ceiling}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("blind", "score"))
    p.add_argument("directory", type=Path)
    args = p.parse_args()
    rows = study.verify(args.directory)
    print(json.dumps(candidates(rows) if args.mode == "blind" else score(rows), ensure_ascii=False, indent=2))
