"""Audit a completed format run and leave semantic judgments explicitly unscored."""
import argparse
import json
from pathlib import Path

from country_persona.action_eval import index_unique, validate_case
from country_persona.evidence_ledger import check_ledger
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def audit(pack, run, output):
    if output.exists():
        raise ValueError("Use a fresh audit directory")
    manifest = json.loads((pack / "manifest.json").read_text())
    for name, expected in manifest["files_sha256"].items():
        if sha256(pack / name) != expected:
            raise ValueError("Changed frozen diagnostic file: " + name)
    record = json.loads((run / "run.json").read_text())
    if record["status"] != "completed" or record["run_kind"] != "pinned_model_development_inference":
        raise ValueError("Require a completed model run, not a tokenizer/fixture report")
    if sha256(run / "predictions.jsonl") != record["predictions_sha256"]:
        raise ValueError("Changed predictions")
    preflight = record["preflight"]
    if preflight["pack_manifest_sha256"] != sha256(pack / "manifest.json") or preflight["model_lock_sha256"] != manifest["planned_model_lock_sha256"]:
        raise ValueError("Run model/pack binding differs")
    if record["adapter"] is not None or record["generation_config"]["max_new_tokens"] != manifest["maximum_output_tokens_per_call"]:
        raise ValueError("This base diagnostic requires the declared unadapted model and output cap")
    cases = index_unique(read_jsonl(pack / "cases.jsonl"), "case")
    rows = index_unique(read_jsonl(run / "predictions.jsonl"), "prediction")
    scenarios = index_unique(read_jsonl(pack / "scenarios.jsonl"), "scenario")
    if set(cases) != set(rows) or record["completed_cases"] != len(cases):
        raise ValueError("Missing or extra delivered outputs")
    reports, reviews = [], []
    for key, case in cases.items():
        validate_case(case)
        row = rows[key]
        if row["case_sha256"] != case["case_sha256"] or row["input_ids_digest"] != preflight["input_token_digests"][key] or digest(row["input_ids"]) != row["input_ids_digest"]:
            raise ValueError("Output case/input binding differs")
        if row["prompt_tokens"] != len(row["input_ids"]) or row["generated_tokens"] != len(row["generated_ids"]) or row["generated_tokens"] > manifest["maximum_output_tokens_per_call"]:
            raise ValueError("Invalid output/input token accounting")
        if row["stop_reason"] not in {"eos", "max_new_tokens"}:
            raise ValueError("Unknown stopping reason")
        result = {"id": key, "response_id": row["response_id"], "case_sha256": case["case_sha256"],
                  "output_digest": digest(row["output"]), "scenario_id": case["scenario_id"],
                  "format_condition": case["format_condition"], "stop_reason": row["stop_reason"],
                  "prompt_tokens": row["prompt_tokens"], "generated_tokens": row["generated_tokens"],
                  "generation_seconds": row["generation_seconds"], "ledger": None,
                  "semantic_validity": None, "answer_completeness": None}
        if case["format_condition"] == "evidence_json":
            result["ledger"] = check_ledger(row["output"], scenarios[case["scenario_id"]]["evidence"],
                                             capped=row["stop_reason"] == "max_new_tokens")
        reports.append(result)
        reviews.append({"id": key, "case_sha256": case["case_sha256"], "output_digest": digest(row["output"]),
                        "reference_file_sha256": manifest["files_sha256"]["review.references.jsonl"],
                        "reviewer": None, "review_status": "not_reviewed", "ratings": None,
                        "checks": ["All country questions answered with material qualifications",
                                   "No internally contradictory assertions even if a correct phrase also occurs",
                                   "Quoted passage supports the attached claim, not merely the topic",
                                   "Shared claims supported by every named country; differences not invented",
                                   "Silence remains unknown; source country, institutional actor and chronology preserved",
                                   "Proposals are distinguished from commitments; assess response as delivered"]})
    summary = {"status": "mechanical_audit_only_semantic_review_pending", "cases": len(reports),
               "run_sha256": sha256(run / "run.json"), "predictions_sha256": record["predictions_sha256"],
               "pack_manifest_sha256": sha256(pack / "manifest.json"),
               "by_condition": {}, "semantic_quality_scores": None,
               "limitations": manifest["limitations"]}
    for condition in manifest["conditions"]:
        selected = [r for r in reports if r["format_condition"] == condition]
        summary["by_condition"][condition] = {"calls": len(selected),
            **{k: sum(r[k] for r in selected) for k in ("prompt_tokens", "generated_tokens", "generation_seconds")},
            "capped_outputs": sum(r["stop_reason"] == "max_new_tokens" for r in selected),
            "mechanical_ledger_passes": sum(r["ledger"]["mechanical_checks_passed"] for r in selected) if condition == "evidence_json" else None}
    output.mkdir(parents=True)
    write_json(output / "report.json", summary)
    write_jsonl(output / "per-response.jsonl", reports)
    write_jsonl(output / "blank-review-checklist.jsonl", reviews)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.pack, args.run, args.output), indent=2))
