from copy import deepcopy
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from country_persona.inference_probe import (
    generation_config, infer_one, probability_trace, run_cases, stop_trace, verify_snapshot,
)
from country_persona.io import digest, sha256


class ToyTokenizer:
    eos_token_id = 1
    pad_token_id = 0

    def decode(self, ids, skip_special_tokens=False, **kwargs):
        return "".join(f"<t{i}>" for i in ids if not skip_special_tokens or i not in (0, 1))


@pytest.fixture
def tiny_inputs():
    torch.manual_seed(42)
    torch.set_num_threads(2)
    config = transformers.Qwen3Config(vocab_size=8, hidden_size=16, intermediate_size=32,
                                      num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1,
                                      head_dim=8, max_position_embeddings=64, bos_token_id=3,
                                      eos_token_id=[1, 0], pad_token_id=0)
    model = transformers.Qwen3ForCausalLM(config).eval()
    case = {"id": "tiny", "country": "IND", "split_group": "test-only", "condition": "B",
            "task": "recorded_vote_prediction", "prompt": [{"role": "user", "content": "Test only."}]}
    case["case_sha256"] = digest(case)
    entry = {"case": case, "input_ids": [2, 3], "input_ids_digest": digest([2, 3])}
    return model, ToyTokenizer(), entry, {"Y": 2, "N": 3, "A": 4}


def test_high_conditional_confidence_does_not_hide_low_legal_mass():
    probs = torch.tensor([0.90, 0.04, 0.03, 0.01, 0.02], dtype=torch.float64)
    result = probability_trace(torch.log(probs), 0, {"Y": 1, "N": 2, "A": 3}, [4])
    assert result["probabilities"] == pytest.approx({"Y": 0.5, "N": 0.375, "A": 0.125})
    assert result["legal_label_mass"] == pytest.approx(0.08)
    assert result["selected_token_log_probability"] == pytest.approx(float(torch.log(probs[0])))
    assert result["top_tokens"][0]["id"] == 0


def test_probability_trace_is_stable_for_large_logits():
    logits = torch.tensor([10000.0, 9999.0, 9998.0, 9997.0], dtype=torch.float64)
    a = probability_trace(logits, 0, {"Y": 1, "N": 2, "A": 3}, [0])
    b = probability_trace(logits - 10000, 0, {"Y": 1, "N": 2, "A": 3}, [0])
    assert a["probabilities"] == pytest.approx(b["probabilities"])
    assert a["legal_label_mass"] == pytest.approx(b["legal_label_mass"])


def test_nonfinite_logits_are_rejected():
    with pytest.raises(ValueError, match="Non-finite"):
        probability_trace(torch.tensor([float("nan"), 0, 1, 2]), 0, {"Y": 1, "N": 2, "A": 3}, [0])


def test_eos_at_cap_is_not_misreported_as_truncation():
    trace = stop_trace([2, 1], [1, 0], [1, 0], 2)
    assert trace["stop_reason"] == "eos"
    assert trace["at_cap_boundary"] is True
    assert trace["hit_output_cap"] is False


def test_legacy_eos_omission_is_visible_in_raw_trace():
    trace = stop_trace([0, 2, 2], [1], [1, 0], 3)
    assert trace["ignored_model_eos_positions"] == [0]
    assert trace["hit_output_cap"] is True


@pytest.mark.parametrize("tokens,limit", [([1, 2], 2), ([2], 3), ([], 3)])
def test_unexplained_or_broken_stopping_fails(tokens, limit):
    with pytest.raises(ValueError):
        stop_trace(tokens, [1, 0], [1, 0], limit)


def test_actual_qwen_generation_trace_matches_direct_first_forward(tiny_inputs):
    model, tokenizer, entry, labels = tiny_inputs
    config, original = generation_config(model.generation_config, tokenizer, 4, "model")
    with torch.inference_mode():
        direct = model(torch.tensor([entry["input_ids"]]), logits_to_keep=1).logits[0, -1]
    row = infer_one(model, tokenizer, entry, config, original, labels)
    expected = probability_trace(direct, row["generated_ids"][0], labels, original)
    assert row["probabilities"] == pytest.approx(expected["probabilities"], abs=1e-7)
    assert row["legal_label_mass"] == pytest.approx(expected["legal_label_mass"], abs=1e-7)
    assert row["input_ids"] == entry["input_ids"]
    assert len(row["steps"]) == row["generated_tokens"]
    assert row["effective_eos_ids"] == [1, 0]


