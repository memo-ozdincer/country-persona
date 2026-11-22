"""Compare retaining the default candidate with replacing it after a question."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_measured_channel_fit as trained
import facilitator_retained_replies as study

fit, D = trained.fit, trained.D


def row(data, context):
    return [None, *(data["replies"][f"{context}/{c}"] for c in range(1, 4))]


def contexts():
    reader = trained.read
    wording_path = study.HERE / "facilitator-question-wording-evidence/admission.json"
    original = reader(study.HERE / "facilitator-measured-channel-evidence/admission.json")
    wording = reader(wording_path)
    point_2719 = trained.rubric.ceilings(trained.study.dossier.packet()["criteria"])
    variants = [[*row(original, q)] for q in range(4)]
    variants[0] = row(wording, 1)
    yield "2719_archived_questions", point_2719, row(wording, 0), deepcopy(variants)
    for c in range(1, 4):
        variants[c][c] = wording["replies"][f"2/{c}"]
    yield "2719_alternate_questions", point_2719, row(wording, 0), variants

    earliest = reader(study.prior.EVIDENCE / "admission.json")
    chronology = reader(study.prior.EVIDENCE / "chronology.json")["admission"]
    second = reader(study.EVIDENCE / "admission.json")
    chron_second = deepcopy(second)
    marks = reader(study.EVIDENCE / "chronology-review.json")
    assert marks.keys() == {"0/3"}
    for key, span in marks.items():
        candidate = chron_second["replies"][key]
        if span:
            assert span in candidate["reply"] and not candidate["assessment"]["required"][2]
            candidate["assessment"]["required"][2] = [span]
            candidate["passed"] = bool(candidate["ended"] and candidate["words"] <= 52
                                       and all(candidate["assessment"]["required"])
                                       and not candidate["assessment"]["errors"])
    point_2504 = reader(study.prior.case.EVIDENCE / "provenance.json")["authored_receipt_ceilings"]
    for label, first_run, second_run in (("strict", earliest, second), ("chronology", chronology, chron_second)):
        alternatives = [row(second_run, 0)] + [row(first_run, q) for q in range(1, 4)]
        yield "2504_" + label, point_2504, row(first_run, 0), alternatives


def metrics(policy, points, prior, first, second):
    _, opening = fit.context(points, prior)
    query, reply = map(np.asarray, policy)
    decisions = np.einsum("rbm,mt,rbtc->tc", opening, fit.heard(D.one_hot(query)), D.one_hot(reply))
    expected_calls = float(decisions[:, 1:].sum()) * 2
    a = np.array([False, *(x["passed"] for x in first[1:])])
    b = np.array([[False, *(r["passed"] for r in context[1:])] for context in second])
    result = {"expected_author_calls": expected_calls,
              "first_only_pass_probability": float((decisions * (a & ~b)).sum()),
              "second_only_pass_probability": float((decisions * (~a & b)).sum()),
              "topical_only_pass_probability": float((decisions[1:] * (~a & b[1:])).sum())}
    for token in ("input_tokens", "output_tokens"):
        tok = np.array([[0, *(first[i][token] + array[i][token] for i in range(1, 4))] for array in second])
        result["expected_author_" + token] = float((decisions * tok).sum())
    return result


def pair_selection(first, second):
    selected = {}
    for q, context in enumerate(second):
        for c in range(1, 4):
            a, b = first[c], context[c]
            choice = "first_generic" if a["passed"] else "second" if b["passed"] else "withheld"
            chosen = {"first_generic": a["reply"], "second": b["reply"], "withheld": None}[choice]
            selected[f"{q}/{c}"] = {"choice": choice, "selected_reply": chosen,
                                     "first_pass": a["passed"], "second_pass": b["passed"]}
    return selected


def replay(points, first, second, fitted):
    conditions = {}
    candidate_first = np.array([1, *(int(x["passed"]) for x in first[1:])])
    replacement = np.array([[1, *(int(row["passed"]) for row in context[1:])] for context in second])
    retained = np.maximum(candidate_first, replacement)
    assert (retained >= replacement).all()
    selected = pair_selection(first, second)
    for name, trial in selected.items():
        q, c = map(int, name.split("/"))
        assert bool(trial["selected_reply"]) == bool(retained[q, c])
    for name, matrix in (("replace", replacement), ("retain", retained)):
        with patch.object(trained.rubric, "ceilings", lambda _: points):
            model = trained.evaluate(fitted, matrix)
        for label, rows in model["policies"].items():
            prior = fit.ROUTE.TEST_PRIORS[label]
            reference = rows["exact_held_independent"]["net"]
            for policy, scores in rows.items():
                scores["gain_over_budget_matched_no_request"] = scores["net"] - reference
                scores.update(metrics(scores["policy"], np.array(points), prior, first, second))
                if name == "retain" and policy not in ("exact_held_joint", "exact_held_independent"):
                    old = conditions["replace"]["policies"][label][policy]
                    assert scores["policy"] == old["policy"] and scores["net"] >= old["net"] - 1e-10
                    assert scores["expected_author_calls"] == old["expected_author_calls"]
        conditions[name] = model
    for result in conditions.values():
        result.pop("one_cell_flip_advantage_over_fixed_measured_no_request")
        for same_prior in result["policies"].values():
            for details in same_prior.values():
                details["requests_by_opening"] = details.pop("policy")[0]
    return {"first_generic_pass": candidate_first.tolist(), "comparison": conditions,
            "selected_reply_by_context": selected}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    weights = study.HERE / "facilitator-measured-channel-evidence/fits.json"
    fitted = trained.read(weights)
    outcome = {"scenarios": {name: replay(points, first, second, fitted) for name, points, first, second in contexts()},
               "weights_sha256": sha256(weights.read_bytes()).hexdigest()}
    print(json.dumps(outcome, indent=2))
