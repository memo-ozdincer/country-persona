"""Replay two descriptive scoring sensitivities without changing the primary marks."""
import json
from score import HERE, TEAM, evaluate, read


def run():
    grades = read(HERE / "results.json")["live_grades"]
    team = read(TEAM / "results.json")
    raw_bank = {
        k: row | {"released_70": row["raw_70"][0],
                  "released_relationship": 22 if "consultation-not-consent" in row["met"] else 0}
        for k, row in grades.items()
    }
    # Every draft got the adoption and abstainers right. Award the full
    # disposition item for this sensitivity, while keeping the source guard.
    lenient_vote_bank = {
        k: row | {"released_70": row["released_70"] + (0 if row["blockers"] else 20)}
        for k, row in grades.items()
    }
    return {name: evaluate(bank, team)["summary"] for name, bank in (
        ("ignore_guard_for_raw_coverage", raw_bank), ("lenient_vote_keep_guard", lenient_vote_bank)
    )}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
