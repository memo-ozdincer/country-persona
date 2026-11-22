"""Stress frozen policies when predicted joint source credit is wrong."""
from itertools import product
import json
from statistics import mean

import study as model


SCALES = (0., .5, 1., 1.5, 2.)


def intervene(scores, scale):
    additive = [scores[0]+sum(scores[1 << i]-scores[0] for i in range(3) if mask & (1 << i))
                for mask in model.MASKS]
    return [base+scale*(value-base) for value,base in zip(scores,additive,strict=True)]


def run():
    archived_path = model.HERE/"results.json"
    saved = model.read(archived_path)
    banks = model.banks()
    outcomes = {}
    for name, other in (("2475","2686"),("2686","2475")):
        weights = saved["training"][other]["120"]["weights"]
        exact_rows = saved["held"][name]["rows"]
        effects = {}
        for scale in SCALES:
            actual, announced = banks[name], intervene(banks[name],scale)
            contexts = [model.scene(announced,order,rate,fee)
                        for order,rate,fee in product(model.ORDERS,model.RATES,model.FEES)]
            inputs = [(actual, *context[1:]) for context in contexts]
            result = model.evaluate(inputs,weights,False)
            for row, original in zip(result["rows"],exact_rows,strict=True):
                for reference in ("standalone","adaptive_ceiling","static_ceiling"):
                    assert row["net"][reference] == original["net"][reference]
                if scale == 1:
                    assert row == original
            effects[str(scale)] = {
                "mean":result["mean"],
                "fit_wins_vs_forecast":sum(r["net"]["fit"] > r["net"]["future_forecast"]+model.TOL
                                            for r in result["rows"]),
                "forecast_wins_vs_fit":sum(r["net"]["future_forecast"] > r["net"]["fit"]+model.TOL
                                            for r in result["rows"]),
            }
        gains = [row["net"]["adaptive_ceiling"]-row["net"]["static_ceiling"] for row in exact_rows]
        outcomes[name] = {
            "shift":effects,
            "mean_receipt_information_value":mean(gains),
            "maximum_receipt_information_value":max(gains),
            "strict_values":sum(g > model.TOL for g in gains),
        }
    return {"baseline_results_sha256":model.pin(archived_path),"banks":outcomes}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
