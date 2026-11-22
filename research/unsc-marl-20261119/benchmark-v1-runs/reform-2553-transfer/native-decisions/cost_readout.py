"""Translate the observed receipt gains into break-even forwarding costs."""
import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def run():
    report = json.loads((HERE / "scores.json").read_text())
    rows = []
    for context in report["scenarios"]:
        content = context["results"]["content"]
        arrival = context["results"]["arrival"]
        rate = context["receipt"]
        scores = {}
        for arm in ("mean", "consensus", "prior_fixed", "prior_oracle"):
            difference = content[arm]["released"] - arrival[arm]["released"]
            # Forwarding is attempted exactly once conditional on a successful early receipt.
            maximum = difference / rate
            scores[arm] = {"release_gain_over_arrival": difference,
                           "break_even_extra_cost_per_attempt": maximum}
        independent = content["mean"]["third"]
        assert all(context["results"][mode]["mean"]["third"] == independent for mode in ("arrival", "none"))
        rows.append({"order": context["order"], "receipt_rate": rate, "arms": scores})
    return {"scenarios": rows, "average_release_gains": {
                arm: mean(row["arms"][arm]["release_gain_over_arrival"] for row in rows)
                for arm in rows[0]["arms"]},
            "assumption": "Treat extra forwarding cost as incurred on each early arrival; all other costs match."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
