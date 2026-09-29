"""Freeze a three-context, three-format synthesis diagnostic; never generate answers."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from country_persona.action_eval import validate_case
from country_persona.deliberation import make_case, validate_scenario
from country_persona.eval_evidence import extract_columns, extract_speech, locate_support
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

CONDITIONS = ("prose_control", "evidence_prose", "evidence_json")
REQUIREMENTS = (
    "Answer every national question, preserving material conditions. For each country give a concise answer, "
    "one or two important factual claims with verbatim supporting quotations and the bracketed evidence ID, "
    "and any requested position not established by its full statement. Quotation whitespace may be normalized; "
    "do not rewrite words or punctuation. Source silence is not approval or rejection. "
    "Then give up to two common-ground claims and up to two material differences. Name the countries "
    "covered by each claim and supply a quotation from EACH named country's own source. A difference may be "
    "one of emphasis; do not invent a conflict. Empty common-ground/difference lists are allowed if unsupported. "
    "Give one or two proposed next steps, explicitly labeled as proposals, not documented commitments. "
    "An exact quote is insufficient if it does not support the associated claim. Notes may contain errors; "
    "the dated sources control. Keep the substantive analysis, not just a list of quotations.")
JSON_SHAPE = {
    "countries": [{"country": "FRA", "answer": "Answer this country's complete question",
                   "evidence": [{"claim": "Supported factual claim", "evidence_id": "packet evidence ID", "quote": "verbatim source text"}],
                   "not_established": ["Requested position that the statement does not establish"]}],
    "common_ground": [{"claim": "Shared position", "countries": ["FRA", "GBR"],
                       "evidence": [{"country": "FRA", "evidence_id": "packet evidence ID", "quote": "verbatim source text"},
                                    {"country": "GBR", "evidence_id": "packet evidence ID", "quote": "verbatim source text"}]}],
    "differences": [{"claim": "Material distinction", "countries": ["FRA", "IND"],
                     "evidence": [{"country": "FRA", "evidence_id": "packet evidence ID", "quote": "verbatim source text"},
                                  {"country": "IND", "evidence_id": "packet evidence ID", "quote": "verbatim source text"}]}],
    "proposals": [{"text": "Proposed next step", "status": "proposal_not_commitment"}],
}


def fresh_scenario(spec_path):
    spec = json.loads(spec_path.read_text())
    raw = Path(spec["source_directory"])
    acquired = json.loads((raw / "acquisition.json").read_text())
    source, = [s for s in acquired["sources"] if s["id"] == spec["source_id"]]
    if source["status"] != "acquired" or sha256(source["path"]) != source["sha256"] or source["sha256"] != spec["source_pdf_sha256"]:
        raise ValueError("Source PDF differs from the reviewed curation")
    # Re-extract from the pinned PDF, never trust a stale intermediate text file.
    document = extract_columns(source["path"])
    evidence = [extract_speech(document, s, source) for s in spec["speeches"]]
    scenario = {"id": "south-sudan-policy-workshop-v1", "split_group": "unsc-south-sudan-peace-process-2022",
                "description": "Compare the four delegations' documented positions in the 20 June 2022 South Sudan debate. This authored retrospective workshop did not occur historically.",
                "provenance": "authored_task_on_observed_dated_sources", "questions": spec["questions"], "evidence": evidence,
                "final_task": "Write a policy-analysis memo covering France, the UK, India and Brazil: what is documented common ground, what material differences or conditions remain, and what next steps could be proposed without inventing agreement? Address the questions in each country's brief."}
    scenario["scenario_sha256"] = digest(scenario)
    validate_scenario(scenario)
    by_country = {e["country"]: e for e in evidence}
    criteria = []
    for unit in spec["criteria"]:
        e = by_country[unit["country"]]
        c = {k: v for k, v in unit.items() if k != "quotes"}
        c["support_spans"] = [locate_support(e, quote) for quote in unit["quotes"]]
        if c.get("kind") == "bounded_absence":
            c["bounded_source_for_absence"] = {"evidence_id": e["id"], "text_digest": e["text_digest"], "scope": "complete supplied national statement"}
        elif not c["support_spans"]:
            raise ValueError("Positive requirement lacks a source span")
        criteria.append(c)
    reference = {"scenario_id": scenario["id"], "scenario_sha256": scenario["scenario_sha256"], "criteria": criteria,
                 "review_status": "assistant_source_checked; independent_review_pending", "quality_scores": None}
    return scenario, reference, spec


def format_case(base, condition):
    case = deepcopy(base)
    parent = case.pop("case_sha256"); case.pop("id")
    content = case["prompt"][-1]["content"]
    if content.count("Use at most 300 words.") != 1:
        raise ValueError("Unexpected source task word limit")
    # Common budget change applies to all three arms, including the prose control.
    content = content.replace("Use at most 300 words.", "Use at most 700 words, including quoted evidence.")
    if condition != "prose_control":
        content += "\n\nEVIDENCE REQUIREMENTS\n" + REQUIREMENTS
        if condition == "evidence_prose":
            content += "\nReturn prose with country headings and common-ground, differences and proposals sections."
        else:
            content += ("\nReturn one JSON object, without a Markdown fence or other text. Use exactly the following keys and types, "
                        "with all four country entries (FRA, GBR, IND, BRA), and real packet IDs and quotes. "
                        "The schema examples are placeholders, not policy evidence. Every list of countries must have a "
                        "supporting evidence entry for each named country. not_established may be empty.\n" + json.dumps(JSON_SHAPE))
    case["prompt"][-1]["content"] = content
    case.update(parent_case_sha256=parent, format_condition=condition,
                evaluation_status="development_format_diagnostic_not_held_out_benchmark")
    case["id"] = digest(case)[:24]; case["case_sha256"] = digest(case)
    validate_case(case)
    return case


def build(run, prior_pack, spec_path, output):
    if output.exists():
        raise ValueError("Use a fresh output directory")
    record = json.loads((run / "run.json").read_text())
    if record["status"] != "completed" or sha256(run / "transcript.jsonl") != record["transcript_sha256"]:
        raise ValueError("Require unchanged completed baseline")
    manifest = json.loads((prior_pack / "manifest.json").read_text())
    if sha256(prior_pack / "manifest.json") != record["pack_manifest_sha256"]:
        raise ValueError("Baseline and source pack differ")
    for name, expected in manifest["files_sha256"].items():
        if sha256(prior_pack / name) != expected:
            raise ValueError("Changed source scenario pack")
    scenarios = list(read_jsonl(prior_pack / "scenarios.jsonl"))
    for s in scenarios:
        validate_scenario(s)
    rows = list(read_jsonl(run / "transcript.jsonl"))
    selected = [r for r in rows if r["stage"] == "synthesis" and (
        (r["scenario_id"].startswith("climate-") and r["condition"] == "peer_revision") or
        (r["scenario_id"].startswith("ukraine-") and r["condition"] == "single_analyst"))]
    if len(selected) != 2:
        raise ValueError("Expected exactly two diagnosed contexts")
    fresh, fresh_ref, spec = fresh_scenario(spec_path)
    scenarios.append(fresh)
    bases = []
    for row in selected:
        validate_case(row["case"])
        scenario, = [s for s in scenarios if s["id"] == row["scenario_id"]]
        visible = [next(r for r in rows if r["response_id"] == rid) for rid in row["depends_on_response_ids"]]
        if make_case(scenario, row["condition"], "synthesis", "ALL", visible) != row["case"]:
            raise ValueError("Recorded source/history differs from replay")
        bases.append((row["case"], row["response_id"], "selected_after_observed_error"))
    bases.append((make_case(fresh, "single_analyst", "synthesis", "ALL", []), None, "fresh_event_without_generated_notes"))
    cases, links = [], []
    for base, rid, selection in bases:
        for condition in CONDITIONS:
            case = format_case(base, condition)
            cases.append(case)
            links.append({"id": case["id"], "case_sha256": case["case_sha256"], "format_condition": condition,
                          "scenario_id": base["scenario_id"], "original_response_id": rid,
                          "parent_case_sha256": base["case_sha256"], "selection": selection,
                          "maximum_output_tokens": 2048})
    output.mkdir(parents=True)
    write_jsonl(output / "cases.jsonl", cases)
    write_jsonl(output / "diagnostic-links.jsonl", links)
    write_jsonl(output / "evidence.jsonl", [e for s in scenarios for e in s["evidence"]])
    write_jsonl(output / "scenarios.jsonl", scenarios)
    old_refs = list(read_jsonl(prior_pack / "review.references.jsonl"))
    write_jsonl(output / "review.references.jsonl", [*old_refs, fresh_ref])
    write_json(output / "source-curation.json", spec)
    write_json(output / "output-shape.json", JSON_SHAPE)
    result = {"status": "frozen_development_format_diagnostic_no_generations", "cases": len(cases),
              "contexts": 3, "conditions": list(CONDITIONS), "source_statements": 12,
              "planned_model_lock_sha256": record["model_lock_sha256"],
              "baseline_run_sha256": sha256(run / "run.json"), "baseline_transcript_sha256": record["transcript_sha256"],
              "curation_sha256": sha256(spec_path), "builder_sha256": sha256(__file__),
              "maximum_output_tokens_per_call": 2048, "maximum_output_tokens_total": 18432,
              "context_budget": 8192, "common_word_limit": 700, "evidence_requirements": REQUIREMENTS,
              "contrasts": {"evidence_prose_minus_prose_control": "Added explicit claim/quote and uncertainty requirements",
                            "evidence_json_minus_evidence_prose": "Structured serialization of the same evidence requirements, with schema instructions"},
              "limitations": ["Two contexts selected after inspecting errors; all outputs will be development results.",
                              "South Sudan is a new issue but the same UN-record genre, model and four-country set, with no generated notes; not a held-out transfer benchmark.",
                              "Common 300-to-700-word limit change means the prose control is not the original prompt byte for byte.",
                              "Equal output caps, not equal actual compute; input tokens and schema overhead differ.",
                              "Quote lookup validates source location and country, not entailment, full-answer correctness or completeness.",
                              "Independent rubric review pending; no training admission or quality scores."],
              "files_sha256": {p.name: sha256(p) for p in sorted(output.iterdir())}}
    write_json(output / "manifest.json", result)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, default=Path("runs/deliberation-999389-base-v1"))
    p.add_argument("--prior-pack", type=Path, default=Path("data/prepared/deliberation-probe-20260928-v1"))
    p.add_argument("--curation", type=Path, default=Path("data/curation/south_sudan_synthesis_20260928.json"))
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(build(args.run, args.prior_pack, args.curation, args.output), indent=2))
