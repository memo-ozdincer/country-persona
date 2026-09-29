from copy import deepcopy
from itertools import permutations
import math

import pytest

from country_persona.action_eval import VOTES, parse_vote, validate_choice_labels
from country_persona.choice_stability import distribution_summary, summarize_group, unique_argmax


def group(always_first=False):
    cases, predictions = [], {}
    for i, order in enumerate(permutations(VOTES)):
        mapping = {v: str(j + 1) for j, v in enumerate(order)}
        case = {"id": str(i), "case_sha256": "fixture", "parent_id": "parent", "country_form": "iso",
                "country": "TEST", "condition": "control", "split_group": "fixture",
                "choice_order": list(order), "choice_labels": mapping}
        vote = order[0] if always_first else "A"
        cases.append(case)
        predictions[str(i)] = {"case_sha256": "fixture", "choice_labels": mapping,
                               "output": mapping[vote], "probability_semantics": "conditional_on_legal_labels",
                               "probabilities": {v: float(v == vote) for v in VOTES}, "legal_label_mass": 0.01}
    return cases, predictions


def test_mapping_makes_digits_semantic_not_literal():
    assert parse_vote(" 2 ", {"Y": "3", "N": "1", "A": "2"}) == "A"
    assert parse_vote("2 because", {"Y": "3", "N": "1", "A": "2"}) is None
    with pytest.raises(ValueError, match="distinct"):
        validate_choice_labels({"Y": "1", "N": "1", "A": "2"})


def test_equivariant_model_has_zero_dispersion_despite_moving_output_digits():
    cases, predictions = group()
    result = summarize_group(cases, predictions, "A")
    assert result["all_six_agree"] and result["correct_under_every_mapping"]
    assert result["generalized_jsd_nats"] == 0
    assert result["mixture_vote"] == "A"
    assert result["legal_label_mass_range"] == [0.01, 0.01]


def test_constant_first_position_is_not_mistaken_for_stable_behavior():
    cases, predictions = group(always_first=True)
    result = summarize_group(cases, predictions, "A")
    assert not result["all_six_agree"]
    assert result["mixture_vote"] is None
    assert result["mean_probabilities"] == pytest.approx(dict.fromkeys(VOTES, 1 / 3))
    assert result["generalized_jsd_nats"] == pytest.approx(math.log(3))
    assert result["pairwise_disagreement_rate"] == pytest.approx(0.8)


def test_invalid_generations_are_not_agreement_or_dropped():
    cases, predictions = group()
    for row in predictions.values():
        row["output"] = "uncertain"
    result = summarize_group(cases, predictions, "A")
    assert not result["all_six_agree"]
    assert result["generation_argmax_agreement"] == 0
    assert result["individual_prompt_metrics"]["invalid_or_missing_rate"] == 1


def test_incomplete_duplicate_or_mismapped_groups_are_rejected():
    cases, predictions = group()
    with pytest.raises(ValueError, match="six permutations"):
        summarize_group(cases[:-1], predictions, "A")
    bad = deepcopy(cases); bad[-1] = bad[0]
    with pytest.raises(ValueError, match="six permutations"):
        summarize_group(bad, predictions, "A")
    predictions["0"]["choice_labels"] = {"Y": "2", "N": "1", "A": "3"}
    with pytest.raises(ValueError, match="mapping or hash"):
        summarize_group(cases, predictions, "A")


def test_probability_validation_and_exact_ties():
    with pytest.raises(ValueError, match="sum to one"):
        distribution_summary([dict.fromkeys(VOTES, 0.2)])
    assert unique_argmax({"Y": 0.5, "N": 0.5, "A": 0}) is None
    a = distribution_summary([{"Y": 0.6, "N": 0.3, "A": 0.1}, {"Y": 0.4, "N": 0.3, "A": 0.3}])
    assert a["mean_probabilities"] == pytest.approx({"Y": 0.5, "N": 0.3, "A": 0.2})
    assert a["generalized_jsd_nats"] > 0
