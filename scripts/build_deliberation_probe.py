"""Freeze two source-backed interaction scenarios and separate review references."""
from copy import deepcopy
from pathlib import Path
import argparse
import json

from country_persona.deliberation import COUNTRIES, PROTOCOL, validate_scenario
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def build(pack, output):
    if output.exists():
        raise ValueError("Use a fresh scenario pack")
    manifest = json.loads((pack / "manifest.json").read_text())
    for name in ("cases.jsonl", "evidence.jsonl"):
        if sha256(pack / name) != manifest["files_sha256"][name]:
            raise ValueError("Source pack changed")
    cases = [c for c in read_jsonl(pack / "cases.jsonl") if c["task"] == "policy_fidelity" and c["condition"] == "B"]
    evidence = list(read_jsonl(pack / "evidence.jsonl"))
    refs = {r["id"]: r for r in read_jsonl("data/review/eval-pilot-20260927/construct-v2.1/policy.references.v2.jsonl")}
    scenarios, references = [], []
    for key, description in (
        ("climate", "Compare the four delegations' documented positions in the 9 December 2021 climate/security debate. This authored workshop did not occur historically."),
        ("ukraine", "Compare the four delegations' documented positions in the 27 September 2022 Ukraine debate. This authored workshop did not occur historically.")):
        selected = [e for e in evidence if e["id"].startswith(key + "-")]
        by_country = {c["country"]: c for c in cases if c["evidence_ids"][0].startswith(key + "-")}
        scenario = {"id": key + "-policy-workshop-v1", "split_group": by_country["FRA"]["family"],
                    "description": description, "provenance": "authored_task_on_observed_dated_sources",
                    "questions": {c: by_country[c]["prompt"][1]["content"].split("QUESTION\n", 1)[1].split("\n\nDATED PUBLIC STATEMENT", 1)[0]
                                  for c in COUNTRIES}, "evidence": selected,
                    "final_task": "Write a policy-analysis memo covering France, the UK, India and Brazil: what is documented common ground, what material differences or conditions remain, and what next steps could be proposed without inventing agreement? Address the questions in each country's brief."}
        scenario["scenario_sha256"] = digest(scenario)
        validate_scenario(scenario)
        scenarios.append(scenario)
        references.append({"scenario_id": scenario["id"], "scenario_sha256": scenario["scenario_sha256"],
                           "national_policy_rubrics": {c: deepcopy(refs[by_country[c]["id"]]) for c in COUNTRIES},
                           "synthesis_checks": {
                               "supported_country_positions": "Represent each country's documented position accurately, with material conditions.",
                               "common_ground_and_differences": "Identify supported agreement and distinctions; do not manufacture either unanimity or conflict.",
                               "proposal_not_commitment": "Label proposed next steps as proposals, without assigning undocumented concessions or joint commitments.",
                               "source_attribution_and_time": "Keep source, country, institutional capacity and dates correct; no later vote is established by the packet.",
                               "responsive_analysis": "Explain implications or remaining tradeoffs, not merely a list of vague diplomatic phrases."},
                           "independent_review_status": "pending", "quality_scores": None})
    output.mkdir(parents=True)
    write_jsonl(output / "scenarios.jsonl", scenarios)
    write_jsonl(output / "review.references.jsonl", references)
    write_json(output / "protocol.json", PROTOCOL)
    report = {"status": "frozen_development_protocol_not_model_results", "scenarios": 2, "source_statements": 8,
              "countries": list(COUNTRIES), "calls_per_model_condition": {"independent_revision": 18, "peer_revision": 18, "single_analyst": 6},
              "total_calls_per_checkpoint": 42, "max_output_tokens_per_checkpoint": 6 * PROTOCOL["per_condition_output_token_cap"],
              "source_pack_sha256": sha256(pack / "manifest.json"), "protocol_sha256": digest(PROTOCOL),
              "files_sha256": {p.name: sha256(p) for p in output.iterdir()},
              "notes": ["Same sources in every arm; only the peer arm sees others' initial answers before revising.",
                        "All revisions are synchronous; no agent sees another agent's revised answer.",
                        "Final aggregation always uses the unadapted base model.",
                        "Equal output caps do not imply equal actual compute; log total tokens and latency.",
                        "Both issues were already exposed; no final-test or statistical generalization claim.",
                        "Independent rubric review is pending; empty review fields are not zero-quality or passing results."]}
    write_json(output / "manifest.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/eval-pilot-20260927/two-event-v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.pack, args.output), indent=2))
