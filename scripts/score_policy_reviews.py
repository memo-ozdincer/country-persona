"""Join a reviewer's criterion ratings to exact policy responses and score them."""
import argparse
from collections import defaultdict

from country_persona.action_eval import index_unique
from country_persona.io import read_jsonl, sha256, write_json
from country_persona.policy_eval import score_policy_response, summarize_policy_scores


def score(cases, references, predictions, reviews):
    case_index = index_unique(cases, "case")
    ref_index = index_unique(references, "reference")
    outputs = {}
    for row in predictions:
        if row["response_id"] in outputs:
            raise ValueError("Duplicate response_id")
        outputs[row["response_id"]] = row
        if row["id"] not in case_index or row["id"] not in ref_index:
            raise ValueError("Response has no matching policy case/reference")
    if not outputs:
        raise ValueError("No outputs to score")
    by_reviewer = defaultdict(dict)
    for review in reviews:
        key = review["response_id"]
        if key not in outputs:
            raise ValueError("Review names an unknown response")
        reviewer = review["reviewer_id"]
        if key in by_reviewer[reviewer]:
            raise ValueError("Reviewer rated the same response twice")
        by_reviewer[reviewer][key] = review
    # Without reviews, expose missingness instead of producing a success rate.
    if not by_reviewer:
        by_reviewer[None] = {}
    result = {}
    for reviewer, supplied in by_reviewer.items():
        scores = [score_policy_response(case_index[p["id"]], ref_index[p["id"]], p, supplied.get(key))
                  for key, p in outputs.items()]
        kinds = {r["reviewer_kind"] for r in scores if r["review_supplied"]}
        if len(kinds) > 1:
            raise ValueError("One reviewer identity cannot mix human and authored-fixture provenance")
        result[reviewer or "unreviewed"] = {"summary": summarize_policy_scores(scores), "rows": scores}
    return {"by_reviewer": result,
            "note": "Reviewers are reported separately. No adjudication or semantic judging is performed by this script."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "references", "predictions", "reviews", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    result = score(list(read_jsonl(args.cases)), list(read_jsonl(args.references)),
                   list(read_jsonl(args.predictions)), list(read_jsonl(args.reviews)))
    result["input_sha256"] = {key: sha256(getattr(args, key)) for key in ("cases", "references", "predictions", "reviews")}
    write_json(args.output, result)
    for reviewer, values in result["by_reviewer"].items():
        print(reviewer, values["summary"])
