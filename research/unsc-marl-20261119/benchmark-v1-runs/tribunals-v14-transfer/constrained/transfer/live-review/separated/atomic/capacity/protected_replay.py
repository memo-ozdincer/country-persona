"""Retrospectively keep the validated role factorization and abstain on UK disagreements."""
import json
from hashlib import sha256
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def run():
    source = HERE / "results.json"
    evidence = json.loads(source.read_text())
    choices = {}
    ratings = {}
    for case, groups in evidence["predicates"].items():
        selected = {}
        for unit, values in groups.items():
            compound, factored = (values[key] for key in ("compound_mean", "factored_mean"))
            selected[unit] = factored if unit == "role" or compound == factored else "uncertain"
        choices[case] = selected
    for case, key in (("archived-pair", "myanmar/pair"), ("archived-full", "myanmar/control")):
        factored = evidence["records"]["factored_mean"][key]
        ratings[key] = {
            "accepted": "uncertain" not in choices[case].values() and factored["accepted"],
            "covered_readout": choices[case], "released_grade_if_admitted": None,
        }
        if ratings[key]["accepted"]:
            assert all(factored["units"][unit] == label for unit, label in choices[case].items())
            ratings[key]["released_grade_if_admitted"] = factored["score"]
    rows = []
    for row in evidence["rows"]:
        case = row["case"]
        grade = None
        selected = row["selected"]
        if case == "myanmar" and ratings["myanmar/pair"]["accepted"]:
            grade = ratings["myanmar/pair"]["released_grade_if_admitted"]
            cand = row["capacity"]["factored_mean"]
            assert cand["grade"] == grade
            selected = cand["metrics"]
        rows.append({key: row[key] for key in ("case", "law", "prior_information", "offset")} |
                    {"baseline": row["original"], "selected": selected, "myanmar_review_grade": grade})
    gains = [r["selected"]["net"] - r["baseline"]["net"] for r in rows]
    return {"scope": "Post hoc policy using factored role and agreement between UK readings.",
            "ratings": ratings, "controls": choices,
            "summary": {"rows": len(rows), "below_informed_silence": sum(
                        row["selected"]["over_informed_silence_quality"] < -1e-7 for row in rows),
                        "net_mean_over_original": mean(gains), "net_improved": sum(v > 1e-7 for v in gains),
                        "net_decreased": sum(v < -1e-7 for v in gains)},
            "rows": rows, "input_sha256": sha256(source.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
