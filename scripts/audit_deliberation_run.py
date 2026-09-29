"""Audit one completed interaction run with exact dependency replay and cost counts."""
import argparse
import json
from pathlib import Path

from country_persona.deliberation_audit import mechanical_summary
from country_persona.io import read_jsonl, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/deliberation-probe-20260928-v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use a fresh report")
    manifest = json.loads((args.pack / "manifest.json").read_text())
    run = json.loads((args.run / "run.json").read_text())
    if run["status"] != "completed" or run["pack_manifest_sha256"] != sha256(args.pack / "manifest.json"):
        raise ValueError("Expected completed model inference on this pack")
    if run["transcript_sha256"] != sha256(args.run / "transcript.jsonl") or manifest["files_sha256"]["scenarios.jsonl"] != sha256(args.pack / "scenarios.jsonl"):
        raise ValueError("Changed transcript or source scenarios")
    rows = list(read_jsonl(args.run / "transcript.jsonl"))
    if any(r["generator_kind"] != "pinned_qwen3_development_inference" for r in rows):
        raise ValueError("Fixtures/preflights are not model results")
    result = mechanical_summary(list(read_jsonl(args.pack / "scenarios.jsonl")), rows)
    result.update(run_sha256=sha256(args.run / "run.json"), transcript_sha256=run["transcript_sha256"],
                  peak_allocated_gpu_gib=run["peak_allocated_gpu_gib"], checkpoint_adapter=run["adapter"])
    write_json(args.output, result)
    print(json.dumps({k: result[k] for k in ("responses", "output_caps", "caps_by_stage", "total_prompt_tokens", "total_generated_tokens", "total_generation_seconds")}, indent=2))


if __name__ == "__main__":
    main()
