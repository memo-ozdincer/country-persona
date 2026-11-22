"""Attribute the observed score margin to receipt changes and writing failures."""
import json

import numpy as np

import routing

EVIDENCE = routing.HERE / "writer-evidence"


def read(path):
    return json.loads(path.read_text())


def delivery(prior, policy):
    request, reply = map(np.asarray, policy)
    q_loss, r_loss, q_cost, _ = routing.config()
    focus = np.arange(4)[:, None]
    selected = (1 - q_loss) * (reply[:, request].T == focus) + q_loss * (reply[:, 0] == focus)
    return (1 - r_loss) * (prior * selected).sum(axis=1), float(q_cost * (prior.sum(axis=1) @ request))


def audit():
    score_record = EVIDENCE / "scores.json"
    scored = read(score_record)
    reference = read(routing.HERE / "routing-results.json")
    fit = read(routing.HERE / "routing-fit.json")
    strong = reference["results"][fit["training_prior"]]["policies"]["independent_priority_by_request"]
    policies = fit["learned_policy"], (strong["sender"], strong["receiver"])
    labels = read(EVIDENCE / "annotations.json")["rows"]
    assert scored["annotations_sha256"] == routing.digest(EVIDENCE / "annotations.json")
    text = read(EVIDENCE / "final-records.json")[routing.load()["id"]]
    edits = {}
    for name, review in labels.items():
        if review["guard"] != "failed":
            continue
        quote = review["issues"]["guard"]
        assert quote.endswith(".") and text[name].endswith(" " + quote)
        repaired = text[name][: -len(quote)].rstrip()
        assert all(entry["record"] in repaired for entry in review["met"].values())
        assert scored["records"][name]["words"] <= 85 and scored["records"][name]["release"] == 0
        edits[name] = {"deleted_exact_sentence": quote, "remaining_record": repaired, "clear": True}
    assert set(edits) == {"amendment_775/slip", "veto_explanation/matched"}

    points = {name: np.asarray(values) for name, values in scored["scores_by_focus_and_receipt"].items()}
    points["release_after_two_exact_deletions"] = points["release"].copy()
    focuses = [focus["id"] for focus in routing.load()["focuses"]]
    for index, focus in enumerate(focuses):
        for bit, scenario in enumerate(("slip", "matched")):
            if f"{focus}/{scenario}" in edits:
                points["release_after_two_exact_deletions"][index, bit] = points["raw"][index, bit]

    results = {}
    for name, prior in routing.priors():
        a, b = (delivery(prior, policy) for policy in policies)
        difference = a[0] - b[0]
        fees = b[1] - a[1]
        changes = {"matched_delivery_probability_differences": dict(zip(focuses, difference.tolist(), strict=True)),
                   "query_fee_contribution": fees}
        for metric, values in points.items():
            contributions = (values[:, 1] - values[:, 0]) * difference
            margin = float(contributions.sum() + fees)
            if metric in scored["comparisons"][name]:
                known = scored["comparisons"][name][metric]
                assert np.isclose(margin, known["learned"] - known["train_frozen_independent_priority_by_request"])
            changes[metric] = {"per_focus": dict(zip(focuses, contributions.tolist(), strict=True)), "margin": margin}
        results[name] = changes
    return {"scope": "Exact score decomposition. The two clean deletion variants are manual, diagnostic counterfactuals. "
                     "The archived candidate outputs and scored judgments are unchanged. Neither uncertain amendment record is repaired.",
            "score_sha256": routing.digest(score_record), "edited_variants": edits, "results": results}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
