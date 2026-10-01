"""Create a portable viewer and exact source→plan→SFT→output samples from frozen artifacts."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import digest, read_jsonl, sha256

FORMAT = Path("data/prepared/evidence-format-20260928-v1")
PLAN = Path("data/prepared/qwen35-plan-to-text-eval-20260930-v2")
FIT = Path("data/prepared/qwen35-plan-to-text-fit-20260930-v1")
BASE_RUN = Path("runs/aurora-qwen35-plan-to-text-base-20260930-v1")
FIT_RUN = Path("runs/aurora-qwen35-plan-to-text-fit-20260930-v1")
TEMPLATE = Path("explorer/training-samples.template.html")
LABELS = {
    "climate-policy-workshop-v1": ("Climate & security", "2021-12-09", "Council authority, participation and climate finance; keep agreement and uncertainty bounded."),
    "ukraine-policy-workshop-v1": ("Ukraine", "2022-09-27", "Draft support, institutional capacity and conditional positions; do not invent later votes or commitments."),
    "south-sudan-policy-workshop-v1": ("South Sudan", "2022-06-20", "Peace-process milestones, humanitarian protection and sanctions scope. This case was excluded from this fit but already exposed in development."),
}

def verified_pack(relative):
    manifest_path = ROOT / relative / ("release.json" if relative == FIT else "manifest.json")
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest["files_sha256"].items():
        assert sha256(ROOT / relative / name) == expected, f"Frozen file changed: {relative/name}"
    return manifest

def build(output: Path, viewer: Path):
    output = output.resolve(); viewer = viewer.resolve()
    if output.exists(): raise ValueError("Use a fresh output directory; preserve previous exports")
    assert viewer.is_relative_to(ROOT)
    release = verified_pack(FIT); verified_pack(PLAN); verified_pack(FORMAT)
    plans = {r["scenario_id"]: r for r in read_jsonl(ROOT / PLAN / "plans.jsonl")}
    cases = {r["scenario_id"]: r for r in read_jsonl(ROOT / PLAN / "cases.jsonl")}
    originals = {r["scenario_id"]: r for r in read_jsonl(ROOT / FORMAT / "cases.jsonl") if r["format_condition"] == "prose_control"}
    evidence = {r["id"]: r for r in read_jsonl(ROOT / FORMAT / "evidence.jsonl")}
    rows = list(read_jsonl(ROOT / FIT / "train.jsonl"))
    metadata = list(read_jsonl(ROOT / FIT / "train.manifest.jsonl"))
    base = {r["scenario_id"]: r for r in read_jsonl(ROOT / BASE_RUN / "transcript.jsonl")}
    adapted = {r["scenario_id"]: r for r in read_jsonl(ROOT / FIT_RUN / "transcript.jsonl")}
    target_spec = json.loads((ROOT / FIT / "teacher-targets.json").read_text())
    inspection = json.loads((ROOT / FIT_RUN / "inspection.json").read_text())
    training = {case["scenario_id"]: (rows[meta["row_index"]], meta)
                for meta in metadata for case in cases.values() if meta["id"] == case["id"]}
    assert len(rows) == len(training) == 2
    output.mkdir(parents=True)
    (output / "sources").mkdir()
    samples = []
    pdfs = {}
    for scenario, (title, date, overview) in LABELS.items():
        plan, case, original = plans[scenario], cases[scenario], originals[scenario]
        assert original["case_sha256"] == plan["original_case_sha256"]
        assert case["plan_sha256"] == plan["plan_sha256"]
        statements = [evidence[name] for name in plan["source_text_digests"]]
        for statement in statements:
            assert digest(statement["text"]) == statement["text_digest"] == plan["source_text_digests"][statement["id"]]
            assert statement["text"] in original["prompt"][-1]["content"]
            for span in plan["countries"][statement["country"]]["bullets"]:
                for anchor in span["support_spans"]:
                    assert statement["text"][anchor["start"]:anchor["end"]] == anchor["quote"]
            name = statement["source_id"] + ".pdf"
            if name not in pdfs:
                roots = [ROOT / "data/raw/eval-sources-20260927", ROOT / "data/raw/ledger-eval-sources-20260928-expansion"]
                path = next((p/name for p in roots if (p/name).exists()), None)
                assert path and sha256(path) == statement["pdf_sha256"]
                shutil.copy2(path, output / "sources" / name)
                pdfs[name] = str(path.relative_to(ROOT))
        before, after = base[scenario], adapted[scenario]
        assert before["id"] == after["id"] == case["id"]
        assert before["case_sha256"] == after["case_sha256"] == case["case_sha256"]
        assert before["input_ids_digest"] == after["input_ids_digest"]
        row, meta = training.get(scenario, (None, None))
        if row:
            assert row["prompt"] == case["prompt"]
            assert digest(row) == meta["example_sha256"]
            assert row["completion"][0]["content"] == target_spec["targets"][scenario]
        sample = dict(id=scenario, title=title, date=date, overview=overview,
                      used_in_fit=row is not None, sources=statements, plan=plan,
                      original_case=original, student_case=case,
                      training_row=row, training_metadata=meta,
                      base_output=before, adapter_output=after,
                      observation=inspection["observations"]["south_sudan_outside_training" if scenario.startswith("south-") else scenario.split("-")[0]])
        samples.append(sample)
    data = dict(schema_version=1, created_at=datetime.now(timezone.utc).isoformat(),
                samples=samples, teacher=target_spec["teacher"], release=release,
                training_jsonl_base64=base64.b64encode((ROOT/FIT/"train.jsonl").read_bytes()).decode(),
                model="Qwen/Qwen3.5-4B", gpu="NVIDIA RTX PRO 6000 Blackwell Server Edition",
                steps=20, new_model_calls=0, independent_review_complete=False)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    (output / "samples.json").write_text(text)
    shutil.copy2(ROOT / FIT / "train.jsonl", output / "training-points.jsonl")
    shutil.copy2(ROOT / FIT / "train.manifest.jsonl", output / "training-provenance.jsonl")
    for name, source in (("original-evidence.jsonl", FORMAT/"evidence.jsonl"),
                         ("original-source-cases.jsonl", FORMAT/"cases.jsonl"),
                         ("checked-plans.jsonl", PLAN/"plans.jsonl"),
                         ("student-inputs.jsonl", PLAN/"cases.jsonl"),
                         ("teacher-targets.json", FIT/"teacher-targets.json"),
                         ("base-transcript.jsonl", BASE_RUN/"transcript.jsonl"),
                         ("adapter-transcript.jsonl", FIT_RUN/"transcript.jsonl")):
        shutil.copy2(ROOT/source, output/name)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = (ROOT / TEMPLATE).read_text()
    assert template.count("__SAMPLE_DATA__") == 1
    html = template.replace("__SAMPLE_DATA__", payload)
    assert not re.search(r"hf_[A-Za-z0-9]{20,}|-----BEGIN .*PRIVATE KEY-----", html)
    viewer.write_text(html)
    (output / "training-samples.html").write_text(html)
    readme = """# Training data samples — 30 September 2026 trial

