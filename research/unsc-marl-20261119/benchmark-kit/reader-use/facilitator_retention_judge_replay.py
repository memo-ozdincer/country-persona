"""Replay automated selection, separate apparent credit from independently reviewed outcomes."""
import argparse
from hashlib import sha256
import json
from unittest.mock import patch

import numpy as np

import facilitator_retention_judge as study

pairs, fit = study.pairs, study.pairs.fit
D, trained = fit.D, pairs.trained


def keyed(card, record):
    return study.key(card, record["reply"], record["ended"])


def select(first, alternatives, judgments, mode):
    matrices = {k: np.zeros((4, 4), dtype=int) for k in ("apparent", "reviewed", "error", "material_error")}
    matrices["apparent"][:, 0] = matrices["reviewed"][:, 0] = 1
    comparisons, trace = {}, {}
    for q, context in enumerate(alternatives):
        for c in range(1, 4):
            labels = [(keyed(c, record), record) for record in (first[c], context[c])]
            for alias, record in labels:
                test = judgments[alias]
                verdict = test[mode + "_pass"]
                assert alias not in comparisons or comparisons[alias]["reviewed"] == record["passed"]
                comparisons[alias] = {"automatic": verdict, "reviewed": record["passed"], "valid_format": test["format"],
                                      "candidate": record["reply"], "card": c,
                                      "material_errors": record["assessment"]["errors"]}
            chosen = next(((alias, record) for alias, record in labels if judgments[alias][mode + "_pass"]), None)
            if chosen:
                alias, record = chosen
                matrices["apparent"][q, c] = 1
                matrices["reviewed"][q, c] = int(record["passed"])
                matrices["error"][q, c] = int(not record["passed"])
                matrices["material_error"][q, c] = int(bool(record["assessment"]["errors"]))
            trace[f"{q}/{c}"] = {"chosen": chosen[0] if chosen else None,
                                 "oracle_can_select": any(record["passed"] for _, record in labels),
                                 "safe_selection": bool(matrices["reviewed"][q, c]),
                                 "invalid_selection": bool(matrices["error"][q, c]),
                                 "material_error_selection": bool(matrices["material_error"][q, c])}
    return matrices, comparisons, trace


def impact(policy, points, prior, matrices, first, alternatives, judgments):
    _, opening = fit.context(points, prior)
    q, r = policy
    mass = np.einsum("rbm,mt,rbtc->tc", opening, fit.heard(D.one_hot(q)), D.one_hot(r))
    counts_by_candidate = {k: 1 + int("challenge" in row) for k, row in judgments.items()}
    calls = np.array([[0, *(counts_by_candidate[keyed(c, first[c])] +
                           counts_by_candidate[keyed(c, second[c])] for c in range(1, 4))]
                      for second in alternatives])
    review_cost = {}
    for metric in ("input_tokens", "output_tokens"):
        counts = np.array([[0, *(judgments[keyed(c, first[c])][metric] +
                                  judgments[keyed(c, second[c])][metric] for c in range(1, 4))]
                           for second in alternatives])
        review_cost["expected_judge_" + metric] = float((mass * counts).sum())
    return {"invalid_delivered_probability": float((1 - D.LOSS) * (mass * matrices["error"]).sum()),
            "material_error_delivered_probability": float((1 - D.LOSS) * (mass * matrices["material_error"]).sum()),
            "expected_judge_calls_without_caching": float((mass * calls).sum()), **review_cost}


def replay(points, first, alternatives, judgments, weights, mode):
    matrices, reviews, trace = select(first, alternatives, judgments, mode)
    with patch.object(trained.rubric, "ceilings", lambda _: points):
        scored = trained.evaluate(weights, matrices["reviewed"])["policies"]
    oracle = pairs.replay(points, first, alternatives, weights)["comparison"]["retain"]["policies"]
    policies = {}
    for label in fit.live.PRIORS:
        prior = fit.ROUTE.TEST_PRIORS[label]
        rows = {}
        for name in ("ideal_fit", "measured_fit", "measured_independent", "exact_held_independent"):
            row = scored[label][name]
            tail = tuple(map(np.asarray, row["policy"]))
            left, opening = fit.context(np.asarray(points), prior)
            apparent = fit.measure(tail, left, opening, prior, np.asarray(points), matrices["apparent"])
            metrics = impact(tail, np.asarray(points), prior, matrices, first, alternatives, judgments)
            rows[name] = {"reviewed_net": row["net"], "apparent_net": apparent["net"],
                          "oracle_gate_net": oracle[label][name]["net"],
                          "reviewed_net_gain_over_hindsight_no_request": row["net"] - scored[label]["exact_held_independent"]["net"],
                          **metrics}
            assert apparent["net"] >= row["net"] - 1e-10
            assert oracle[label][name]["net"] >= row["net"] - 1e-10
        policies[label] = rows
    count = {f"{int(a)}{int(b)}": sum(r["reviewed"] == a and r["automatic"] == b for r in reviews.values())
             for a in (False, True) for b in (False, True)}
    return {"confusion_reviewed_then_automatic": count, "candidate_decisions": reviews,
            "selected_contexts": trace, "matrices": {k: v.tolist() for k, v in matrices.items()},
            "policies": policies}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    raw = study.EVIDENCE / "judgments.json"
    archive = study.HERE / "facilitator-measured-channel-evidence/fits.json"
    output = {}
    for name, points, first, alternatives in pairs.contexts():
        if name.startswith("2504_"):
            mode = name.removeprefix("2504_")
            output[mode] = replay(points, first, alternatives, trained.read(raw), trained.read(archive), mode)
    print(json.dumps({"results": output, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (raw, archive)}},
                     ensure_ascii=False, indent=2))
