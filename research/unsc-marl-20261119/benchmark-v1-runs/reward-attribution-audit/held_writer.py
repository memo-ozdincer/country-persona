"""Compare directional reward labels with one writer omitted."""
from itertools import product
import json

from audit import HERE, across, read, sha


def sign(n):
    return (n > 0) - (n < 0)


def evaluate(rows):
    writer_list = tuple(rows[0]["writers"])
    all_cases = []
    for row, held in product(rows, writer_list):
        known = {name: value for name, value in row["writers"].items() if name != held}
        selected = across(known)["direction"]
        robust = {"prefer_add_or_replace": 1, "prefer_original": -1}.get(selected, 0)
        entry = row["writers"][held]
        all_cases.append({"before": row["before"], "after": row["after"], "held": held,
                          "held_delta": entry, "consensus_prediction": robust,
                          "individual_predictions": {name: sign(value["nominal"])
                                                     for name, value in known.items()}})

    def score(predictions):
        counts = {"opportunities": 0, "issued": 0, "wrong_sign": 0, "nominal_zero": 0,
                  "direction_guaranteed": 0}
        for predicted, held in predictions:
            counts["opportunities"] += 1
            if predicted == 0:
                continue
            counts["issued"] += 1
            counts["wrong_sign"] += predicted * held["nominal"] < 0
            counts["nominal_zero"] += held["nominal"] == 0
            lo, hi = held["band"]
            counts["direction_guaranteed"] += lo > 0 if predicted > 0 else hi < 0
        return counts

    return {
        "per_edge_writer": all_cases,
        "remaining_writers_agree": score((row["consensus_prediction"], row["held_delta"]) for row in all_cases),
        "single_writer_ordered_pairs": score((pred, row["held_delta"]) for row in all_cases
                                             for pred in row["individual_predictions"].values()),
    }


def run():
    prior = HERE / "results.json"
    audit = read(prior)
    panels = {"2475": audit["2475_marginal_delivery"],
              **{f"2686_{key}": rows for key, rows in audit["2686_marginal_delivery"].items()}}
    return {"audit_sha256": sha(prior), "panels": {k: evaluate(board["rows"]) for k, board in panels.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
