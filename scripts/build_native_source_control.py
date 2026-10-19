"""Remove only application R from the existing Brazil prompt; no new source facts."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "research/native-application-writer-20261019-v1"
OUT = ROOT / "research/native-source-control-20261019-v1"


def build():
    original = next(r for r in json.loads((PARENT / "examples.json").read_text())
                    if r["id"] == "application-9469-BRA")
    row = copy.deepcopy(original)
    before, removed = row["messages"][1]["content"].split("\nHYPOTHETICAL APPLICATION R\n")
    assert removed.endswith("\nREQUESTED ROLE: BRA national delegation.")
    row.update(id="source-9469-BRA", split="source_control", target=None)
    row["messages"][1]["content"] = before + "\nREQUESTED ROLE: BRA national delegation."
    row["units"] = {k: v for k, v in original["units"].items() if not k.startswith("A")}
    assert len(row["units"]) == 9
    rubric = json.loads((PARENT / "rubric.json").read_text())
    rubric["units"] = {row["id"]: row["units"]}; rubric["source_map_units"] = {}
    rubric["scope"] = "Source-only deletion control; same dated sources/map, system and budget as historical Brazil application. Same-assistant adaptive development, not independent persona/OOD evidence."
    old_cfg = json.loads((ROOT / "research/native-writer-revision-20261019-v1/config.json").read_text())
    keys = ["model", "revision", "model_path", "seed", "maximum_length", "generation_max_new_tokens",
            "dtype", "attention", "adapter_path", "adapter_files_sha256", "adapter_tensor_digest", "decoder_path"]
    cfg = {k: old_cfg[k] for k in keys}
    cfg.update(optimizer_updates=0, cumulative_qwen35_updates=4134,
               initialization="Pinned base, followed after inspection by saved native40 adapter; no fitting.")
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    bindings = {str(PARENT.relative_to(ROOT) / name): sha(PARENT / name)
                for name in ["examples.json", "rubric.json", "grounding.json", "release.json"]}
    comparators = {}
    for arm, name in [("base", "base-new"), ("adapter", "adapter-new")]:
        stage = PARENT / "runtime" / name
        comparators[arm] = {"responses": str((stage / "responses.jsonl").relative_to(ROOT)),
                            "inspection": str((stage / "inspection.json").relative_to(ROOT))}
        for value in comparators[arm].values(): bindings[value] = sha(ROOT / value)
    protocol = dict(question="Does full source coverage fail even without hypothetical application, or does adding the second task introduce the omission?",
        intervention="Delete exactly the application R and provided analytical-plan substring. Keep complete two-country sources/maps, scenario, role, system240word instruction, weights/runtime/decoder fixed.",
        original_id=original["id"], case_id=row["id"], source_units=9, guards=6,
        decision_sequence="Read one base answer before explicit adapter operation. Read one adapter answer before choosing any next case/fit.",
        runner="scripts/run_native_writer_revision.py", runner_reuse="Data-defined one-case/two-arm runner reused verbatim; despite historical filename, this pack has no draft, peer or revision instruction.",
        planned_answers=2, optimizer_updates=0, source_comparators= comparators,
        unchanged_file_bindings=bindings, independent_review_complete=False,
        source_reading="Complete reused BRA465/FRA771-word sources and all checked maps reread by root assistant; no new documentary text. Independent review pending.",
        scope="Historically exposed adaptive Brazil/Libya development; source-realization/task-interference diagnostic, not hidden utility, forecasting, sealedOOD or multi-agent gain.",
        old_seed_control="preserved/unrun", no_next_fit_or_queue=True)
    return row, rubric, cfg, protocol


if __name__ == "__main__":
    assert not OUT.exists(), "Fresh pack required; preserve frozen evidence"
    OUT.mkdir()
    row, rubric, cfg, protocol = build()
    for name, value in [("example", row), ("rubric", rubric), ("config", cfg), ("protocol", protocol)]:
        (OUT / (name + ".json")).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    (OUT / "example.txt").write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in row["messages"])+"\n")
    print(json.dumps(dict(case=row["id"], source_units=len(row["units"]), optimizer_updates=0)))
