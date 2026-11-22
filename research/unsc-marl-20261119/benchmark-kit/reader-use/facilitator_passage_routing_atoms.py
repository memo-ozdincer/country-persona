"""Score partial machine-certified fields with the existing documentary criterion graphs."""
import argparse
import json
from unittest.mock import patch

import numpy as np

import facilitator_2504_routing_atoms as syria
import facilitator_measured_channel_partial as africa
import facilitator_passage_routing_replay as study

fit, D, trained = study.fit, study.D, study.trained
GRAPHS = {"2504": syria.NEEDED, "2719": africa.REQUIRES}


def tensor(docket, document, points):
    p, _ = study.study.sources()[docket]
    weights = {r["id"]: r["points"] for r in p["criteria"]}
    graph = GRAPHS[docket]
    existing = [{(c, i) for c in range(1, 4) if mask & (1 << (c - 1)) for i in range(3)} for mask in range(8)]
    def score(atoms):
        return 42 + sum(weights[k] for k, required in graph.items() if required <= atoms)
    assert [score(a) for a in existing] == points.tolist()
    scores = np.zeros((8, 4, 4), dtype=int)
    scores[:, :, 0] = points[:, None]
    for q in range(4):
        for c in range(1, 4):
            row = document["records"][f"{docket}/{q}/{c}"]
            facts = {(c, int(field) - 1) for field in row["evidence_emitted"]}
            assert bool(row["delivery"]) == (len(facts) == 3)
            scores[:, q, c] = [score(previous | facts) for previous in existing]
    return scores


def run(document, weights):
    result = {}
    for docket in document["matrices"]:
        packet, _ = study.study.sources()[docket]
        points = np.asarray(trained.rubric.ceilings(packet["criteria"]))
        scores = tensor(docket, document, points)
        utility = ((1 - D.LOSS) * (scores + D.COMPLETE_BONUS * (scores == 70)) +
                   D.LOSS * fit.OLD.base.terminal(points)[:, None, None] - D.SEND_COST)
        whole = fit.value(points, np.asarray(document["matrices"][docket]))
        assert (utility >= whole - 1e-10).all()
        out = {}
        for label in fit.live.PRIORS:
            prior = fit.ROUTE.TEST_PRIORS[label]
            opener, opening = fit.context(points, prior)
            open_fee = prior.sum(1) @ D.SEND_COST[opener[0]] + prior.sum(0) @ D.SEND_COST[opener[1]]
            with patch.object(fit, "value", lambda *_: utility):
                arms = {"exact_independent": fit.exact(points, opening, None, independent=True),
                        "exact_joint": fit.exact(points, opening, None)}
            for key, learned in weights["policies"].items():
                arms[key + "_fit"] = fit.action_policy(learned["weights"], points, opening, np.asarray(learned["feature_channel"]))
            measured = {}
            for name, (q, r) in arms.items():
                dist = np.einsum("rbm,mt,rbtc->mtc", opening, fit.heard(D.one_hot(q)), D.one_hot(r))
                fees = open_fee + opening.sum((0, 1)) @ D.QUERY_COST[q]
                measured[name] = {"net": float((dist * utility).sum() - fees),
                                  "same_policy_whole_card_net": float((dist * whole).sum() - fees)}
            out[label] = measured
        result[docket] = {"policies": out, "field_points_by_opening_question_card": scores.tolist()}
    return result


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    docs = trained.read(study.study.EVIDENCE / "admission.json")
    fitted = trained.read(study.study.HERE / "facilitator-measured-channel-evidence/fits.json")
    print(json.dumps(run(docs, fitted), ensure_ascii=False, indent=2))
