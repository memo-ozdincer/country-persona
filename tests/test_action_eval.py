import math
import pytest
from country_persona.action_eval import classification_metrics, parse_vote, score_actions
from country_persona.io import digest


def fixtures():
    cases, refs, preds = [], [], []
    for i, vote in enumerate("YNA"):
        case = {"id": str(i), "country": "example", "split_group": str(i),
                "prompt": [{"role": "user", "content": "Synthetic scorer fixture"}]}
        case["case_sha256"] = digest(case)
        cases.append(case)
        refs.append({"id": str(i), "case_sha256": case["case_sha256"], "expected": vote})
        preds.append({"id": str(i), "case_sha256": case["case_sha256"], "output": vote})
    return cases, refs, preds


def test_perfect_and_inverted_known_answers():
    perfect = classification_metrics(list("YNA"), list("YNA"))
    wrong = classification_metrics(list("YNA"), list("NAY"))
    assert perfect["macro_f1_fixed_labels"] == perfect["balanced_accuracy_all_classes"] == 1
    assert wrong["accuracy"] == wrong["macro_f1_fixed_labels"] == 0


def test_majority_accuracy_does_not_hide_minority_failure():
    r = classification_metrics(list("YYYYYYYYNA"), list("YYYYYYYYYY"))
    assert r["accuracy"] == .8
    assert r["balanced_accuracy_all_classes"] == pytest.approx(1/3)
    assert r["per_class"]["N"]["recall"] == r["per_class"]["A"]["recall"] == 0


def test_invalid_and_missing_outputs_remain_errors():
    cases, refs, preds = fixtures()
    preds[0]["output"] = "Yes, because..."
    result = score_actions(cases, refs, preds[:2])
    assert result["overall"]["accuracy"] == pytest.approx(1/3)
    assert result["overall"]["invalid_or_missing_rate"] == pytest.approx(2/3)
    assert result["missing_predictions"] == ["2"]
    assert parse_vote(" A \n") == "A"
    assert parse_vote("Non-Voting") is None


def test_absent_class_is_not_a_success():
    r = classification_metrics(["Y"], ["Y"])
    assert r["accuracy"] == 1
    assert r["balanced_accuracy_all_classes"] is None
    assert r["per_class"]["N"]["recall"] is None
    assert r["macro_f1_fixed_labels"] == pytest.approx(1/3)


def test_probability_scores_require_real_complete_distributions():
    probs = {"Y": .5, "N": .25, "A": .25}
    r = classification_metrics(["Y"], ["Y"], probabilities=[probs])
    assert r["nll"] == pytest.approx(math.log(2))
    assert r["brier"] == pytest.approx(.375)
    partial = classification_metrics(["Y", "A"], ["Y", "Y"], probabilities=[probs, None])
    assert partial["probability_coverage"] == .5
    assert partial["nll"] is partial["brier"] is None


@pytest.mark.parametrize("probs", [{"Y": 1}, {"Y": .9, "N": .9, "A": 0},
                                   {"Y": float("nan"), "N": 0, "A": 1}, {"Y": True, "N": 0, "A": 0}])
def test_bad_probabilities_rejected(probs):
    with pytest.raises(ValueError):
        classification_metrics(["Y"], ["Y"], probabilities=[probs])


@pytest.mark.parametrize("kind", ["duplicate", "unknown", "stale", "prompt_changed", "reference_changed"])
def test_join_and_hash_integrity(kind):
    cases, refs, preds = fixtures()
    if kind == "duplicate": preds.append(dict(preds[0]))
    elif kind == "unknown": preds[0]["id"] = "unrecognized"
    elif kind == "stale": preds[0]["case_sha256"] = "old"
    elif kind == "prompt_changed": cases[0]["prompt"][0]["content"] = "changed"
    else: refs[0]["case_sha256"] = "old"
    with pytest.raises(ValueError): score_actions(cases, refs, preds)


def test_nonvoting_and_gold_in_prompt_file_rejected():
    with pytest.raises(ValueError): classification_metrics(["Non-Voting"], ["A"])
    cases, refs, preds = fixtures()
    cases[0]["expected"] = "Y"
    with pytest.raises(ValueError): score_actions(cases, refs, preds)


def test_order_does_not_change_score():
    cases, refs, preds = fixtures()
    assert score_actions(cases, refs, preds) == score_actions(cases, refs[::-1], preds[::-1])


def test_missing_probability_semantics_rejected():
    cases, refs, preds = fixtures()
    preds[0]["probabilities"] = {"Y": 1., "N": 0., "A": 0.}
    with pytest.raises(ValueError): score_actions(cases, refs, preds)
