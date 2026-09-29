"""Report pairwise rating agreement and exact disagreements; never adjudicate."""
from collections import Counter
from itertools import combinations
import argparse

from country_persona.action_eval import index_unique
from country_persona.io import read_jsonl, sha256, write_json
from country_persona.policy_eval import score_policy_response


def agreement(left, right):
    if len(left) != len(right):
        raise ValueError("Unaligned ratings")
    if any(v not in {"met", "unmet", "unratable"} for v in [*left, *right]):
        raise ValueError("Unknown rating")
    observed = [(a, b) for a, b in zip(left, right) if a != "unratable" and b != "unratable"]
    n = len(observed)
    if not n:
        return {"units": len(left), "jointly_ratable": 0, "coverage": 0.0, "raw_agreement": None, "cohen_kappa": None}
    a_count, b_count = Counter(a for a, _ in observed), Counter(b for _, b in observed)
    actual = sum(a == b for a, b in observed) / n
    chance = sum(a_count[k] * b_count[k] for k in ("met", "unmet")) / n ** 2
    return {"units": len(left), "jointly_ratable": n, "coverage": n / len(left), "raw_agreement": actual,
            "cohen_kappa": (actual - chance) / (1 - chance) if chance < 1 else None}


def compare(cases, references, predictions, reviews):
    cases, references = index_unique(cases, "case"), index_unique(references, "reference")
    if len({p["response_id"] for p in predictions}) != len(predictions):
        raise ValueError("Duplicate response ID")
    predictions = {p["response_id"]: p for p in predictions}
    ratings = {}
    for r in reviews:
        pred = predictions[r["response_id"]]
        score_policy_response(cases[pred["id"]], references[pred["id"]], pred, r)
        bucket = ratings.setdefault(r["reviewer_id"], {})
        if r["response_id"] in bucket:
            raise ValueError("Duplicate rating from a reviewer")
        bucket[r["response_id"]] = r
    if len(ratings) < 2:
        raise ValueError("At least two identified reviewers are required")
    output = []
    for a, b in combinations(sorted(ratings), 2):
        if set(ratings[a]) != set(predictions) or set(ratings[b]) != set(predictions):
            raise ValueError("Every reviewer must return every response; use unratable explicitly")
        kinds = {who: {r["reviewer_kind"] for r in ratings[who].values()} for who in (a, b)}
        if any(len(ks) != 1 for ks in kinds.values()):
            raise ValueError("One reviewer cannot mix provenance kinds")
        sections, disputes = {}, []
        for section in ("criteria", "checks"):
            left, right = [], []
            for response_id in sorted(predictions):
                ar, br = ratings[a][response_id], ratings[b][response_id]
                for key in sorted(ar[section]):
                    av, bv = ar[section][key], br[section][key]
                    left.append(av); right.append(bv)
                    if av != bv or av == "unratable":
                        disputes.append({"response_id": response_id, "section": section, "unit": key,
                                         "ratings": {a: av, b: bv}})
            sections[section] = agreement(left, right)
        output.append({"reviewers": [a, b], "reviewer_kinds": {k: next(iter(v)) for k, v in kinds.items()},
                       "both_declared_human": all(ks == {"human"} for ks in kinds.values()),
                       "responses": len(predictions), "agreement": sections, "needs_adjudication": disputes})
    return {"pairs": output,
            "limits": ["Identity labels do not prove independence; collect ratings separately before discussion.",
                       "Unratable is excluded from agreement but retained in coverage and adjudication.",
                       "Criterion units within the same response/event are dependent; no unit-level confidence interval is claimed.",
                       "Kappa is null for a constant agreed category; raw agreement and prevalence must be inspected."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "references", "predictions", "reviews", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    result = compare(*[list(read_jsonl(getattr(args, k))) for k in ("cases", "references", "predictions", "reviews")])
    result["input_sha256"] = {k: sha256(getattr(args, k)) for k in ("cases", "references", "predictions", "reviews")}
    write_json(args.output, result)
