"""Replay the five-target application writer checkpoint; not independent grading."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import sha256, write_json
from country_persona.scenario_sft import audit_trace, locked_runtime
from run_native_application_writer import PACK, prepare, replay_comparators


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    cfg = json.loads((PACK / "config.json").read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg["model_path"], local_files_only=True)
    rows = prepare(tok)
    release = json.loads((PACK / "release.json").read_text())
    for path, expected in release["files_sha256"].items():
        assert sha256(ROOT / path) == expected, path
    grounding = json.loads((PACK / "grounding.json").read_text())
    assert grounding["old_examples_sha256"] == sha256(ROOT / "research/native-plan-writer-20261019-v1/examples.json")
    assert grounding["corrected_application_examples_sha256"] == sha256(ROOT / "research/native-plan-writer-application-20261019-v1/examples.json")
    for span in grounding["new_source_spans"]:
        source = (ROOT / span["path"]).read_text()
        assert source[span["start"]:span["end"]] == span["body"]
        assert hashlib.sha256(span["body"].encode()).hexdigest() == span["body_sha256"]
        for point in span["points"]:
            for anchor in point["support"]:
                assert source[anchor["start"]:anchor["end"]] == anchor["quote"]
    old = json.loads((ROOT / "research/native-plan-writer-20261019-v1/examples.json").read_text())
    for row in rows:
        if row["split"] == "train" and not row["id"].startswith("application-"):
            original = next(x for x in old if x["id"] == row["id"])
            assert all(row[k] == original[k] for k in ["messages", "target", "units"])
    run = ROOT / "runs/native-application-writer-20261019-v1"
    launch = json.loads((run / "launch.json").read_text())
    assert launch["status"] == "completed"
    assert launch["runtime"] == locked_runtime()
    assert launch["gpu"]["name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["production_optimizer_updates"] == 40
    assert json.loads((run / "actual-inputs-and-masks.json").read_text()) == rows
    assert replay_comparators(tok, rows) == json.loads((run / "comparator-replay.json").read_text())
    train = [r for r in rows if r["split"] == "train"]
    result = json.loads((run / "training-result.json").read_text())
    trace = audit_trace(run / "optimization.jsonl", train, 8, 42)
    assert trace["entries"] == result["steps"] == 40
    assert result["sequence_tokens"] == sum(len(r["input_ids"]) for r in train) * 8 == 98304
    assert result["supervised_tokens"] == sum(r["supervised_tokens"] for r in train) * 8 == 8176
    assert result["base_tensor_versions_unchanged"]
    assert result["serialization"]["same_base_probe_logits_equal"]
    assert result["serialization"]["maximum_logit_difference"] == 0
    for path, expected in result["serialization"]["files_sha256"].items():
        assert sha256(run / "adapter" / path) == expected
    rubric_path = PACK / "rubric.json"
    rubric = json.loads(rubric_path.read_text())
    stages = {}
    generated = 0
    for stage, split in [("base-new", "new_eval"), ("adapter-fitting", "train"),
                         ("adapter-source", "source_eval"),
                         ("adapter-application", "application_eval"),
                         ("adapter-new", "new_eval")]:
        dest = run / stage
        responses = [json.loads(s) for s in (dest / "responses.jsonl").read_text().splitlines()]
        inspection = json.loads((dest / "inspection.json").read_text())
        assert inspection["complete_outputs_read"] is True
        assert inspection["independent_review_complete"] is False
        assert inspection["responses_sha256"] == sha256(dest / "responses.jsonl")
        assert inspection["rubric_sha256"] == sha256(rubric_path)
        if "same_assistant_adjudication" in inspection:
            prior = inspection["same_assistant_adjudication"]
            assert sha256(dest / prior["prior_review"]) == prior["prior_sha256"]
        selected = {r["id"]: r for r in rows if r["split"] == split}
        reviews = {r["id"]: r for r in inspection["records"]}
        assert len(responses) == len(reviews) == len(selected)
        assert {r["id"] for r in responses} == set(selected) == set(reviews)
        counts, guards, coverage = Counter(), Counter(), Counter()
        passes = exact = tokens = 0
        for record in responses:
            row, review = selected[record["id"]], reviews[record["id"]]
            assert record["prefix_ids"] == row["prefix_ids"]
            assert record["prefix_sha256"] == row["prefix_sha256"]
            assert tok.decode(record["output_ids"], skip_special_tokens=False) == record["output_raw"]
            assert tok.decode(record["output_ids"], skip_special_tokens=True) == record["output_display"]
            assert len(record["output_ids"]) == record["generated_tokens"] and not record["at_cap"]
            assert review["words"] == len(record["output_display"].split())
            assert set(review["material"]) == set(rubric["units"][record["id"]])
            assert set(review["guards"]) == set(rubric["guards"])
            extra = review.get("source_map", {})
            assert set(extra) == set(rubric["source_map_units"].get(record["id"], {}))
            ratings = list(review["material"].values()) + list(review["guards"].values()) + list(extra.values())
            assert all(r in {"met", "unmet", "uncertain"} for r in ratings)
            assert review["strict_pass"] == all(r == "met" for r in ratings)
            assert (review["guards"]["length"] == "met") == (review["words"] <= 240)
            counts.update(review["material"].values()); guards.update(review["guards"].values()); coverage.update(extra.values())
            passes += review["strict_pass"]
            exact += row["target"] is not None and record["output_display"].strip() == row["target"].strip()
            tokens += record["generated_tokens"]
        generated += len(responses)
        stages[stage] = dict(answers=len(responses), material=dict(counts), guards=dict(guards),
                             source_map=dict(coverage), strict_passes=passes, exact_targets=exact,
                             generated_tokens=tokens, responses_sha256=sha256(dest / "responses.jsonl"))
    assert generated == launch["production_generation_records"] == 11
    write_json(args.output, dict(status="actual_inputs_masks_sources_40_updates_and_11_outputs_replayed",
        generation_records=generated, historical_comparator_records=8, historical_comparator_new_calls=0,
        optimizer_updates=40, cumulative_qwen35_updates=4134, fit_sequence_tokens=98304,
        fit_supervised_tokens=8176, stages=stages,
        adapter_tensor_digest=result["update"]["final_adapter_digest"],
        independent_semantic_review_complete=False,
        scope="Software integrity and same-assistant rating arithmetic, not independent semantic validation."))
    print(json.dumps(json.loads(args.output.read_text()), indent=2))


if __name__ == "__main__":
    main()
