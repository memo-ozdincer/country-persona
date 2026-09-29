"""Prepare a tiny source-backed fit probe; never claim a substantive persona trial."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.posttraining import tokenize_example


def build(source, output, lock_path):
    if output.exists():
        raise ValueError("Use a fresh prepared directory")
    spec = importlib.util.spec_from_file_location("workshop_validator", Path(__file__).with_name("validate_policy_workshop.py"))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.validate(source)
    lock = json.loads(lock_path.read_text())
    for item in lock["files"]:
        if sha256(item["path"]) != item["sha256"]:
            raise ValueError("Tokenizer lock mismatch")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(lock["tokenizer_path"], local_files_only=True)
    rows = list(read_jsonl(source / "revision.sft.jsonl"))
    metas = list(read_jsonl(source / "revision.sft.manifest.jsonl"))
    items = []
    for row, meta in zip(rows, metas):
        if meta["example_sha256"] != module.digest(row) or len(meta["country_iso3s"]) != 1:
            raise ValueError("Expected aligned single-country revision cases")
        country = meta["country_iso3s"][0]
        if country not in {"FRA", "GBR", "IND", "BRA"}:
            raise ValueError("Excluded country")
        length, supervised = tokenize_example(tokenizer, row)
        if length > 8192:
            raise ValueError("No silent truncation")
        m = {**meta, "country_iso3": country, "upstream_example_sha256": meta["example_sha256"], "upstream_split": meta["split"],
             "split": "train", "status": "research_prepared", "machine_checks_passed": True,
             "human_reviewed": False, "sequence_tokens": length, "supervised_tokens": supervised,
             "model_revision": lock["revision"], "tokenizer_lock_sha256": sha256(lock_path),
             "preparation_policy": "technical-fit-probe-only; assistant-authored-grounded-revision; not-observed-behavioral-SFT"}
        items.append((row, m))
    smoke = [min((item for item in items if item[1]["country_iso3"] == c), key=lambda x: x[1]["sequence_tokens"])
             for c in ("FRA", "GBR", "IND", "BRA")]
    output.mkdir(parents=True)
    files = {}
    for name, subset in (("smoke.train", smoke), ("fit-probe.train", items)):
        write_jsonl(output / f"{name}.jsonl", [r for r, _ in subset])
        write_jsonl(output / f"{name}.manifest.jsonl", [{**m, "row_index": i, "example_sha256": digest(r)} for i, (r, m) in enumerate(subset)])
        files[name] = {"examples": len(subset), "source_components": len({m["split_group"] for _, m in subset}),
                       "countries": dict(Counter(m["country_iso3"] for _, m in subset)),
                       "sequence_tokens_once": sum(m["sequence_tokens"] for _, m in subset),
                       "supervised_tokens_once": sum(m["supervised_tokens"] for _, m in subset),
                       "maximum_sequence_tokens": max(m["sequence_tokens"] for _, m in subset)}
    old_evidence = list(read_jsonl("data/prepared/eval-pilot-20260927/two-event-v1/evidence.jsonl"))
    training_evidence = list(read_jsonl(source / "evidence.jsonl"))
    overlap = {e["pdf_sha256"] for e in old_evidence} & {e["raw_sha256"] for e in training_evidence}
    if overlap:
        raise ValueError("Training source bytes overlap the exposed UN evaluation sources")
    report = {"status": "technical_probe_prepared_not_launched", "model": lock["model"], "revision": lock["revision"],
              "model_lock_sha256": sha256(lock_path), "input_build_report_sha256": sha256(source / "build-report.json"),
              "builder_sha256": sha256(__file__), "outputs": files, "source_documents": len({e["raw_sha256"] for e in training_evidence}),
              "source_cases": len(items), "exact_raw_source_overlap_with_two_event_eval": len(overlap),
              "substantive_training_ready": False, "substantive_training_blockers": [
                  "Only ten underlying authored cases/four connected source components; no meaningful hidden test.",
                  "Independent evaluation/source review remains pending.",
                  "A fit probe verifies optimization and grounded response behavior; it does not replace the planned observed-behavior SFT experiment."],
              "training_admitted": False, "research_use_is_explicit": True,
              "limits": ["Original quarantine files are preserved; research_prepared does not assert human review or rights clearance.",
                         "One primary SFT view only; no duplicate audit/DPO/multi-agent targets are mixed into the probe.",
                         "Exact-source separation does not certify semantic-family separation or base-model decontamination.",
                         "Fit-probe training loss and memorization are not evaluation gains."],
              "files_sha256": {p.name: sha256(p) for p in output.iterdir() if p.is_file()}}
    write_json(output / "release.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/prepared/policy-workshop-20260916"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=Path("configs/posttraining/model.lock.json"))
    args = parser.parse_args()
    result = build(args.source, args.output, args.lock)
    print(json.dumps({k: result[k] for k in ("status", "outputs", "substantive_training_ready")}, indent=2))
