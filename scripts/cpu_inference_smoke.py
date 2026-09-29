"""Exercise all frozen probe prompts through tiny random Qwen3; no quality claims."""
import argparse
import json
from pathlib import Path

import torch
import transformers
from transformers import AutoTokenizer, GenerationConfig, Qwen3Config, Qwen3ForCausalLM

from country_persona.inference_probe import generation_config, run_cases, tokenize_cases
from country_persona.io import read_jsonl, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/eval-pilot-20260927/probe-v1"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(42)
    lock_path = Path("configs/posttraining/model.lock.json")
    lock = json.loads(lock_path.read_text())
    for entry in lock["files"]:
        if sha256(entry["path"]) != entry["sha256"]:
            raise ValueError("Locked tokenizer/config changed")
    manifest = json.loads((args.pack / "manifest.json").read_text())
    if sha256(args.pack / "cases.jsonl") != manifest["files_sha256"]["cases.jsonl"]:
        raise ValueError("Frozen probe changed")
    cases = list(read_jsonl(args.pack / "cases.jsonl"))
    tokenizer = AutoTokenizer.from_pretrained(lock["tokenizer_path"], local_files_only=True)
    source_generation = GenerationConfig.from_pretrained(lock["tokenizer_path"], local_files_only=True)
    config, model_eos = generation_config(source_generation, tokenizer, 4, "model")
    tokenized, label_ids = tokenize_cases(cases, tokenizer, lock["chat_template_kwargs"], 8192, 4, 8)
    tiny = Qwen3Config(vocab_size=len(tokenizer), hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                      num_attention_heads=2, num_key_value_heads=1, head_dim=8, max_position_embeddings=8192,
                      bos_token_id=source_generation.bos_token_id, eos_token_id=model_eos,
                      pad_token_id=source_generation.pad_token_id)
    model = Qwen3ForCausalLM(tiny)
    metadata = {"run_kind": "infrastructure_smoke_random_weights", "seed": 42, "device": "cpu",
                "torch_version": torch.__version__, "transformers_version": transformers.__version__,
                "weights": "random initialization; not Qwen3-8B pretrained weights; never use for quality evaluation",
                "architecture": tiny.to_dict(), "model_lock_sha256": sha256(lock_path),
                "case_file_sha256": sha256(args.pack / "cases.jsonl"),
                "chat_template_kwargs": lock["chat_template_kwargs"],
                "source_code_sha256": {str(p): sha256(p) for p in [Path(__file__), Path("src/country_persona/inference_probe.py")]}}
    result = run_cases(model, tokenizer, tokenized, config, model_eos, label_ids, args.output, metadata)
    rows = list(read_jsonl(args.output / "predictions.jsonl"))
    assert {r["id"] for r in rows} == {c["id"] for c in cases}
    for row, entry in zip(rows, tokenized):
        assert row["input_ids"] == entry["input_ids"]
        assert row["generated_tokens"] == len(row["steps"]) <= 4
        assert row["output_with_special_tokens"] == tokenizer.decode(row["generated_ids"], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if row["task"] == "recorded_vote_prediction":
            assert abs(sum(row["probabilities"].values()) - 1) < 1e-8
            assert 0 <= row["legal_label_mass"] <= 1
    report = {"status": "passed_infrastructure_only", "real_pretrained_model_generations": 0,
              "random_weight_generations": len(rows), "prompt_tokens": result["prompt_tokens"],
              "maximum_prompt_tokens": max(r["prompt_tokens"] for r in rows),
              "generated_tokens": result["generated_tokens"], "generation_seconds": result["generation_seconds"],
              "trace_processing_seconds": result["trace_processing_seconds"],
              "run_path": str(args.output), "run_receipt_sha256": sha256(args.output / "run.json"),
              "checks": ["All eight frozen prompts preserve every input token.",
                         "Per-step raw token IDs, decoded forms, EOS scores and stop reasons are present.",
                         "Every action has conditional canonical-label probabilities and independent legal-label mass.",
                         "Every run and output declares random-weight infrastructure provenance."],
              "limits": ["This does not test the 8B model, CUDA/BF16 behavior or the full 384-token output cap.",
                         "No action accuracy or policy fidelity score is computed from random-weight outputs.",
                         "Production GPU throughput, memory and stopping behavior remain unmeasured."]}
    write_json(args.report, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