Open `training-samples.html` in a browser. The viewer works offline as one file; no server or model runtime is needed. Send that HTML file for the easiest walkthrough, or this folder/ZIP for PDFs and exact underlying files.

Both actual training points are included: climate/security and Ukraine. South Sudan is an outside-training, already-exposed development comparison; it has no SFT target in this release.

The pipeline is original bounded UN national statements → this session assistant's checked bullet plans → student prompt + assistant-authored full memo target → observed Qwen3.5-4B base/adapter answers. Plans and targets were authored by the same assistant after inspecting earlier errors; no separate teacher API endpoint was called and no standalone teacher conversation transcript is available. The source packet and saved specification are supplied rather than an invented teacher prompt.

`training-points.jsonl` is an exact byte copy of the two-row file used by the 20-step development fit. Loss applies only to the assistant memo completion, not the source or checked-plan prompt. Targets are synthetic analyst memos, not authentic government statements. Production admission/human-review flags remain false. Source statements retain the saved English UN extraction without cleanup; PDFs are included under `sources/`.

Model outputs are historical, unedited saved transcripts on identical checked-plan input token digests. Climate/Ukraine outputs are training controls, not held-out evaluation. The same assistant reviewed plans, targets and outputs; independent semantic review and validated persona gains remain pending. No new inference or training was performed to create this viewer.

Raw files retain original serialization where copied. `samples.json` joins records for browsing; it does not replace the frozen originals. `export-receipt.json` binds source and exported files by SHA256. Inline preview excerpts are labeled and can be expanded to full text.
"""
    (output / "README.md").write_text(readme)
    inputs = [FIT/"train.jsonl", FIT/"train.manifest.jsonl", FIT/"teacher-targets.json",
              PLAN/"plans.jsonl", PLAN/"cases.jsonl", FORMAT/"cases.jsonl", FORMAT/"evidence.jsonl",
              BASE_RUN/"transcript.jsonl", FIT_RUN/"transcript.jsonl", FIT_RUN/"inspection.json", TEMPLATE, Path(__file__).relative_to(ROOT)]
    receipt = dict(status="exact_training_samples_exported_no_new_model_calls", created_at=data["created_at"],
                   training_points=2, outside_training_monitor=1,
                   source_statements=12, original_pdfs=3, teacher_api_transcript_available=False,
                   source_hashes={str(p):sha256(ROOT/p) for p in inputs},
                   files={str(p.relative_to(output)):dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in output.rglob("*") if p.is_file()},
                   viewer=str(viewer.relative_to(ROOT)), viewer_sha256=sha256(viewer),
                   exact_sft_jsonl_bytes=True, source_text_digests_verified=True,
                   source_anchor_locations_verified=True, identical_comparison_input_token_digests=True,
                   semantic_validation="not_implied_by_byte_and_location_checks",
                   new_model_calls=0, new_optimizer_steps=0, independent_review_complete=False)
    (output / "export-receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    archive = output.parent / (output.name + ".zip")
    assert not archive.exists()
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output.rglob("*")):
            if p.is_file(): z.write(p, Path(output.name)/p.relative_to(output))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert z.read(output.name+"/training-points.jsonl") == (ROOT/FIT/"train.jsonl").read_bytes()
        assert z.read(output.name+"/training-samples.html") == viewer.read_bytes()
    print(json.dumps(dict(status=receipt["status"], viewer=str(viewer), bundle=str(archive),
                         bundle_bytes=archive.stat().st_size, bundle_sha256=sha256(archive)),indent=2))

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--viewer",type=Path,default=ROOT/"explorer/training-samples.html")
    args=parser.parse_args();build(args.output,args.viewer)
