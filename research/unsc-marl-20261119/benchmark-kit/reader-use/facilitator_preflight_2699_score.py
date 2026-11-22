"""Score preflight selection and matched held-docket communication interfaces."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_preflight_2699 as study

source = study.source
fit = study.fit


def reply_flow(policy, prior, decoded):
    left, right, ask, reply = policy
    opening = np.einsum("lr,la,rb,abm->rbm", prior, fit.D.one_hot(left), fit.D.one_hot(right), fit.D.FIRST)
    physical = fit.heard(fit.D.one_hot(ask))
    return np.einsum("rbm,mt,rbtc->tc", opening, physical, fit.D.one_hot(reply[:, :, decoded]))


def evaluate(rows, review):
    preflight = study.preflight(rows)
    with patch.object(source, "packet", study.packet):
        original = source.score(rows, review)
        admissions = np.zeros((4, 4), dtype=bool)
        for label in original["approved_reply_ids"]:
            _, q, c = label.split("/")
            admissions[int(q), int(c)] = True
        isolated = np.broadcast_to(admissions[0], (4, 4))
        results = {}
        for family in source.PRIORS:
            prior = source.ROUTE.TEST_PRIORS[family]
            policies = source.policies(prior)
            score = {name: {"visible": original["priors"][family][name]["english"],
                            "source_only": source.distribution(policy, prior, original["decoded"], isolated),
                            "typed": original["priors"][family][name]["typed"]}
                     for name, policy in policies.items()}
            mode = preflight["selected"]
            selected = score["independent"]["source_only"] if mode == "independent_source_only" else score["fitted"][mode]
            flows = reply_flow(policies["fitted"], prior, original["decoded"])
            for interface, table in (("visible", admissions), ("source_only", isolated)):
                failed = np.sum((flows * ~table)[:, 1:])
                assert abs(failed - score["fitted"][interface]["failed_replies"]) < 1e-12
            results[family] = {"all_arms": score, "preflight_selected": selected,
                               "fitted_reply_attempts_by_physical_question_and_payload": flows.tolist(),
                               "net_delta_over_visible_fit": selected["net"] - score["fitted"]["visible"]["net"],
                               "net_delta_over_isolated_independent": selected["net"] - score["independent"]["source_only"]["net"]}
    return {"preflight": preflight, "decoded": original["decoded"], "admitted_replies": original["approved_reply_ids"],
            "rendered_record_bank": original["records"], "points_by_record": original["record_points"], "priors": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    review = json.loads((study.EVIDENCE / "review.json").read_text())
    print(json.dumps(evaluate(study.verify(args.directory), review), ensure_ascii=False, indent=2))