def test_case_mapping_changes_probability_semantics_not_model_logits(tiny_inputs):
    model, tokenizer, entry, canonical = tiny_inputs
    config, original = generation_config(model.generation_config, tokenizer, 4, "model")
    baseline = infer_one(model, tokenizer, entry, config, original, canonical)
    changed = deepcopy(entry)
    changed["case"]["choice_labels"] = {"Y": "<t4>", "N": "<t2>", "A": "<t3>"}
    changed["label_token_ids"] = {"Y": 4, "N": 2, "A": 3}
    row = infer_one(model, tokenizer, changed, config, original, canonical)
    assert row["generated_ids"] == baseline["generated_ids"]
    assert row["probabilities"] == pytest.approx({"Y": baseline["probabilities"]["A"],
                                                 "N": baseline["probabilities"]["Y"],
                                                 "A": baseline["probabilities"]["N"]})
    assert "canonical_label_logits" not in row
    assert row["legal_label_mass"] == pytest.approx(baseline["legal_label_mass"], rel=1e-12, abs=1e-15)


def test_actual_qwen_stops_on_second_eos_only_when_enabled(tiny_inputs):
    model, tokenizer, entry, labels = tiny_inputs
    # With zero parameters every logit ties; deterministic argmax selects ID 0.
    # This creates a controlled stopping edge case, not a model-quality example.
    with torch.no_grad():
        for p in model.parameters():
            p.zero_()
    default, original = generation_config(model.generation_config, tokenizer, 4, "model")
    legacy, _ = generation_config(model.generation_config, tokenizer, 4, "legacy-tokenizer")
    a = infer_one(model, tokenizer, entry, default, original, labels)
    b = infer_one(model, tokenizer, entry, legacy, original, labels)
    assert a["generated_ids"] == [0] and a["stop_reason"] == "eos"
    assert b["generated_ids"] == [0, 0, 0, 0] and b["hit_output_cap"]
    assert b["ignored_model_eos_positions"] == [0, 1, 2, 3]
    assert a["probabilities"] == b["probabilities"]


def test_checkpoint_sampling_defaults_cannot_override_greedy_probe(tiny_inputs):
    model, tokenizer, entry, labels = tiny_inputs
    # The production checkpoint supplies sampling defaults. With tied logits,
    # greedy decoding must still emit EOS ID 0 immediately, not sample a token.
    model.generation_config.do_sample = True
    model.generation_config.temperature = 0.6
    model.generation_config.top_k = 20
    model.generation_config.top_p = 0.95
    with torch.no_grad():
        for p in model.parameters():
            p.zero_()
    config, original = generation_config(model.generation_config, tokenizer, 4, "model")
    row = infer_one(model, tokenizer, entry, config, original, labels)
    assert row["generated_ids"] == [0]
    assert row["stop_reason"] == "eos"
    assert config.do_sample is False


def test_run_receipt_preserves_tokens_and_refuses_overwrite(tiny_inputs, tmp_path):
    model, tokenizer, entry, labels = tiny_inputs
    config, original = generation_config(model.generation_config, tokenizer, 2, "model")
    destination = tmp_path / "run"
    report = run_cases(model, tokenizer, [entry], config, original, labels, destination,
                       {"run_kind": "infrastructure_smoke_random_weights"})
    assert report["status"] == "completed"
    assert report["predictions_sha256"] == sha256(destination / "predictions.jsonl")
    row = json.loads((destination / "predictions.jsonl").read_text())
    assert row["input_ids_digest"] == digest(row["input_ids"])
    assert row["run_kind"] == "infrastructure_smoke_random_weights"
    with pytest.raises(ValueError, match="fresh run"):
        run_cases(model, tokenizer, [entry], config, original, labels, destination,
                  {"run_kind": "infrastructure_smoke_random_weights"})


def test_snapshot_receipt_does_not_replace_checking_current_bytes(tmp_path):
    names = ["config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt", "model.safetensors.index.json", "weights.safetensors"]
    for name in names:
        (tmp_path / name).write_text("fixture")
    (tmp_path / "model.safetensors.index.json").write_text(json.dumps({"weight_map": {"weight": "weights.safetensors"}}))
    receipt = {"model": "fixture", "revision": "abc", "status": "verified",
               "files": [{"file": n, "algorithm": "sha256", "digest": sha256(tmp_path / n),
                          "bytes": (tmp_path / n).stat().st_size} for n in names]}
    lock = {"model": "fixture", "revision": "abc", "files": []}
    assert verify_snapshot(tmp_path, lock, receipt)["status"] == "verified_current_bytes"
    (tmp_path / "weights.safetensors").write_text("changed")  # Same byte count.
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_snapshot(tmp_path, lock, receipt)
