"""Compare a completed baseline and adapter run on the same frozen interaction pack."""
import argparse
import json
from pathlib import Path

from country_persona.deliberation_audit import validate_transcript
from country_persona.deliberation_comparison import compare_checkpoints
from country_persona.io import read_jsonl, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--before-reviews", type=Path)
    parser.add_argument("--after-reviews", type=Path)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/deliberation-probe-20260928-v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use a fresh comparison report")
    manifest = json.loads((args.pack / "manifest.json").read_text())
    for name, expected in manifest["files_sha256"].items():
        if sha256(args.pack / name) != expected:
            raise ValueError("Changed frozen interaction pack")
    scenarios = list(read_jsonl(args.pack / "scenarios.jsonl"))
    refs = list(read_jsonl(args.pack / "review.references.jsonl"))
    runs, outputs = [], []
    for root in (args.before, args.after):
        record = json.loads((root / "run.json").read_text())
        if record["pack_manifest_sha256"] != sha256(args.pack / "manifest.json") or record["transcript_sha256"] != sha256(root / "transcript.jsonl"):
            raise ValueError("Run does not match the frozen pack or exact transcript")
        rows = list(read_jsonl(root / "transcript.jsonl"))
        if any(r.get("generator_kind") != "pinned_qwen3_development_inference" for r in rows):
            raise ValueError("Expected real-model inference, not placeholders")
        validate_transcript(scenarios, rows)
        runs.append(record); outputs.append(rows)
    ratings = [list(read_jsonl(p)) if p else [] for p in (args.before_reviews, args.after_reviews)]
    result = compare_checkpoints(*runs, *outputs, refs, *ratings)
    result["inputs_sha256"] = {str(p): sha256(p) for p in (args.before / "run.json", args.after / "run.json", args.before_reviews, args.after_reviews) if p}
    write_json(args.output, result)
    print(f"Compared {result['matched_responses']} pairs; {result['fully_rated_pairs']} fully rated. Missing quality remains null.")


if __name__ == "__main__":
    main()
