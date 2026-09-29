"""Prepare a blinded review deck and test rating arithmetic with authored fixtures."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.policy_eval import score_policy_response, summarize_policy_scores


def build(pack, seeds_path, output):
    if output.exists():
        raise ValueError("Choose a fresh calibration directory")
    manifest = json.loads((pack / "manifest.json").read_text())
    for filename in ("cases.jsonl", "policy.references.jsonl", "evidence.jsonl"):
        if sha256(pack / filename) != manifest["files_sha256"][filename]:
            raise ValueError("Frozen evaluation package changed")
    cases = {c["id"]: c for c in read_jsonl(pack / "cases.jsonl")}
    refs = {r["item_key"]: r for r in read_jsonl(pack / "policy.references.jsonl") if cases[r["id"]]["condition"] == "B"}
    seeds = json.loads(seeds_path.read_text())
    fixtures = []
    if seeds["include_one_supported_answer_per_item"]:
        for key, ref in refs.items():
            fixtures.append({"item_key": key, "seed_kind": "supported_paraphrase", "output": ref["worked_answer"],
                             "unmet_criteria": [], "unmet_checks": [], "expected_outcome": "pass",
                             "why": "Authored supported paraphrase; equivalent wording is acceptable."})
    fixtures += seeds["negative_seeds"]
    predictions, answer_key, templates, scores = [], [], [], []
    for fixture in fixtures:
        ref = refs[fixture["item_key"]]
        case = cases[ref["id"]]
        prediction = {"id": case["id"], "case_sha256": case["case_sha256"],
                      "response_id": digest([case["id"], fixture["output"]])[:24], "output": fixture["output"],
                      "provenance": "assistant_authored_calibration_example_not_model_output"}
        review = {"id": case["id"], "case_sha256": case["case_sha256"], "response_id": prediction["response_id"],
                  "output_digest": digest(prediction["output"]), "reviewer_id": "authored-fixture-expectations-v1",
                  "reviewer_kind": "authored_fixture",
                  "criteria": {c["id"]: "unmet" if c["id"] in fixture["unmet_criteria"] else "met" for c in ref["criteria"]},
                  "checks": {k: "unmet" if k in fixture["unmet_checks"] else "met" for k in ref["universal_checks"]}}
        if set(fixture["unmet_criteria"]) - set(review["criteria"]) or set(fixture["unmet_checks"]) - set(review["checks"]):
            raise ValueError("Seed names an unknown rubric criterion")
        score = score_policy_response(case, ref, prediction, review)
        if score["outcome"] != fixture["expected_outcome"]:
            raise ValueError("Scorer does not match the seed's expected treatment")
        template = deepcopy(review)
        template.update(reviewer_id=None, reviewer_kind=None, notes=None)
        template["criteria"] = {k: None for k in review["criteria"]}
        template["checks"] = {k: None for k in review["checks"]}
        predictions.append(prediction)
        answer_key.append({"review": review, "seed_kind": fixture["seed_kind"], "why": fixture["why"],
                           "expected_outcome": fixture["expected_outcome"]})
        templates.append(template)
        scores.append(score)
    if len({p["response_id"] for p in predictions}) != len(predictions):
        raise ValueError("Duplicate calibration response")
    # Stable opaque ordering hides the authored pass/fail groups, not authorship.
    predictions.sort(key=lambda p: p["response_id"])
    templates.sort(key=lambda p: p["response_id"])
    output.mkdir(parents=True)
    write_jsonl(output / "outputs.jsonl", predictions)
    write_jsonl(output / "review-template.jsonl", templates)
    write_jsonl(output / "private-answer-key.jsonl", answer_key)
    write_jsonl(output / "fixture-scores.jsonl", scores)
    report = {"status": "scoring_arithmetic_checked; semantic_calibration_pending",
              "source_pack_manifest_sha256": sha256(pack / "manifest.json"), "seed_config_sha256": sha256(seeds_path),
              "fixture_summary": summarize_policy_scores(scores), "seed_expectations_matched": len(scores),
              "model_outputs": 0, "independent_reviewers": 0, "raw_human_agreement": None,
              "limitations": ["Expectations were authored with the examples; these checks do not validate a semantic evaluator.",
                              "Reviewers should independently rate the deck without opening the private answer key.",
                              "The two-event deck is for rubric debugging, not a statistical estimate of model performance."]}
    write_json(output / "report.json", report)
    deck = ["# Policy rubric calibration deck", "",
            "These are authored examples, not model generations. Positive/negative seed labels and expected ratings are hidden here.", "",
            "Two reviewers should independently mark every required criterion and check as `met`, `unmet` or `unratable`. "
            "Use `review-template.jsonl`; fill reviewer identity/kind and retain the exact case/output hashes. "
            "Do not open `private-answer-key.jsonl` before rating. Record ambiguities before adjudication.", "",
            "Equivalent wording is acceptable. Empty answers fail. A correct vote does not excuse fabricated reasoning. "
            "Not established means absent from the bounded statement, not absent from every historical source.", ""]
    ref_by_id = {r["id"]: r for r in refs.values()}
    for pred in predictions:
        case, ref = cases[pred["id"]], ref_by_id[pred["id"]]
        deck += [f"## Response {pred['response_id']}", "", case["prompt"][1]["content"], "",
                 "### Candidate answer", "", pred["output"] or "[EMPTY ANSWER]", "", "### Required criteria", ""]
        deck += [f"- `{c['id']}`: {c['description']}" for c in ref["criteria"]]
        deck += ["", "### Universal checks", ""]
        deck += [f"- `{key}`: {description}" for key, description in ref["universal_checks"].items()]
        deck += ["", "---", ""]
    (output / "review-deck.md").write_text("\n".join(deck))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--seeds", type=Path, default=Path("data/curation/eval_calibration_seeds_20260927.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.pack, args.seeds, args.output), indent=2))
