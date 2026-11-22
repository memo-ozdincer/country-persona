"""Audit a bounded-disagreement gate on the archived replay."""
import json
from hashlib import sha256
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
RADIUS = 7


def run():
    archive = HERE / "results.json"
    data = json.loads(archive.read_text())
    cases = data["grades"]["archived_grades"]
    report = {}
    for arm in ("numeric", "quoted"):
        observed = []
        for row in data["rows"]:
            initial = min(70, max(0, cases[row["case"]] + row["offset"]))
            second = row["observed_model_grades"][arm]
            admissible = second is not None and abs(second - initial) <= RADIUS
            selected = row[arm] if admissible else row["original"]
            observed.append({"case": row["case"], "law": row["law"],
                             "prior_information": row["prior_information"], "offset": row["offset"],
                             "original_grade": initial, "proposed_grade": second, "accepted": admissible,
                             "net_change": selected["net"] - row["original"]["net"],
                             "over_informed_silence_quality": selected["over_informed_silence_quality"]})
        report[arm] = {"review_grades_proposed": sum(r["proposed_grade"] is not None for r in observed),
                       "accepted_under_gate": sum(r["accepted"] for r in observed),
                       "mean_net_change": mean(r["net_change"] for r in observed),
                       "below_informed_silence": sum(r["over_informed_silence_quality"] < -1e-7 for r in observed),
                       "rows": observed}
    return {"scope": "Post hoc use of the original scenario's seven-point error envelope. No new calls.",
            "radius": RADIUS, "arms": report, "replay_sha256": sha256(archive.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
