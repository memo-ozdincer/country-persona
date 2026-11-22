"""Score response witness requirements and run matched sender optimization."""
from importlib.util import module_from_spec, spec_from_file_location
import json

from collect_grounded import HERE, OLD, fixtures, plan, read

spec = spec_from_file_location("prior_native_judge_score", OLD / "score_judgments.py")
prior_score = module_from_spec(spec)
spec.loader.exec_module(prior_score)


def classify(row, mappings):
    scope = row["scope"]
    if not scope:
        assert not row["verification"]
        return {}, {"ab": False, "ba": False, "mean": False, "agreement": False}
    margins = {}
    for suffix, labels in mappings.items():
        met = next(letter for letter, status in labels.items() if status == "met")
        unmet = next(letter for letter, status in labels.items() if status == "not met")
        scores = row["verification"][suffix]["logits"]
        margins[suffix] = scores[met] - scores[unmet]
    by_order = {key: score > 0 for key, score in margins.items()}
    return (margins | {"mean": sum(margins.values()) / 2},
            by_order | {"mean": sum(margins.values()) > 0, "agreement": all(by_order.values())})


def run():
    data = fixtures()
    archived = read(HERE / "verified.json")
    labels = plan()["labels"]
    assert data.keys() == archived["cases"].keys()
    judged = {}
    for key, row in archived["cases"].items():
        case = data[key]
        span = row["scope"]
        if span:
            assert span["text"] == case["payload"]["record"][span["start"]:span["stop"]]
        margins, calls = classify(row, labels)
        calls_used = [row["id_reply"], *row["verification"].values()]
        judged[key] = {
            "calls": len(calls_used), "input_tokens": sum(call["input_tokens"] for call in calls_used),
            "met": case["met"], "mutation": case["mutation"], "weight": case["weight"],
            "scope": span, "selector": row["id_reply"]["text"], "margins": margins,
            "judgments": calls | {"span_exists": bool(span)},
        }
    held = [row for key, row in judged.items() if key.startswith("control/")]
    actual = [row for key, row in judged.items() if not key.startswith("control/") and not row["mutation"]]
    changes = [row for row in judged.values() if row["mutation"]]
    groups = {"archived": actual, "mutations": changes, "cross_family": held}
    metrics = {name: prior_score.summarize(rows) for name, rows in groups.items()}
    selector = {
        name: {"cited_true": sum(r["met"] and r["scope"] is not None for r in rows),
               "cited_false": sum(not r["met"] and r["scope"] is not None for r in rows),
               "calls": sum(r["calls"] for r in rows), "input_tokens": sum(r["input_tokens"] for r in rows),
               "n": len(rows)}
        for name, rows in groups.items()
    }
    old = read(OLD / "results.json")
    return {"calls": archived["calls"], "selection": selector, "metrics": metrics,
            "previous_averaged": {"archived": old["archived_record_metrics"]["mean"],
                                  "mutations": old["mutation_metrics"]["mean"]},
            "cases": judged, "downstream": prior_score.replay(judged)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
