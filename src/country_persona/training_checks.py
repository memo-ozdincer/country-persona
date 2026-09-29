"""Measured optimization checks shared by the real trainer and tiny CPU probe.

These checks establish that training and serialization worked, not that policy
fidelity or deliberation improved.
"""
import hashlib
import math
from pathlib import Path

from .io import digest, sha256
from transformers import TrainerCallback


class MeasuredTrainingSteps:
    """Mixin placed before SFTTrainer in the method-resolution order."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_tokens = 0
        self.target_tokens = 0

    def training_step(self, model, inputs, num_items_in_batch=None):
        import torch
        self.processed_tokens += int(inputs["attention_mask"].sum().item())
        self.target_tokens += int((inputs["labels"][:, 1:] != -100).sum().item())
        loss = super().training_step(model, inputs, num_items_in_batch)
        if not torch.isfinite(loss).all():
            raise FloatingPointError("Nonfinite microbatch loss; do not average/filter it into a successful run")
        return loss


def audit_completion_masks(rows, prepared_rows, collator, tokenizer):
    import torch
    if len(rows) != len(prepared_rows):
        raise ValueError("Prepared dataset changed row count")
    sequence_tokens = target_tokens = 0
    for i, (row, prepared) in enumerate(zip(rows, prepared_rows)):
        kwargs = row.get("chat_template_kwargs", {})
        full = tokenizer.apply_chat_template(row["prompt"] + row["completion"], tokenize=True, **kwargs)
        prefix = tokenizer.apply_chat_template(row["prompt"], tokenize=True, add_generation_prompt=True, **kwargs)
        batch = collator([prepared])
        labels = batch["labels"][0]
        if prepared["input_ids"] != full or full[:len(prefix)] != prefix:
            raise ValueError(f"Actual trainer input differs from the audited template at row {i}")
        if batch["input_ids"][0, :len(full)].tolist() != full or int(batch["attention_mask"].sum()) != len(full):
            raise ValueError(f"Collator changed source tokens or attention at row {i}")
        if len(labels) < len(full) or not torch.all(labels[:len(prefix)] == -100):
            raise ValueError(f"Prompt tokens are supervised at row {i}")
        expected = torch.tensor(full[len(prefix):], device=labels.device)
        if not torch.equal(labels[len(prefix):len(full)], expected) or not torch.all(labels[len(full):] == -100):
            raise ValueError(f"Completion/padding mask differs at row {i}")
        if not len(full) > len(prefix) > 0:
            raise ValueError(f"Missing prompt or supervised target at row {i}")
        sequence_tokens += len(full)
        target_tokens += len(full) - len(prefix)
    return {"rows": len(rows), "sequence_tokens_once": sequence_tokens,
            "supervised_tokens_once": target_tokens, "actual_trainer_masks_checked": True}


def adapter_snapshot(model):
    from peft import get_peft_model_state_dict
    state = {k: v.detach().cpu().clone() for k, v in get_peft_model_state_dict(model).items()}
    if not state:
        raise ValueError("No adapter tensors")
    return state


def tensor_state_digest(state):
    import torch
    return digest({k: {"shape": list(v.shape), "dtype": str(v.dtype),
                       "sha256": hashlib.sha256(v.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()}
                   for k, v in sorted(state.items())})


def check_adapter_update(initial, current):
    import torch
    if not initial or set(initial) != set(current):
        raise ValueError("Adapter tensor inventory changed")
    changed = 0
    delta_square = 0.0
    for k in initial:
        a, b = initial[k], current[k]
        if a.shape != b.shape or a.dtype != b.dtype:
            raise ValueError("Adapter shape/dtype changed: " + k)
        if not torch.isfinite(a).all() or not torch.isfinite(b).all():
            raise FloatingPointError("Nonfinite adapter tensor: " + k)
        changed += int(not torch.equal(a, b))
        delta_square += float((b.double() - a.double()).square().sum())
    if not changed:
        raise ValueError("No adapter tensors changed")
    return {"adapter_tensors": len(current), "changed_adapter_tensors": changed,
            "adapter_update_l2": math.sqrt(delta_square), "all_adapter_tensors_finite": True,
            "initial_adapter_digest": tensor_state_digest(initial), "final_adapter_digest": tensor_state_digest(current)}


def finite_gradient_summary(model):
    import torch
    gradients = [p.grad.detach() for p in model.parameters() if p.requires_grad and p.grad is not None]
    if not gradients:
        raise ValueError("No trainable gradients before optimizer step")
    if any(not torch.isfinite(g).all() for g in gradients):
        raise FloatingPointError("Nonfinite trainable gradient before optimizer step")
    norm = math.sqrt(sum(float(g.float().square().sum()) for g in gradients))
    if not math.isfinite(norm):
        raise FloatingPointError("Nonfinite gradient norm")
    return {"gradient_tensors": len(gradients), "finite": True,
            "gradient_l2_after_clipping": norm}


class OptimizationAudit(TrainerCallback):
    def __init__(self):
        self.initial = None
        self.gradients = []

    def on_train_begin(self, args, state, control, model=None, **kwargs):
        # Trainer invokes this after wrapping/preparing DDP, which broadcasts
        # parameters. A snapshot before DDP wrapping can differ across ranks.
        self.initial = adapter_snapshot(model)

    def on_pre_optimizer_step(self, args, state, control, model=None, **kwargs):
        self.gradients.append({"step": state.global_step + 1, **finite_gradient_summary(model)})


def validate_rank_checks(reports, world, expected_steps=None):
    if len(reports) != world or sorted(r["rank"] for r in reports) != list(range(world)):
        raise ValueError("Missing or duplicate training ranks")
    if len({r["final_adapter_digest"] for r in reports}) != 1:
        raise ValueError("Final adapter tensors differ between ranks")
    if len({r["initial_adapter_digest"] for r in reports}) != 1:
        raise ValueError("Initial adapter tensors differ between ranks after DDP preparation")
    if len({r["steps"] for r in reports}) != 1:
        raise ValueError("Ranks completed different optimizer-step counts")
    for r in reports:
        if not math.isfinite(r["training_loss"]) or r["changed_adapter_tensors"] < 1:
            raise ValueError("A rank has nonfinite loss or no adapter update")
        if r["actual_sequence_tokens"] <= 0 or r["actual_target_tokens"] <= 0:
            raise ValueError("A rank did not process supervised examples")
        if r["gradient_checks"] != r["steps"] or r["steps"] < 1:
            raise ValueError("Missing optimizer gradient checks")
        if expected_steps is not None and r["steps"] != expected_steps:
            raise ValueError("Training did not complete the requested steps")
    return {"all_ranks_participated": True, "rank_count": world,
            "all_ranks_same_final_adapter": True, "rank_checks": reports}


def verify_saved_adapter(model, directory, input_ids, *, atol=1e-6, rtol=1e-6):
    """Reload saved tensors into the same base; no second 8B model allocation.

    This is a serialization check. Separate frozen evaluation still loads the
    adapter through PeftModel.from_pretrained and measures behavioral outcomes.
    """
    import torch
    from peft import set_peft_model_state_dict
    from safetensors.torch import load_file
    directory = Path(directory)
    path = directory / "adapter_model.safetensors"
    current = adapter_snapshot(model)
    saved = load_file(str(path), device="cpu")
    if set(current) != set(saved) or any(not torch.equal(current[k], saved[k]) or current[k].dtype != saved[k].dtype for k in current):
        raise ValueError("Saved adapter tensors differ from the trained adapter")
    if any(not torch.isfinite(t).all() for t in saved.values()):
        raise FloatingPointError("Nonfinite saved adapter")
    was_training = model.training
    model.eval()
    try:
        with torch.inference_mode():
            expected = model(input_ids=input_ids, use_cache=False).logits[:, -1, :].float().cpu()
            # Perturb only adapter state before loading, so a no-op loader fails.
            set_peft_model_state_dict(model, {k: torch.zeros_like(v) for k, v in current.items()})
            if tensor_state_digest(adapter_snapshot(model)) == tensor_state_digest(current):
                raise ValueError("Adapter reload test did not perturb the state")
            loaded = set_peft_model_state_dict(model, saved)
            if loaded.unexpected_keys or tensor_state_digest(adapter_snapshot(model)) != tensor_state_digest(current):
                raise ValueError("Reloaded adapter state differs")
            actual = model(input_ids=input_ids, use_cache=False).logits[:, -1, :].float().cpu()
        if not torch.isfinite(expected).all() or not torch.isfinite(actual).all() or not torch.allclose(expected, actual, atol=atol, rtol=rtol):
            raise ValueError("Same-base logits differ after adapter reload")
        return {"saved_tensors_equal": True, "reload_verified_after_state_perturbation": True,
                "same_base_probe_logits_equal": True, "probe_tokens": input_ids.shape[-1],
                "maximum_logit_difference": float((expected - actual).abs().max()),
                "logit_atol": atol, "logit_rtol": rtol,
                "files_sha256": {p.name: sha256(p) for p in (path, directory / "adapter_config.json")}}
    finally:
        set_peft_model_state_dict(model, current)
        model.train(was_training)
