"""Small, strict action scorer. Invalid generations remain errors; no judge calls."""
from __future__ import annotations

from collections import Counter
import math
from .io import digest

VOTES = ("Y", "N", "A")


def index_unique(rows, kind):
    result = {}
    for row in rows:
        key = row["id"]
        if not isinstance(key, str) or not key:
            raise ValueError(f"Invalid {kind} id")
        if key in result:
            raise ValueError(f"Duplicate {kind} id: {key}")
        result[key] = row
    return result


def validate_case(case):
    if not case.get("split_group") or not case.get("country"):
        raise ValueError("Missing country or event group")
    if not case.get("prompt"):
        raise ValueError("Empty prompt")
    if "expected" in case or "reference" in case:
        raise ValueError("Gold labels belong in the separate reference file")
    payload = {k: v for k, v in case.items() if k != "case_sha256"}
    if case.get("case_sha256") != digest(payload):
        raise ValueError("Case hash mismatch")
    if "choice_labels" in case:
        validate_choice_labels(case["choice_labels"])
        if case.get("task") != "recorded_vote_prediction":
            raise ValueError("Choice labels are only supported for the action task")


def validate_choice_labels(labels):
    if not isinstance(labels, dict) or set(labels) != set(VOTES):
        raise ValueError("Choice mapping must cover Y/N/A exactly")
    if any(not isinstance(v, str) or not v or v != v.strip() for v in labels.values()):
        raise ValueError("Choice strings must be nonempty without outer whitespace")
    if len(set(labels.values())) != len(VOTES):
        raise ValueError("Choice strings must be distinct")


def parse_vote(output, choice_labels=None):
    """Accept only the requested output vocabulary, allowing outer whitespace."""
    labels = choice_labels if choice_labels is not None else dict(zip(VOTES, VOTES))
    validate_choice_labels(labels)
    return {v: k for k, v in labels.items()}.get(output.strip()) if isinstance(output, str) else None


def check_probabilities(values, labels):
    if not isinstance(values, dict) or set(values) != set(labels):
        raise ValueError("Probabilities must name every legal label exactly once")
    for p in values.values():
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError("Invalid probability")
    if not math.isclose(sum(values.values()), 1.0, abs_tol=1e-8, rel_tol=0):
        raise ValueError("Probabilities do not sum to one; no silent normalization")


def classification_metrics(truth, predictions, labels=VOTES, probabilities=None):
    """None denotes an invalid/missing prediction and counts as a false negative."""
    labels = tuple(labels)
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("Expected distinct legal labels")
    if not truth or len(truth) != len(predictions):
        raise ValueError("Empty or unaligned classification rows")
    if any(y not in labels for y in truth):
        raise ValueError("Unknown reference label; non-voting is not abstention")
    if any(p is not None and p not in labels for p in predictions):
        raise ValueError("Unknown prediction label")
    n = len(truth)
    confusion = {y: {p: 0 for p in (*labels, "INVALID")} for y in labels}
    for y, pred in zip(truth, predictions):
        confusion[y][pred if pred is not None else "INVALID"] += 1
    support = Counter(truth)
    per_class = {}
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[y][label] for y in labels if y != label)
        fn = support[label] - tp
        per_class[label] = {
            "support": support[label], "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / support[label] if support[label] else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
        }
    observed_recalls = [x["recall"] for x in per_class.values() if x["recall"] is not None]
    result = {
        "rows": n, "accuracy": sum(y == p for y, p in zip(truth, predictions)) / n,
        "invalid_or_missing_rate": predictions.count(None) / n,
        "macro_f1_fixed_labels": sum(x["f1"] for x in per_class.values()) / len(labels),
        "balanced_accuracy_observed_classes": sum(observed_recalls) / len(observed_recalls),
        "balanced_accuracy_all_classes": sum(observed_recalls) / len(labels) if len(observed_recalls) == len(labels) else None,
        "missing_reference_classes": [x for x in labels if not support[x]],
        "per_class": per_class, "confusion": confusion,
        "probability_rows": 0, "probability_coverage": 0.0, "nll": None, "brier": None,
    }
    if probabilities is not None:
        if len(probabilities) != n:
            raise ValueError("Unaligned probabilities")
        losses, briers = [], []
        for y, probs in zip(truth, probabilities):
            if probs is None:
                continue
            check_probabilities(probs, labels)
            losses.append(-math.log(max(probs[y], 1e-15)))
            briers.append(sum((probs[k] - float(y == k)) ** 2 for k in labels))
        result["probability_rows"] = len(losses)
        result["probability_coverage"] = len(losses) / n
        # Avoid silently comparing selective subsets: headline proper scores require full coverage.
        if len(losses) == n:
            result.update(nll=sum(losses) / n, brier=sum(briers) / n, nll_probability_floor=1e-15)
    return result


def score_actions(cases, references, predictions):
    """Join by immutable case hash; outputs can be partial, references cannot."""
    case_index = index_unique(cases, "case")
    ref_index = index_unique(references, "reference")
    pred_index = index_unique(predictions, "prediction")
    if set(ref_index) != set(case_index):
        raise ValueError("Reference IDs do not match case IDs")
    if set(pred_index) - set(case_index):
        raise ValueError("Unknown prediction IDs")
    truth, parsed, probs, enriched = [], [], [], []
    for key, case in case_index.items():
        validate_case(case)
        reference = ref_index[key]
        if reference.get("case_sha256") != case["case_sha256"]:
            raise ValueError("Reference case hash mismatch")
        if reference.get("expected") not in VOTES:
            raise ValueError("Unknown reference label; non-voting is not abstention")
        prediction = pred_index.get(key)
        if prediction is not None and prediction.get("case_sha256") != case["case_sha256"]:
            raise ValueError("Prediction case hash mismatch")
        if prediction is not None and prediction.get("choice_labels") != case.get("choice_labels"):
            raise ValueError("Prediction choice mapping differs from its case")
        vote = parse_vote(prediction.get("output"), case.get("choice_labels")) if prediction else None
        p = prediction.get("probabilities") if prediction else None
        if p is not None and prediction.get("probability_semantics") != "conditional_on_legal_labels":
            raise ValueError("Declare probability semantics; verbal confidence is not sufficient")
        truth.append(reference["expected"]); parsed.append(vote); probs.append(p)
        enriched.append({"id": key, "country": case["country"], "split_group": case["split_group"],
                         "expected": reference["expected"], "prediction": vote, "probabilities": p})
    overall = classification_metrics(truth, parsed, probabilities=probs)
    by_country = {}
    for country in sorted({r["country"] for r in enriched}):
        rows = [r for r in enriched if r["country"] == country]
        by_country[country] = classification_metrics([r["expected"] for r in rows], [r["prediction"] for r in rows],
                                                      probabilities=[r["probabilities"] for r in rows])
        by_country[country]["event_groups"] = len({r["split_group"] for r in rows})
    return {
        "overall": overall, "by_country": by_country,
        "event_groups": len({r["split_group"] for r in enriched}),
        "missing_predictions": sorted(set(case_index) - set(pred_index)),
        "country_macro_accuracy": sum(x["accuracy"] for x in by_country.values()) / len(by_country),
        "notes": ["Invalid or missing generations count as errors, never random votes.",
                  "Class labels are fixed at Y/N/A; absent-class recalls are null, not evidence of success.",
                  "NLL and Brier require full probability coverage and are conditional on legal labels.",
                  "No ranking AUC is inferred from hard labels. Scores do not certify temporal/source validity."],
    }
