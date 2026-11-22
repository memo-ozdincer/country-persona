"""Attribute transfer loss to send value or reply selection."""
import json
from itertools import product

import numpy as np

import fit_transfer as study


def run():
    result = study.read(study.HERE/"results.json")
    draft = study.read(study.HERE/"fit.json")
    actual = np.array(result["reference"])
    tags = np.arange(1, 4)
    details = {}
    for group, rows in draft["routes"].items():
        outputs = []
        for row in rows:
            q0, q1, price, views = row["setting"]
            setting = q0, q1, price, np.array(views)
            sender, reply = (np.array(x) for x in row["routes"]["donor_fit_256/peer"])
            _, ideal_reply = study.prior.best_route(actual, tags, setting)

            def evaluate(s, r):
                return float(study.prior.pay(actual, tags, setting, np.asarray(s), r)[0])

            all_senders = list(product((0, 1), repeat=3))
            optimal_given_reply = max(evaluate(s, reply) for s in all_senders)
            optimal_reply_given_sender = max(evaluate(sender, np.array(r))
                                             for r in product((0, 1), repeat=4))
            scores = {
                "fitted": evaluate(sender, reply),
                "best_sender_with_fitted_reply": optimal_given_reply,
                "best_reply_with_fitted_sender": optimal_reply_given_sender,
                "oracle_reply_with_fitted_sender": evaluate(sender, ideal_reply),
            }
            outputs.append({"setting": row["setting"], "utility": scores})
        means = {key: round(float(np.mean([row["utility"][key] for row in outputs])), 8)
                 for key in outputs[0]["utility"]}
        assert means["fitted"] == result["evaluation"][group]["summary"]["donor_fit_256/peer"]["utility"]
        details[group] = {"means": means, "rows": outputs}
    return details


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
