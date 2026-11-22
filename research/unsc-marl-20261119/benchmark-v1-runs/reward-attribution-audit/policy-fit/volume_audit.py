"""Test a common send-threshold shift matched on the training docket's volume."""
import json
from pathlib import Path

import fit

HERE = Path(__file__).resolve().parent


def count(scenes, weights):
    return sum(p > .5 for scene in scenes for p in fit.policy(scene, weights))


def calibration(scenes, target):
    # Greedy volume can change only at a standalone expected-return threshold.
    margins = sorted({(scene[0]*value-scene[1])/7 for scene in scenes for value in scene[2]})
    options = [0., margins[0]-1., margins[-1]+1.,
               *((left+right)/2 for left,right in zip(margins, margins[1:]))]
    distance, _, shift, matched = min(
        (abs(total-target), abs(shift), shift, total)
        for shift in options for total in (count(scenes, [-shift, 0., 0.]),))
    return {"training_target": target, "training_threshold_sends": matched,
            "send_count_discrepancy": distance, "threshold_increase_points": 7*shift,
            "weights": [-shift,0.,0.]}


def run():
    result_path = HERE / "results.json"
    saved = fit.audit.read(result_path)
    cases = fit.load()
    output = {}
    for key, row in saved["folds"].items():
        trained, tested = key.split("_to_")
        arm = {name: trace["120"]["weights"] for name,trace in row["train"].items()}
        arm["fixed"] = [0.]*3
        training = list(fit.scenes(cases[trained]))
        adjusted = calibration(training, count(training, arm["agreement"]))
        arm["matched_volume"] = adjusted["weights"]
        checked = fit.evaluate(cases[tested], arm)
        for older, newer in zip(row["held"]["rows"], checked["rows"], strict=True):
            assert all(newer["sends"][k] == v for k,v in older["sends"].items())
            for writer, values in older["net"].items():
                assert all(newer["net"][writer][k] == v for k,v in values.items())
        output[key] = {"calibration": adjusted,
                       "held_sends": {name: sum(sum(r["sends"][name]) for r in checked["rows"])
                                      for name in arm}, "held": checked}
    return {"parent_result_sha256": fit.audit.sha(result_path), "folds": output}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
