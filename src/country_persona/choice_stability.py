"""Counterbalanced choice metrics; variants are not independent observations."""
from itertools import permutations
import math

from .action_eval import VOTES, check_probabilities, classification_metrics, parse_vote


def unique_argmax(probabilities):
    check_probabilities(probabilities, VOTES)
    winners = [v for v in VOTES if probabilities[v] == max(probabilities.values())]
    return winners[0] if len(winners) == 1 else None


def distribution_summary(probabilities):
    if not probabilities:
        raise ValueError("Cannot summarize zero distributions")
    for p in probabilities:
        check_probabilities(p, VOTES)
    mean = {v: math.fsum(p[v] for p in probabilities) / len(probabilities) for v in VOTES}
    jsd = math.fsum(p[v] * math.log(p[v] / mean[v])
                   for p in probabilities for v in VOTES if p[v] > 0) / len(probabilities)
    return {"mean_probabilities": mean, "generalized_jsd_nats": max(0.0, jsd)}


def summarize_group(cases, predictions, expected):
    """Require all six mappings exactly once, without silently dropping errors."""
    if len(cases) != 6 or {tuple(c["choice_order"]) for c in cases} != set(permutations(VOTES)):
        raise ValueError("A group must contain all six permutations exactly once")
    if len({(c["parent_id"], c["country_form"]) for c in cases}) != 1:
        raise ValueError("Mixed parent/name-form groups")
    rows = []
    for case in cases:
        if case["choice_labels"] != {v: str(i + 1) for i, v in enumerate(case["choice_order"])}:
            raise ValueError("Choice mapping does not match the declared order")
        p = predictions[case["id"]]
        if p["case_sha256"] != case["case_sha256"] or p.get("choice_labels") != case["choice_labels"]:
            raise ValueError("Prediction/case mapping or hash mismatch")
        if p.get("probability_semantics") != "conditional_on_legal_labels":
            raise ValueError("Unknown probability semantics")
        check_probabilities(p["probabilities"], VOTES)
        rows.append(p)
    probabilities = [p["probabilities"] for p in rows]
    votes = [parse_vote(p["output"], c["choice_labels"]) for c, p in zip(cases, rows)]
    summary = distribution_summary(probabilities)
    mixture_vote = unique_argmax(summary["mean_probabilities"])
    # Two invalid answers are not treated as a robust agreement.
    pair_agreement = sum(a is not None and a == b for i, a in enumerate(votes) for b in votes[i + 1:]) / 15
    return {"parent_id": cases[0]["parent_id"], "country_form": cases[0]["country_form"],
            "country": cases[0]["country"], "condition": cases[0]["condition"],
            "split_group": cases[0]["split_group"], "expected": expected,
            "case_ids": [c["id"] for c in cases], "generated_votes": votes,
            "conditional_argmax_votes": [unique_argmax(p) for p in probabilities],
            "generation_argmax_agreement": sum(v is not None and v == unique_argmax(p) for v, p in zip(votes, probabilities)) / 6,
            "all_six_agree": None not in votes and len(set(votes)) == 1,
            "correct_under_every_mapping": all(v == expected for v in votes),
            "pairwise_disagreement_rate": 1 - pair_agreement,
            "gold_probability_range": [min(p[expected] for p in probabilities), max(p[expected] for p in probabilities)],
            "legal_label_mass_range": [min(p["legal_label_mass"] for p in rows), max(p["legal_label_mass"] for p in rows)],
            "individual_prompt_metrics": classification_metrics([expected] * 6, votes, probabilities=probabilities),
            "mixture_vote": mixture_vote, **summary}


def summarize_groups(groups):
    if not groups:
        raise ValueError("Empty groups")
    return {"parent_prompts": len(groups), "event_groups": len({g["split_group"] for g in groups}),
            "mixture_metrics": classification_metrics([g["expected"] for g in groups], [g["mixture_vote"] for g in groups],
                                                       probabilities=[g["mean_probabilities"] for g in groups]),
            "mean_individual_prompt_accuracy": math.fsum(g["individual_prompt_metrics"]["accuracy"] for g in groups) / len(groups),
            "mean_individual_prompt_nll": math.fsum(g["individual_prompt_metrics"]["nll"] for g in groups) / len(groups),
            "all_six_agree_count": sum(g["all_six_agree"] for g in groups),
            "correct_under_every_mapping_count": sum(g["correct_under_every_mapping"] for g in groups),
            "mean_jsd_nats": math.fsum(g["generalized_jsd_nats"] for g in groups) / len(groups),
            "mean_pairwise_disagreement_rate": math.fsum(g["pairwise_disagreement_rate"] for g in groups) / len(groups),
            "generated_argmax_agreement": math.fsum(g["generation_argmax_agreement"] for g in groups) / len(groups)}
