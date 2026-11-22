"""Decompose net transfer against silence by opening state and reply result."""
import argparse
import json

import numpy as np

import facilitator_2504_routing_replay as study

fit, D = study.fit, study.D


def contribution(policy, opening, payoff):
    q, r = map(np.asarray, policy)
    path = np.einsum("rbm,mt,rbtc->mtrc", opening, fit.heard(D.one_hot(q)), D.one_hot(r))
    subtotal = (path * payoff[:, :, None, :]).sum((1, 2, 3)) - opening.sum((0, 1)) * D.QUERY_COST[q]
    return subtotal, path.sum(2)


def run(whole):
    scores = np.asarray(whole["authored_points"])
    actual = np.asarray(whole["held_admission"])
    payoff = fit.value(scores, actual)
    result = {}
    for label, cases in whole["policies"].items():
        prior = fit.ROUTE.TEST_PRIORS[label]
        _, opening = fit.context(scores, prior)
        baseline, _ = contribution(cases["exact_held_independent"]["policy"], opening, payoff)
        learned, path = contribution(cases["ideal_fit"]["policy"], opening, payoff)
        q = cases["ideal_fit"]["policy"][0]
        differences = learned - baseline
        assert abs(differences.sum() - cases["ideal_fit"]["gain_over_hindsight_no_request"]) < 1e-10
        result[label] = [{"opening": i, "mass": float(opening[:, :, i].sum()), "request": q[i],
                          "net_gain": float(differences[i]), "query_reply_mass": path[i].tolist()} for i in range(8)]
    return result


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    files = study.study.EVIDENCE
    strict = study.trained.read(files / "replay.json")
    chronology = study.trained.read(files / "chronology.json")["whole_replay"]
    output = {"strict": run(strict["new_label_to_original_by_key"]["123"]),
              "chronology": run(chronology["new_label_to_original_by_key"]["123"])}
    print(json.dumps(output, indent=2))
