"""Freeze a six-case diagnostic of truncation and unsupported conclusions in synthesis."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from country_persona.action_eval import validate_case
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

INSTRUCTION = (
    "Before writing the memo, check every substantive conclusion against each country's own statement. "
    "A source that does not establish a position is not evidence that the country approved, rejected, "
    "or never approved that position. Preserve this distinction explicitly. Describe a position as common "
    "to all four countries only when each country's supplied statement supports it. Keep proposed next "
    "steps separate from documented commitments. Include common ground, unresolved differences and proposed next steps.")


def build(run, output):
    if output.exists():
        raise ValueError("Use a fresh diagnostic pack")
    record = json.loads((run / "run.json").read_text())
    if record["status"] != "completed" or sha256(run / "transcript.jsonl") != record["transcript_sha256"]:
        raise ValueError("Require the complete unchanged exploratory baseline")
    rows = [r for r in read_jsonl(run / "transcript.jsonl") if r["scenario_id"].startswith("climate-") and r["stage"] == "synthesis"]
    if len(rows) != 3:
        raise ValueError("Expected one climate synthesis per control condition")
    cases, links = [], []
    for row in rows:
        for name in ("original_prompt", "support_check_instruction"):
            case = deepcopy(row["case"])
            if name != "original_prompt":
                case.pop("id"); case.pop("case_sha256")
                case["prompt"][-1]["content"] += "\n\nFINAL SOURCE CHECK\n" + INSTRUCTION
                case["diagnostic_condition"] = name
                case["id"] = digest(case)[:24]; case["case_sha256"] = digest(case)
            validate_case(case)
            cases.append(case)
            links.append({"id": case["id"], "case_sha256": case["case_sha256"], "diagnostic_condition": name,
                          "original_response_id": row["response_id"], "original_case_sha256": row["case_sha256"],
                          "original_output_cap": row["maximum_output_tokens"], "new_output_cap": 1024,
                          "hypothesis": "Output-cap repair and source-scope wording are separate diagnostic changes."})
    output.mkdir(parents=True)
    write_jsonl(output / "cases.jsonl", cases)
    write_jsonl(output / "diagnostic-links.jsonl", links)
    result = {"status": "post_hoc_development_diagnostic_not_a_new_benchmark", "cases": len(cases),
              "source_run_sha256": sha256(run / "run.json"), "source_transcript_sha256": record["transcript_sha256"],
              "instruction": INSTRUCTION, "planned_model_lock_sha256": record["model_lock_sha256"],
              "maximum_output_tokens_per_call": 1024, "maximum_output_tokens_total": 6144,
              "files_sha256": {p.name: sha256(p) for p in output.iterdir()},
              "notes": ["Original rows retain exact prompts: compare greedy prefixes with the 512-token baseline.",
                        "Both diagnostic arms receive a 1024-token cap; only the added source-check instruction differs between them.",
                        "National input notes are frozen from the original run. No peers or training are regenerated.",
                        "Designed after inspecting baseline errors; it cannot supply a held-out efficacy claim or substitute for independent review."]}
    write_json(output / "manifest.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.run, args.output), indent=2))
