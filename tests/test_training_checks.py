"""Fault injection for technical training checks, not persona-quality tests."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
peft = pytest.importorskip("peft")
from country_persona.training_checks import (MeasuredTrainingSteps, OptimizationAudit,
    adapter_snapshot, audit_completion_masks, check_adapter_update, finite_gradient_summary,
    tensor_state_digest, validate_rank_checks, verify_saved_adapter)


@pytest.fixture
def adapter():
    from transformers import Qwen3Config, Qwen3ForCausalLM
    torch.manual_seed(42)
    base = Qwen3ForCausalLM(Qwen3Config(vocab_size=32, hidden_size=8, intermediate_size=16,
        num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1, head_dim=4))
    return peft.get_peft_model(base, peft.LoraConfig(r=2, lora_alpha=4, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"))


def test_noop_and_nonfinite_adapter_updates_cannot_pass():
    start = {"lora_A": torch.ones(2, 2), "lora_B": torch.zeros(2, 2)}
    with pytest.raises(ValueError, match="No adapter"):
        check_adapter_update(start, deepcopy(start))
    end = deepcopy(start); end["lora_B"][0, 0] = float("nan")
    with pytest.raises(FloatingPointError, match="Nonfinite"):
        check_adapter_update(start, end)


def test_no_gradient_and_infinite_gradient_cannot_pass(adapter):
    with pytest.raises(ValueError, match="No trainable gradients"):
        finite_gradient_summary(adapter)
    p = next(p for p in adapter.parameters() if p.requires_grad)
    p.grad = torch.full_like(p, float("inf"))
    with pytest.raises(FloatingPointError, match="Nonfinite"):
        finite_gradient_summary(adapter)


def test_callback_snapshots_at_training_start_not_construction(adapter):
    callback = OptimizationAudit()
    assert callback.initial is None
    with torch.no_grad():
        for p in adapter.parameters():
            if p.requires_grad:
                p.add_(0.01)
    callback.on_train_begin(None, SimpleNamespace(global_step=0), None, model=adapter)
    assert tensor_state_digest(callback.initial) == tensor_state_digest(adapter_snapshot(adapter))


@pytest.mark.parametrize("loss", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_microbatch_loss_is_rejected_before_trainer_log_filter(loss):
    class Underlying:
        def training_step(self, model, inputs, num_items_in_batch=None):
            return torch.tensor(loss)
    class Measured(MeasuredTrainingSteps, Underlying):
        pass
    trainer = Measured()
    with pytest.raises(FloatingPointError, match="microbatch"):
        trainer.training_step(None, {"attention_mask": torch.ones(1, 3), "labels": torch.tensor([[-100, 2, 3]])})


def test_masks_detect_prompt_leak_and_lost_completion():
    row = {"prompt": [{"role": "user", "content": "source"}], "completion": [{"role": "assistant", "content": "answer"}]}
    class Tokenizer:
        def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=False):
            return [1, 2] if add_generation_prompt else [1, 2, 3, 4]
    prepared = [{"input_ids": [1, 2, 3, 4]}]
    for labels in ([1, -100, 3, 4], [-100, -100, -100, 4]):
        def collator(_):
            return {"input_ids": torch.tensor([[1, 2, 3, 4]]), "attention_mask": torch.ones(1, 4), "labels": torch.tensor([labels])}
        with pytest.raises(ValueError, match="supervised|Completion"):
            audit_completion_masks([row], prepared, collator, Tokenizer())


@pytest.fixture
def rank_reports():
    return [{"rank": i, "steps": 2, "training_loss": 1.5, "changed_adapter_tensors": 4,
             "initial_adapter_digest": "same-initial-fixture", "final_adapter_digest": "same-final-fixture",
             "actual_sequence_tokens": 100, "actual_target_tokens": 20, "gradient_checks": 2}
            for i in range(4)]


@pytest.mark.parametrize("field,value", [("rank", 0), ("steps", 1), ("training_loss", float("nan")),
    ("changed_adapter_tensors", 0), ("initial_adapter_digest", "different"),
    ("final_adapter_digest", "different"), ("actual_target_tokens", 0), ("gradient_checks", 1)])
def test_rank_disagreement_or_skipped_work_cannot_pass(rank_reports, field, value):
    validate_rank_checks(rank_reports, world=4, expected_steps=2)
    rank_reports[-1][field] = value
    with pytest.raises(ValueError):
        validate_rank_checks(rank_reports, world=4, expected_steps=2)


def test_missing_rank_cannot_pass(rank_reports):
    with pytest.raises(ValueError, match="rank"):
        validate_rank_checks(rank_reports[:-1], world=4, expected_steps=2)


def test_saved_adapter_reload_and_corruption(adapter, tmp_path):
    from safetensors.torch import load_file, save_file
    initial = adapter_snapshot(adapter)
    with torch.no_grad():
        for p in adapter.parameters():
            if p.requires_grad:
                p.add_(0.01)
    update = check_adapter_update(initial, adapter_snapshot(adapter))
    assert update["changed_adapter_tensors"] > 0
    adapter.save_pretrained(tmp_path)
    report = verify_saved_adapter(adapter, tmp_path, torch.tensor([[1, 2, 3]]))
    assert report["saved_tensors_equal"] and report["reload_verified_after_state_perturbation"]
    assert report["same_base_probe_logits_equal"]
    current = tensor_state_digest(adapter_snapshot(adapter))
    path = tmp_path / "adapter_model.safetensors"
    state = load_file(str(path)); state[next(iter(state))].add_(1)
    save_file(state, str(path))
    with pytest.raises(ValueError, match="Saved adapter"):
        verify_saved_adapter(adapter, tmp_path, torch.tensor([[1, 2, 3]]))
    assert tensor_state_digest(adapter_snapshot(adapter)) == current


def test_failed_reload_restores_in_memory_weights_and_training_mode(adapter, tmp_path, monkeypatch):
    adapter.train(); adapter.save_pretrained(tmp_path)
    expected = tensor_state_digest(adapter_snapshot(adapter))
    original = peft.set_peft_model_state_dict
    calls = 0
    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Injected loader failure")
        return original(*args, **kwargs)
    monkeypatch.setattr(peft, "set_peft_model_state_dict", fail_second)
    with pytest.raises(RuntimeError, match="Injected"):
        verify_saved_adapter(adapter, tmp_path, torch.tensor([[1, 2, 3]]))
    assert adapter.training
    assert tensor_state_digest(adapter_snapshot(adapter)) == expected
