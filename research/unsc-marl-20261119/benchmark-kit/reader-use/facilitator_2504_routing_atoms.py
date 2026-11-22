"""Audit the effect of crediting partial source-grounded facts in the last reply."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_2504_routing_replay as study

fit, D, trained = study.fit, study.D, study.trained
NEEDED = {"P": {(1, 0), (1, 1), (1, 2)}, "B": {(2, 0), (2, 1), (2, 2)}, "R": {(3, 0), (3, 1), (3, 2)},
          "PR": {(1, 0), (1, 1), (1, 2), (3, 2)}, "BR": {(2, 0), (3, 0), (3, 1)}}


def atom_values(admissions):
    packet = study.study.case.packet()
    weights = {c["id"]: c["points"] for c in packet["criteria"]}
    def points(atoms):
        return packet["public_points"] + sum(w for k, w in weights.items() if NEEDED[k] <= atoms)

    openings = [{(c, i) for c in range(1, 4) if mask & (1 << (c - 1)) for i in range(3)} for mask in range(8)]
    scores = np.full((8, 4, 4), 42.)
    base = np.asarray([points(a) for a in openings])
    assert base.tolist() == [42, 46, 48, 52, 50, 59, 61, 70]
    for m, present in enumerate(openings):
        scores[m, :, 0] = base[m]
        for name, row in admissions["replies"].items():
            q, c = map(int, name.split("/"))
            mark = row["assessment"]
            usable = row["ended"] and row["words"] <= 52 and not mark["errors"]
            obtained = {(c, i) for i, spans in enumerate(mark["required"]) if usable and spans}
            scores[m, q, c] = points(present | obtained)
    encoded = fit.OLD.base.terminal(base)
    utility = ((1 - D.LOSS) * (scores + D.COMPLETE_BONUS * (scores == 70)) +
               D.LOSS * encoded[:, None, None] - D.SEND_COST)
    return base, scores, utility


def run(admissions, eval_result):
    points, scores, utility = atom_values(admissions)
    result = {}
    for name, rows in eval_result["new_label_to_original_by_key"]["123"]["policies"].items():
        prior = fit.ROUTE.TEST_PRIORS[name]
        opener, opening = fit.context(points, prior)
        fees = prior.sum(1) @ D.SEND_COST[opener[0]] + prior.sum(0) @ D.SEND_COST[opener[1]]
        selected = ("ideal_fit", "measured_fit", "measured_independent", "ideal_exact")
        policies = {k: tuple(map(np.asarray, rows[k]["policy"])) for k in selected}
        with patch.object(fit, "value", lambda _points, _table: utility):
            for mode in ("joint", "independent"):
                policies[f"actual_atom_{mode}"] = fit.exact(points, opening, None, independent=(mode == "independent"))
        evaluated = {}
        for label, (q, r) in policies.items():
            outcome = np.einsum("rbm,mt,rbtc->mtc", opening, fit.heard(D.one_hot(q)), D.one_hot(r))
            net = np.sum(outcome * utility) - fees - opening.sum((0, 1)) @ D.QUERY_COST[q]
            evaluated[label] = {"net": float(net), "request_rate": float(opening.sum((0, 1)) @ (q != 0))}
            if label in selected:
                gate_only = fit.value(points, np.asarray(admissions["matrix"]))
                previous = (outcome * gate_only).sum() - fees - opening.sum((0, 1)) @ D.QUERY_COST[q]
                assert abs(previous - rows[label]["net"]) < 1e-10
                assert net >= previous - 1e-10
                evaluated[label]["whole_card_net"] = float(previous)
        result[name] = evaluated
    return {"last_reply_points_by_opening_question_card": scores.tolist(), "original_label_policies": result}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    directory = study.study.EVIDENCE
    output = run(*(trained.read(directory / (key + ".json")) for key in ("admission", "replay")))
    print(json.dumps(output, indent=2))
