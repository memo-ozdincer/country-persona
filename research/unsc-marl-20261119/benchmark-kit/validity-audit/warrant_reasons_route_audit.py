"""Audit which routing differences the language contrasts represent."""
import argparse
import json
from itertools import product
from pathlib import Path

import numpy as np

import warrant_reasons as study


def run():
    prior_report = json.loads(study.GENERAL.read_text())
    panels = {row["index"]: row for row in prior_report["panels"]}
    weights = json.loads(study.base.FIT.read_text())
    out = {}
    for k in prior_report["comparisons"]:
        if abs(k["delta"]) < 1e-10:
            continue
        panel = panels[k["panel"]]
        prior = study.base.fit.prior(k["prior"] == "correlated")
        policies = {name: study.policy(panel["domain"], k["prior"] == "correlated", np.asarray(weights[key]))
                    for name, key in (("initial", "initial"), ("fitted", "fit"))}
        only = dict.fromkeys(policies, 0.)
        different_label = 0.
        certified = dict.fromkeys(policies, 0.)
        for a, b, *links in product(range(4), range(4), *((True, False),) * 4):
            p = prior[a, b] * .9 ** sum(links) * .1 ** (4 - sum(links))
            available = {key: study.delivered(panel["domain"], rule, (a, b), links)[1]["permitted_decisions"]
                         for key, rule in policies.items()}
            initial = available["initial"] != ["UNRESOLVED"]
            fitted = available["fitted"] != ["UNRESOLVED"]
            if initial and not fitted:
                only["initial"] += p
            if fitted and not initial:
                only["fitted"] += p
            if available["initial"] != available["fitted"]:
                different_label += p
            certified["initial"] += p * initial
            certified["fitted"] += p * fitted
        for key, archived in (("initial", "initial"), ("fitted", "fit")):
            metrics = panel["records"][k["prior"]]["arms"][archived]
            assert abs(metrics["recommend"] + metrics["impasse"] - certified[key]) < 1e-12
        out[f"domain{k['panel']}-{k['prior']}"] = {"fitted_net_change": k["delta"],
                                                  "decision_differs_mass": different_label,
                                                  "only_one_policy_can_certify": only,
                                                  "total_certified_mass": certified}
    inputs = list(study.requests())
    unique = len({json.dumps(item["messages"], sort_keys=True) for item in inputs})
    return {"conditions": out, "generation_rows": len(inputs), "distinct_prompts": unique}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(run(), indent=2))
