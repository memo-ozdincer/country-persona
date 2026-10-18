"""Replay actual input/output/review/exposure records without model inference."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import read_jsonl, sha256, write_json
from country_persona.scenario_sft import load_pack, role_counterfactual, ids_digest, audit_trace
from review_scenario_sft import validate_review
from run_scenario_native_boundary_control import derive


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--require-complete", action="store_true")
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Preserve prior verification receipt")
    release = ROOT / "research/scenario-role-sft-20261017-v1"
    cfg = json.loads((release / "fit-config.json").read_text())
    model_receipt = ROOT / "reports/qwen35-model-verification-20260930.json"
    model_files = json.loads(model_receipt.read_text())["files"]
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg["model_path"], local_files_only=True)
    fitting, held = load_pack(ROOT, release / "pack", tok)
    rubric_path = release / "rubric.json"
    rubric = json.loads(rubric_path.read_text())
    stages = {"base-sequence": (held, "sequence"), "base-native": (held, "native"),
              "base-native-boundary": (held, "boundary"), "adapter-fitting": (fitting, "sequence"),
              "adapter-held": (held, "sequence")}
    if (a.checkpoint / "adapter-native-boundary").exists():
        stages["adapter-native-boundary"] = (held, "boundary")
    checked = []
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    for name, (rows, mode) in stages.items():
        run = a.checkpoint / name
        if not run.exists() and not a.require_complete:
            continue
        launch = json.loads((run / "launch.json").read_text())
        parent = json.loads((a.checkpoint / "fit/launch.json").read_text()) if launch.get("resident_parent") else launch
        weights = parent["model_verification"]
        if (weights["revision"] != cfg["revision"] or weights["files"] != model_files
                or weights["receipt_sha256"] != sha256(model_receipt)
                or launch["gpu"]["name"] != "NVIDIA RTX PRO 6000 Blackwell Server Edition"):
            raise ValueError("Model/hardware verification changed")
        if launch.get("resident_parent") and launch["identity"] != parent["identity"]:
            raise ValueError("Resident evaluation identity changed")
        result = json.loads((run / "evaluation-result.json").read_text())
        responses = list(read_jsonl(run / "responses.jsonl"))
        if launch["status"] != "completed" or len(responses) != len(rows) or result["calls"] != len(rows):
            raise ValueError("Incomplete actual stage: " + name)
        if result["responses_sha256"] != sha256(run / "responses.jsonl"):
            raise ValueError("Changed response transcript")
        if [r["id"] for r in responses] != [r["id"] for r in rows]:
            raise ValueError("Case order changed")
        for response, row in zip(responses, rows):
            expected = row["input_ids"][:row["prefix_tokens"]]
            if mode == "native":
                expected = row["native_prefix_ids"]
            elif mode == "boundary":
                expected = derive(row, tok)[0]["native_prefix_ids"]
            if response["prefix_ids"] != expected or response["input_sha256"] != ids_digest(expected):
                raise ValueError("Actual prompt differs from the frozen/declared control")
            output = response["output_ids"]
            if not output or len(output) != response["generated_tokens"] or len(output) > 2048:
                raise ValueError("Output accounting changed")
            if response["output_raw"] != tok.decode(output, skip_special_tokens=False) or response["output_display"] != tok.decode(output, skip_special_tokens=True):
                raise ValueError("Actual decoded output changed")
            capped = len(output) == 2048 and output[-1] != eos
            if capped != response["at_cap"] or (not capped and output[-1] != eos):
                raise ValueError("Cap/termination accounting changed")
            if not math.isfinite(response["target_nll"]):
                raise ValueError("Nonfinite reference likelihood")
            if mode == "sequence":
                other = next(r["provenance"]["turns"][-1] for r in rows if r["source"] == row["source"] and r["country"] != row["country"])
                wrong = role_counterfactual(row, tok, other)
                if response["wrong_role_prefix_ids"] != wrong["input_ids"][:wrong["prefix_tokens"]]:
                    raise ValueError("Wrong-role diagnostic changed more than the requested header")
                if not math.isfinite(response["wrong_role_target_nll"]) or not math.isclose(response["correct_role_advantage"], response["wrong_role_target_nll"] - response["target_nll"], abs_tol=1e-9):
                    raise ValueError("Role-likelihood arithmetic changed")
        review = json.loads((run / "inspection.json").read_text())
        if review["rubric_sha256"] != sha256(rubric_path):
            raise ValueError("Different review criteria")
        scored = validate_review(review, responses, rubric, sha256(run / "responses.jsonl"))
        if scored != review["scores"]:
            raise ValueError("Stored review arithmetic changed")
        counts = Counter(u["status"] for c in review["cases"] for u in c["units"])
        checked.append(dict(stage=name, calls=len(rows), generated_tokens=sum(r["generated_tokens"] for r in responses),
                            content_units=dict(counts), strict_passes=sum(r["strict_pass"] for r in scored),
                            response_sha256=sha256(run / "responses.jsonl")))
    trace = None
    fit = a.checkpoint / "fit"
    if fit.exists():
        trace = audit_trace(fit / "optimization.jsonl", fitting, 32, 42)
        result = json.loads((fit / "training-result.json").read_text())
        if result["steps"] != 128 or result["sequence_tokens"] != 444032 or result["supervised_tokens"] != 100736:
            raise ValueError("Measured fitting exposure changed")
        if result["trace_sha256"] != sha256(fit / "optimization.jsonl") or not result["base_tensor_versions_unchanged"]:
            raise ValueError("Training provenance changed")
    elif a.require_complete:
        raise ValueError("Missing inspected fitting trace")
    write_json(a.output, dict(status="actual_inputs_outputs_masks_reviews_and_trace_replayed", stages=checked,
        trace=trace, actual_generated_answers=sum(s["calls"] for s in checked),
        optimizer_updates=128 if trace else 0, model_inference_calls_for_replay=0,
        limitation="Byte/decoder/provenance/arithmetic replay, not independent semantic entailment or persona adjudication."))
    print(json.dumps({"stages": len(checked), "answers": sum(s["calls"] for s in checked), "trace": trace}))


if __name__ == "__main__":
    main()
