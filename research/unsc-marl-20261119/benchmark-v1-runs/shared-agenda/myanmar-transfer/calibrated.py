"""Transfer the observed fraction of a publicly declared rubric opportunity."""
import json
from math import isclose
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def run():
    data = read("replay.json")
    rates = {arm: coef / .2 for arm, coef in data["frozen_coefficients"].items()}
    opportunities = {"original": 0., "second-card-required": .1}
    reports = {}
    for group, evaluations in data["replays"].items():
        arm, contract = group.split("/")
        opportunity = opportunities[contract]
        forecast = opportunity * rates[arm]
        fees = {}
        for fee_str, values in evaluations.items():
            fee = float(fee_str)
            outputs = []
            for branch in values["rows"]:
                weight, p = branch["priority"], branch["link"]
                true_value = (branch["after_two"]-branch["after_one"])/70
                candidates = {"scaled-fit": forecast, "fixed-rubric": opportunity}
                row = {}
                for name, value in candidates.items():
                    send = p*weight*value > fee
                    realized = int(send) * (p*weight*true_value - fee)
                    reference = branch["policies"]["fixed-7" if opportunity else "wait"]
                    if name == "fixed-rubric":
                        assert send == reference["send"] and isclose(realized, reference["incremental_net"], abs_tol=1e-12)
                    assert realized <= branch["policies"]["oracle"]["incremental_net"] + 1e-10
                    row[name] = dict(send=send, net_gain=realized)
                outputs.append(row)
            summary = {name: {key: mean(r[name][key] for r in outputs) for key in row[name]} for name in row}
            fees[fee_str] = dict(summary=summary, outcomes=outputs)
        reports[group] = dict(available_points=70*opportunity, predicted_points=70*forecast, evaluations=fees)
    return dict(retention=rates, results=reports)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
