"""Audit every prepared mask and run a tiny random-model CPU/DDP optimization check."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

from country_persona.io import sha256, write_json
from country_persona.train import validated_export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/training-readiness-20260928-v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rank, world = int(os.environ.get("RANK", "0")), int(os.environ.get("WORLD_SIZE", "1"))
    if world > 1 and sys.platform == "darwin":
        raise RuntimeError("This installed Accelerate/PyTorch combination passes device_ids to a Gloo barrier, "
                           "which selects unsupported MPS collectives on macOS. Run the single-CPU check here "
                           "and validate distributed execution on Linux; do not count this as a GPU/DDP pass.")
    # TRL constructs PartialState during preprocessing, before Trainer applies
    # use_cpu. Initialize that shared state explicitly below as well.
    os.environ["ACCELERATE_USE_CPU"] = "true"
    import torch
    from datasets import Dataset
    from peft import LoraConfig, PeftModel, get_peft_model_state_dict
    from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM
    from trl import SFTConfig, SFTTrainer
    from country_persona.training_checks import (MeasuredTrainingSteps, OptimizationAudit, adapter_snapshot, audit_completion_masks,
        check_adapter_update, validate_rank_checks, verify_saved_adapter)
    torch.set_num_threads(1)
    if world > 1:
        torch.distributed.init_process_group(backend="gloo")
    exists = torch.tensor([int(args.output.exists()) if rank == 0 else 0])
    if world > 1:
        torch.distributed.broadcast(exists, src=0)
    if exists.item():
        raise ValueError("Use a fresh check output directory")
    if rank == 0:
        args.output.mkdir(parents=True)
    if world > 1:
        torch.distributed.barrier()
    from accelerate import PartialState
    PartialState(cpu=True)
    torch.manual_seed(42)
    lock = json.loads(Path("configs/posttraining/model.lock.json").read_text())
    for item in lock["files"]:
        if sha256(item["path"]) != item["sha256"]:
            raise ValueError("Tokenizer lock mismatch")
    rows, meta = validated_export(args.pack / "fit-probe.train.jsonl", args.pack / "fit-probe.train.manifest.jsonl", "train", True)
    tokenizer = AutoTokenizer.from_pretrained(lock["tokenizer_path"], local_files_only=True)
    config = Qwen3Config(vocab_size=len(tokenizer), hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                        num_attention_heads=2, num_key_value_heads=1, head_dim=8, max_position_embeddings=8192,
                        eos_token_id=[151645, 151643], pad_token_id=151643)
    model = Qwen3ForCausalLM(config)
    original_weights = deepcopy(model.state_dict())
    model.config.use_cache = False
    model.enable_input_require_grads()
    settings = SFTConfig(output_dir=str(args.output / "adapter"), use_cpu=True, bf16=False, fp16=False,
                         ddp_backend="gloo" if world > 1 else None, ddp_find_unused_parameters=False,
                         gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
                         max_steps=2, max_length=8192, per_device_train_batch_size=1, gradient_accumulation_steps=1,
                         completion_only_loss=True, packing=False, report_to="none", save_strategy="no", logging_steps=1,
                         eos_token=tokenizer.eos_token, learning_rate=5e-5, seed=42, dataloader_pin_memory=False)
    optimization_audit = OptimizationAudit()
    class MeasuredTrainer(MeasuredTrainingSteps, SFTTrainer):
        pass
    trainer = MeasuredTrainer(model=model, args=settings, train_dataset=Dataset.from_list(rows), processing_class=tokenizer,
                         callbacks=[optimization_audit],
                         peft_config=LoraConfig(r=2, lora_alpha=4, lora_dropout=0.0, target_modules="all-linear", task_type="CAUSAL_LM"))
    mask_audit = audit_completion_masks(rows, trainer.train_dataset, trainer.data_collator, tokenizer)
    for row, prepared in zip(rows, trainer.train_dataset):
        full = tokenizer.apply_chat_template(row["prompt"] + row["completion"], tokenize=True, **lock["chat_template_kwargs"])
        prefix = tokenizer.apply_chat_template(row["prompt"], tokenize=True, add_generation_prompt=True, **lock["chat_template_kwargs"])
        if tokenizer.decode(full[len(prefix):]) != row["completion"][0]["content"] + tokenizer.eos_token + "\n":
            raise ValueError("Supervision is not the literal answer plus terminator")
    trained = trainer.train()
    state = get_peft_model_state_dict(trainer.model)
    update = check_adapter_update(optimization_audit.initial, adapter_snapshot(trainer.model))
    changed = update["changed_adapter_tensors"]
    if not changed or not torch.isfinite(torch.tensor(trained.training_loss)):
        raise ValueError("No finite, effective adapter update")
    trainer.save_model(str(args.output / "adapter"))
    local_check = {"rank": rank, "steps": trainer.state.global_step, "training_loss": trained.training_loss,
                   "actual_sequence_tokens": trainer.processed_tokens,
                   "actual_target_tokens": trainer.target_tokens,
                   "gradient_checks": len(optimization_audit.gradients),
                   "gradient_trace": optimization_audit.gradients, **update}
    if torch.distributed.is_initialized():
        gathered = [None for _ in range(world)]
        torch.distributed.all_gather_object(gathered, local_check)
        torch.distributed.barrier()
    else:
        gathered = [local_check]
    rank_checks = validate_rank_checks(gathered, world, expected_steps=2)
    if trainer.is_world_process_zero():
        serialization = verify_saved_adapter(trainer.model, args.output / "adapter",
                                             torch.tensor([trainer.train_dataset[0]["input_ids"][:32]]))
        base = Qwen3ForCausalLM(config); base.load_state_dict(original_weights)
        restored = PeftModel.from_pretrained(base, str(args.output / "adapter")).eval()
        restored_state = get_peft_model_state_dict(restored)
        if any(not torch.equal(state[k], restored_state[k]) for k in state):
            raise ValueError("Saved adapter state differs after reload")
        trainer.model.eval()
        ids = torch.tensor([trainer.train_dataset[0]["input_ids"][:16]])
        with torch.inference_mode():
            before = trainer.model(ids, use_cache=False).logits
            after = restored(ids, use_cache=False).logits
        if not torch.allclose(before, after, atol=1e-6, rtol=1e-6):
            raise ValueError("Same-base reloaded model logits differ")
        write_json(args.output / "check.json", {
            "status": "passed_random_tiny_cpu_model_not_persona_training", "world_size": world,
            "backend": "gloo" if world > 1 else "single_cpu", "actual_trl_rows_audited_per_rank": len(rows),
            "actual_supervised_tokens_audited_once": mask_audit["supervised_tokens_once"],
            "rank_checks_rows_changed_tensors": [[len(rows), r["changed_adapter_tensors"]] for r in gathered],
            "mask_audit": mask_audit, "optimization_checks": rank_checks, "serialization_checks": serialization,
            "steps": trainer.state.global_step, "finite_loss": trained.training_loss,
            "adapter_reload_equal": True, "same_base_reloaded_logits_equal": True,
            "base_weights_source": "random_initialization_not_the_pinned_8B_checkpoint",
            "source_sha256": sha256(__file__), "shared_checks_sha256": sha256("src/country_persona/training_checks.py"),
            "data_sha256": sha256(args.pack / "fit-probe.train.jsonl"),
            "limitations": ["CPU/Gloo does not validate CUDA, NCCL, H100 memory, throughput or cluster allocation.",
                            "Two steps and a tiny random network establish software behavior, not persona quality."]})
        print(f"Readiness check passed on {world} CPU process(es); no production model trained.", flush=True)
    if torch.distributed.is_initialized():
        torch.distributed.barrier()
        torch.distributed.destroy_process_group()


if __name__ == "__main__":
    main()
