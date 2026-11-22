"""Audit the impasse proof gap before routing and the scope of two clause checks."""
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def evaluate():
    result = json.loads((HERE / "evidence/metrics.json").read_text())
    case = json.loads((HERE / "case.json").read_text())
    options = case["options"]
    letters = {opt["id"] for opt in options}
    known = {
        letter for letter in letters
        if any(result["decisions"][f"{role}/{letter}"]["sign"] is False and
               result["decisions"][f"{role}/{letter}"]["expected"] is False
               for role in ("japan", "china-impasse"))
    }
    missing = letters - known
    clause_checks = {
        "japan/no-broad-first-stage": {opt["id"] for opt in options if opt["scope"] == "broad"},
        "china-impasse/require-broad-first-stage": {opt["id"] for opt in options if opt["scope"] != "broad"},
    }
    for clause, covered in clause_checks.items():
        role = clause.split("/")[0]
        assert all(not result["decisions"][f"{role}/{letter}"]["expected"] for letter in covered)
    added = set().union(*clause_checks.values())
    assert known == {"A", "B"}
    assert missing <= added and all(missing - cover for cover in clause_checks.values())
    return {"initial_truthful_exclusions": sorted(known),
            "minimum_single_package_returns": len(missing),
            "uncovered_packages": sorted(missing),
            "authored_clause_checks": {k: sorted(v) for k, v in clause_checks.items()},
            "clauses_cover_all_missing_exclusions": missing <= added,
            "scope": "Evidence availability only. Publication, turns, and model clause verification are unmeasured."}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
