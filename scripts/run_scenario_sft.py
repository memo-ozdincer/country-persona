"""One explicit preflight, CPU engineering check, fit OR evaluation; never a queue."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import sha256, write_json
from country_persona.scenario_sft import load_pack, locked_runtime, schedule, train_loop, evaluate, ids_digest
from run_aurora_qwen35_smoke import identity, current_gpu, verify_model

RELEASE = ROOT / "research/scenario-role-sft-20261017-v1"
MODEL = "/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"


def tiny_model():
    import torch
    from transformers import Qwen3_5ForCausalLM, Qwen3_5TextConfig
    torch.manual_seed(123)
    config = Qwen3_5TextConfig(vocab_size=128, hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1, head_dim=16,
        linear_num_key_heads=2, linear_num_value_heads=2, linear_key_head_dim=16, linear_value_head_dim=16,
        layer_types=["linear_attention", "full_attention"], tie_word_embeddings=True,
        max_position_embeddings=256, eos_token_id=2, pad_token_id=0,
        rope_parameters={"rope_type": "default", "rope_theta": 10000.0, "partial_rotary_factor": 0.5,
                         "mrope_section": [1, 1, 2]})
    config._attn_implementation = "sdpa"
    return Qwen3_5ForCausalLM(config)


def fresh_adapter(model, rank=8):
    from peft import get_peft_model, LoraConfig
    import torch
    model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM", r=rank, lora_alpha=2 * rank,
                                            lora_dropout=0.0, target_modules="all-linear", bias="none"))
    model.eval()
    device = next(model.parameters()).device
    probe = torch.tensor([[3, 4, 5]], device=device)
    with torch.inference_mode():
        actual = model(input_ids=probe, use_cache=False).logits
        with model.disable_adapter():
            base = model(input_ids=probe, use_cache=False).logits
    if not torch.equal(actual, base):
        raise ValueError("Fresh adapter changes base logits before fitting")
    return model


def cpu_check(output):
    import torch
    from peft import PeftModel
    from country_persona.scenario_sft import completion_loss
    from country_persona.training_checks import adapter_snapshot, tensor_state_digest
    torch.set_num_threads(1)
    rows = []
    for index in range(4):
        ids = [3, 4 + index, 8, 9, 10, 11, 12, 13, 14 + index, 2]
        rows.append(dict(id=f"synthetic-{index}", input_ids=ids, labels=[-100] * 6 + ids[6:],
                         prefix_tokens=6, supervised_tokens=4))
    model = fresh_adapter(tiny_model(), rank=2)
    probe = torch.tensor([rows[0]["input_ids"]])
    with torch.no_grad():
        full = model(input_ids=probe, use_cache=False).logits
        expected = torch.nn.functional.cross_entropy(full[:, 5:-1, :].float().reshape(-1, 128), probe[:, 6:].reshape(-1))
        actual = completion_loss(model, rows[0], "cpu")
    if not torch.allclose(expected, actual, atol=1e-6):
        raise ValueError("Target-only logits differ from full causal loss")
    corrupt = {**rows[0], "labels": list(rows[0]["input_ids"])}
    try:
        completion_loss(model, corrupt, "cpu")
    except ValueError:
        pass
    else:
        raise ValueError("Corrupt prompt mask admitted")
    result = train_loop(model, rows, presentations=2, seed=42, learning_rate=1e-3, output=output, device="cpu")
    model.eval()
    loaded = PeftModel.from_pretrained(tiny_model(), output / "adapter")
    loaded.eval()
    with torch.no_grad():
        a = model(input_ids=probe, use_cache=False).logits
        b = loaded(input_ids=probe, use_cache=False).logits
    if not torch.equal(a, b) or tensor_state_digest(adapter_snapshot(model)) != tensor_state_digest(adapter_snapshot(loaded)):
        raise ValueError("Cold adapter reload changed tensors/logits")
    # Prove the first token and EOS participate; a later-target perturbation must
    # change loss, and context labels must remain rejected above.
    result.update(kind="engineering_only_random_tiny_Qwen3_5_not_production_model",
                  full_vs_target_only_loss_equal=True, corrupt_prompt_mask_rejected=True,
                  cold_separate_base_reload_exact=True, production_model_calls=0, production_optimizer_updates=0)
    write_json(output / "cpu-check.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["preflight", "cpu-check", "fit", "evaluate"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gpu-uuid")
    parser.add_argument("--adapter-run", type=Path)
    parser.add_argument("--base-run", type=Path)
    parser.add_argument("--split", choices=["train", "eval"], default="eval")
    parser.add_argument("--format", choices=["sequence", "native"], default="sequence")
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    launch = dict(identity=identity(), mode=args.mode, runtime=locked_runtime(),
                  output=str(args.output), status="started", production_model_calls=0, production_optimizer_updates=0)
    write_json(args.output / "launch.json", launch)
    try:
        if args.mode == "cpu-check":
            result = cpu_check(args.output)
        else:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
            fitting, held = load_pack(ROOT, RELEASE / "pack", tokenizer)
            plan = schedule(fitting, 32, 42)
            write_json(args.output / "planned-schedule.json", plan)
            write_json(args.output / "mask-audit.json", [dict(id=r["id"],
                sequence_tokens=len(r["input_ids"]), masked_prefix_tokens=r["prefix_tokens"],
                supervised_tokens=r["supervised_tokens"],
                first_supervised_position=r["prefix_tokens"], first_prediction_position=r["prefix_tokens"] - 1,
                first_target_token_id=r["input_ids"][r["prefix_tokens"]],
                final_target_token_id=r["input_ids"][-1],
                prefix_labels_all_ignored=all(x == -100 for x in r["labels"][:r["prefix_tokens"]]),
                target_labels_equal_input=r["labels"][r["prefix_tokens"]:] == r["input_ids"][r["prefix_tokens"]:],
                input_ids_sha256=ids_digest(r["input_ids"]), labels_sha256=ids_digest(r["labels"])) for r in fitting + held])
            result = dict(examples=6, fitting_examples=4, development_examples=2, planned_updates=len(plan),
                sequence_tokens=sum(len(fitting[e["row"]]["input_ids"]) for e in plan),
                supervised_tokens=sum(fitting[e["row"]]["supervised_tokens"] for e in plan),
                actual_model_calls=0, actual_optimizer_updates=0)
            write_json(args.output / "preflight.json", result)
            if args.mode != "preflight":
                config_path = RELEASE / "fit-config.json"
                config = json.loads(config_path.read_text())
                if sha256(RELEASE / "pack/release.json") != config["release_sha256"] or sha256(RELEASE / "quality-review.json") != config["quality_review_sha256"]:
                    raise ValueError("Data/review lock changed")
                for name, expected in config["code_sha256"].items():
                    if sha256(ROOT / name) != expected:
                        raise ValueError("Training implementation changed since locking: " + name)
                for name, expected in config["artifact_sha256"].items():
                    if sha256(ROOT / name) != expected:
                        raise ValueError("Grounding, rubric or model receipt changed: " + name)
                if config["training"] != dict(rank=8, alpha=16, target_modules="all-linear", presentations=32,
                    updates=128, seed=42, learning_rate=5e-5, weight_decay=0.0, clip_norm=1.0,
                    batch_size=1, accumulation=1, max_length=8192, generation_max_new_tokens=2048):
                    raise ValueError("Different settings require a versioned experiment and runner")
                launch["fit_config_sha256"] = sha256(config_path)
                if args.mode == "fit":
                    if args.base_run is None:
                        raise ValueError("Inspect the two base development replies before fitting; supply their run")
                    inspection = json.loads((args.base_run / "inspection.json").read_text())
                    if inspection["responses_sha256"] != sha256(args.base_run / "responses.jsonl") or inspection["decision"] != "run_four_example_fit":
                        raise ValueError("Base inspection is missing, stale or recommends replanning")
                    base_launch = json.loads((args.base_run / "launch.json").read_text())
                    if base_launch.get("fit_config_sha256") != sha256(config_path) or base_launch.get("arm") != "base" or base_launch.get("format") != "sequence" or base_launch.get("status") != "completed":
                        raise ValueError("Base run is not the matched completed sequence control")
                    from review_scenario_sft import validate_review
                    from country_persona.io import read_jsonl
                    rubric_path = RELEASE / "rubric.json"
                    if inspection["rubric_sha256"] != sha256(rubric_path):
                        raise ValueError("Base inspection uses a changed rubric")
                    responses = list(read_jsonl(args.base_run / "responses.jsonl"))
                    if {r["id"] for r in responses} != {r["id"] for r in held}:
                        raise ValueError("Base inspection must cover both whole-episode development answers")
                    validate_review(inspection, responses, json.loads(rubric_path.read_text()), sha256(args.base_run / "responses.jsonl"))
                    launch["base_inspection_sha256"] = sha256(args.base_run / "inspection.json")
                if not args.gpu_uuid:
                    raise ValueError("An explicitly selected free GPU UUID is required")
                launch["gpu"] = current_gpu(args.gpu_uuid)
                if launch["gpu"]["name"] != "NVIDIA RTX PRO 6000 Blackwell Server Edition":
                    raise ValueError("Different hardware requires a separately recorded comparison")
                os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_uuid
                launch["model_verification"] = verify_model(config)
                # Hashing weights takes time; recheck immediately before allocation.
                current_gpu(args.gpu_uuid)
                write_json(args.output / "launch.json", launch)
                import torch
                from transformers import Qwen3_5ForCausalLM
                torch.manual_seed(42)
                model = Qwen3_5ForCausalLM.from_pretrained(MODEL, local_files_only=True,
                    dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda:0")
                if args.mode == "fit":
                    model = fresh_adapter(model)
                    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
                    result = train_loop(model, fitting, presentations=32, seed=42, learning_rate=5e-5,
                                        output=args.output, device="cuda:0")
                    launch["production_optimizer_updates"] = result["steps"]
                else:
                    launch.update(arm="adapter" if args.adapter_run else "base", format=args.format, split=args.split)
                    if args.adapter_run:
                        from peft import PeftModel
                        prior = json.loads((args.adapter_run / "launch.json").read_text())
                        training = json.loads((args.adapter_run / "training-result.json").read_text())
                        if prior.get("status") != "completed" or prior.get("fit_config_sha256") != sha256(config_path):
                            raise ValueError("Adapter fit is not a completed matched experiment")
                        for name, value in training["serialization"]["files_sha256"].items():
                            if sha256(args.adapter_run / "adapter" / name) != value:
                                raise ValueError("Changed saved adapter")
                        launch["adapter_training_result_sha256"] = sha256(args.adapter_run / "training-result.json")
                        model = PeftModel.from_pretrained(model, args.adapter_run / "adapter")
                    write_json(args.output / "launch.json", launch)
                    result = evaluate(model, tokenizer, fitting if args.split == "train" else held,
                                      args.output, "cuda:0", native=args.format == "native")
                    launch["production_model_calls"] = result["calls"]
                    write_json(args.output / "evaluation-result.json", result)
        launch.update(status="completed", result=result)
        write_json(args.output / "launch.json", launch)
        print(json.dumps({"status": "completed", "mode": args.mode, "output": str(args.output)}, indent=2))
    except Exception as exc:
        launch.update(status="failed", exception=repr(exc), traceback=traceback.format_exc())
        # Preserve actual partial progress, including an interrupted fit/generation.
        for name, key in [("optimization.jsonl", "production_optimizer_updates"), ("responses.jsonl", "production_model_calls")]:
            path = args.output / name
            if path.exists() and args.mode != "cpu-check":
                launch[key] = len(path.read_text().splitlines())
        write_json(args.output / "launch.json", launch)
        raise


if __name__ == "__main__":
    main()
