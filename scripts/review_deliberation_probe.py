"""Create a review packet and score supplied ratings for a completed real transcript."""
import argparse
import json
from pathlib import Path

from country_persona.deliberation import evidence_packet
from country_persona.deliberation_audit import validate_transcript
from country_persona.deliberation_review import REVIEW_GUIDANCE, review_completion, review_item, review_template, score_deliberation
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/deliberation-probe-20260928-v1"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh review directory")
    manifest = json.loads((args.pack / "manifest.json").read_text())
    run = json.loads((args.run / "run.json").read_text())
    if run["status"] != "completed" or run["pack_manifest_sha256"] != sha256(args.pack / "manifest.json"):
        raise ValueError("Expected completed model inference on this exact frozen pack, not a preflight")
    if run["transcript_sha256"] != sha256(args.run / "transcript.jsonl"):
        raise ValueError("Transcript changed")
    for name in ("scenarios.jsonl", "review.references.jsonl"):
        if sha256(args.pack / name) != manifest["files_sha256"][name]:
            raise ValueError("Frozen sources/references changed")
    rows = list(read_jsonl(args.run / "transcript.jsonl"))
    if len(rows) != manifest["total_calls_per_checkpoint"] or any(r.get("generator_kind") != "pinned_qwen3_development_inference" for r in rows):
        raise ValueError("Expected a complete real-model transcript")
    refs = list(read_jsonl(args.pack / "review.references.jsonl"))
    by_ref = {r["scenario_id"]: r for r in refs}
    scenarios = {r["id"]: r for r in read_jsonl(args.pack / "scenarios.jsonl")}
    validate_transcript(list(scenarios.values()), rows)
    reviews = list(read_jsonl(args.reviews)) if args.reviews else []
    result = score_deliberation(rows, refs, reviews)
    items = [review_item(r, by_ref[r["scenario_id"]]) for r in rows]
    args.output.mkdir(parents=True)
    write_jsonl(args.output / "review-items.jsonl", items)
    write_jsonl(args.output / "review-template.jsonl", [review_template(i) for i in items])
    write_json(args.output / "scores.json", result)
    # Opaque ordering removes explicit condition/stage/model labels. Answer style
    # can still reveal its origin; this is not a guarantee of effective blinding.
    indexed = {r["response_id"]: r for r in rows}
    deck = ["# Deliberation review", "", "Rate independently before comparing outputs. Use met, unmet or unratable for every unit. Record source evidence and ambiguities in notes. Do not consult scores or transcript condition labels first.",
            "", "These proposed rubrics are awaiting independent construct review. A nation's dated public statement does not establish timeless national values or private negotiation preferences.",
            "", *REVIEW_GUIDANCE, ""]
    for scenario in scenarios.values():
        deck += [f"## Source packet {scenario['id']}", "", scenario["description"], "", evidence_packet(scenario), ""]
    for item in sorted(items, key=lambda r: r["response_id"]):
        row = indexed[item["response_id"]]; scenario = scenarios[row["scenario_id"]]
        countries = list(scenario["questions"]) if row["country"] == "ALL" else [row["country"]]
        deck += [f"## Response {row['response_id']}", "",
                 f"[Source packet: {scenario['id']}](#source-packet-{scenario['id']})", "", "### Questions", ""]
        deck += [f"{c}: {scenario['questions'][c]}" for c in countries]
        if row["stage"] == "synthesis":
            deck += ["", scenario["final_task"]]
        deck += ["", "### Candidate answer", "", row["output"] or "[EMPTY]", "", "### Rating units", ""]
        deck += [f"- `{k}`: {v}" for k, v in item["units"].items()]
        deck += ["", "---", ""]
    (args.output / "review-deck.md").write_text("\n".join(deck))
    write_json(args.output / "receipt.json", {"run_sha256": sha256(args.run / "run.json"),
               "pack_sha256": sha256(args.pack / "manifest.json"), "reviews_sha256": sha256(args.reviews) if args.reviews else None,
               **review_completion(result, refs),
               "scoring_code_sha256": {str(p): sha256(p) for p in [Path(__file__), Path("src/country_persona/deliberation_review.py"), Path("src/country_persona/deliberation.py")]},
               "guidance": list(REVIEW_GUIDANCE), "guidance_sha256": digest(REVIEW_GUIDANCE)})
    print(f"Prepared {len(items)} response reviews; {len(reviews)} supplied ratings. Unreviewed scores remain null.")


if __name__ == "__main__":
    main()
