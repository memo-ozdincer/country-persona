"""Price strict note admission before the chair consumes a receipt."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_climate_language_channel as language

transfer, read, digest = language.transfer, language.read, language.digest
route = transfer.route
WORD_LIMIT = 55


def evaluate(path):
    reviewed = read(path)
    eligible = 0
    report = reviewed["notes"]
    for i, source in enumerate(transfer.task()["optional_sources"]):
        item = report[f"note-{source['id']}"]
        if item["ended"] and item["words"] <= WORD_LIMIT:
            eligible |= 1 << i
    score = reviewed["arms"]["visible"]
    priors, _, _ = transfer.original.selections()
    plans = read(language.PLAN)["plans"]
    case = {}
    for tag in ("raw", "release"):
        values = np.asarray(score[tag])[route.STATES & eligible]
        rows = {}
        for name, prior in priors.items():
            nets = {group: sum(weight * route.evaluate(transfer.base.space.as_policy(p), prior.T if swap else prior,
                                                       values, route.TRAIN_LOSS)["net"]
                               for p, swap, weight in plan) for group, plan in plans.items()}
            rows[name] = {"nets": nets, "gains_vs_scripted": nets["learned"] - nets["scripted"],
                          "gains_vs_independent": nets["learned"] - nets["independent"]}
        case[tag] = {"score_vector": values.tolist(), "priors": rows}
    return {"scope": "Strict 55-word admission of generated notes. Charge every attempted send. Project each "
                     "receipt to its budget-compliant subset and use the actual archived chair response for "
                     "that subset. This supplies the counterfactual for dropping over-budget evidence.",
            "score_sha256": digest(path), "eligible_mask": eligible, "results": case}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scores", type=Path)
    print(json.dumps(evaluate(cli.parse_args().scores), indent=2))
