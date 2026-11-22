"""Post-hoc comparison of full-record and witness checks on matched outputs."""
import json

from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "judged-relation-reward"


def read(path):
    return json.loads(path.read_text())


def run():
    baseline = read(OLD / "results.json")["judgments"]
    anchored = read(HERE / "results.json")["cases"]
    rows = {}
    for key, old in baseline.items():
        new = anchored[key]
        assert old["met"] == new["met"] and old["weight"] == new["weight"]
        full = old["judgments"]["mean"]
        witness = new["judgments"]["mean"]
        rows[key] = {"met": old["met"], "weight": old["weight"], "mutation": old["mutation"],
                     "judgments": {"either": full or witness, "both": full and witness,
                                   "full": full, "witness": witness}}
    exact = {}
    for group in ("archived", "mutations"):
        active = [row for row in rows.values() if row["mutation"] == (group == "mutations")]
        exact[group] = {method: {
            "correct": sum(row["judgments"][method] == row["met"] for row in active),
            "false_accepted": sum(not row["met"] and row["judgments"][method] for row in active),
            "true_accepted": sum(row["met"] and row["judgments"][method] for row in active),
        } for method in ("either", "both", "full", "witness")}
    return exact


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
