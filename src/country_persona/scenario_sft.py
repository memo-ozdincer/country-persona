"""Auditable response-only SFT and matched evaluation for authentic meeting turns.

No automatic experiment chaining or resource waiting. CPU probes exercise these
same loss/optimizer/save functions on a randomly initialized tiny Qwen3.5.
"""
from collections import Counter
import importlib.metadata
import json
import math
from pathlib import Path
import random

from .io import read_jsonl, sha256, write_json
from .meeting_sequence import END, digest, render, tokenize_example


def ids_digest(ids):
    return digest(json.dumps(ids, separators=(",", ":")))


def schedule(rows, presentations, seed):
    if presentations < 1 or not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Invalid exposure schedule")
    rng, result = random.Random(seed), []
    for epoch in range(presentations):
        order = list(range(len(rows)))
        rng.shuffle(order)
        start = len(result)
        result.extend({"step": start + i + 1, "epoch": epoch + 1,
                       "row": index, "id": rows[index]["id"]} for i, index in enumerate(order))
    return result


def audit_trace(path, rows, presentations, seed):
    events = schedule(rows, presentations, seed)
    records = list(read_jsonl(path))
    if len(records) != len(events):
        raise ValueError("Missing or extra optimizer trace entries")
    for record, event in zip(records, events):
        row = rows[event["row"]]
        if any(record[k] != v for k, v in event.items()):
            raise ValueError("Trace order, identity or exposure changed")
        if (record["input_ids_sha256"] != ids_digest(row["input_ids"])
                or record["labels_sha256"] != ids_digest(row["labels"])
                or record["sequence_tokens"] != len(row["input_ids"])
                or record["supervised_tokens"] != row["supervised_tokens"]):
            raise ValueError("Trace input, mask or token accounting changed")
        gradient = record["gradient"]
        if (not math.isfinite(record["loss"]) or not gradient["finite"]
                or not math.isfinite(record["gradient_l2_before_clipping"])
                or not 0 < gradient["gradient_l2_after_clipping"] <= 1.00001):
            raise ValueError("Nonfinite, absent or unclipped optimizer gradient")
    return dict(entries=len(records), source_inputs_masks_schedule_and_finite_gradients_replayed=True)


def check_row(row, tokenizer, sources, max_length=8192):
    source = sources[row["source"]]
    p = row["provenance"]
    a, b = p["window"]
    if not 0 <= a < b <= len(source) or digest(source) != p["source_sha256"]:
        raise ValueError("Changed source or window")
    meeting = dict(scenario=row["scenario"], source_sha256=digest(source[a:b]), turns=p["turns"])
    expected = render(meeting, source[a:b], len(p["turns"]) - 1)
    for key in ("prefix", "body", "completion"):
        if row[key] != expected[key]:
            raise ValueError("Rendered source mismatch: " + key)
    target = p["turns"][-1]
    if row["country"] != target["country"] or p["target"] != [a + target["content_start"], b]:
        raise ValueError("Requested country/source target mismatch")
    if row["body"] in row["prefix"] or row["completion"] != row["body"] + END:
        raise ValueError("Target leaked or end marker changed")
    actual = tokenize_example(tokenizer, expected, max_length)
    if any(row[k] != v for k, v in actual.items()):
        raise ValueError("Stored token IDs or response-only mask differ")
    if row["prefix_sha256"] != digest(row["prefix"]) or row["target_sha256"] != digest(row["body"]):
        raise ValueError("Changed input/target digest")
    native = tokenizer.apply_chat_template(row["native_messages"], tokenize=True, add_generation_prompt=True,
                                          enable_thinking=False, return_dict=False)
    if isinstance(native, dict):
        native = native["input_ids"]
    if native != row["native_prefix_ids"]:
        raise ValueError("Native-chat control changed")
    return actual


def load_pack(root, pack, tokenizer):
    root, pack = Path(root), Path(pack)
    release = json.loads((pack / "release.json").read_text())
    for name, value in release["files_sha256"].items():
        if sha256(pack / name) != value:
            raise ValueError("Changed pack file: " + name)
    lock = json.loads((pack / "tokenizer-lock.json").read_text())
    for name, value in lock["files_sha256"].items():
        if sha256(Path(lock["model_path"]) / name) != value:
            raise ValueError("Changed tokenizer/config lock: " + name)
    source_dir = root / release["sources"]
    for name, value in release["source_files_sha256"].items():
        if sha256(source_dir / name) != value:
            raise ValueError("Changed extraction: " + name)
    pins = json.loads((source_dir / "sources.json").read_text())["sources"]
    sources = {}
    for pin in pins:
        if sha256(root / pin["pdf"]) != pin["pdf_sha256"]:
            raise ValueError("Changed primary PDF")
        sources[pin["id"]] = (source_dir / pin["source"]).read_text()
    rows = list(read_jsonl(pack / "train.jsonl")) + list(read_jsonl(pack / "eval.jsonl"))
    if len(rows) != 6 or len({r["id"] for r in rows}) != 6:
        raise ValueError("Expected the frozen four-train/two-development examples")
    for r in rows:
        check_row(r, tokenizer, sources)
    fitting, held = [r for r in rows if r["split"] == "train"], [r for r in rows if r["split"] == "eval"]
    if (len(fitting), len(held)) != (4, 2) or {r["source"] for r in fitting} & {r["source"] for r in held}:
        raise ValueError("Whole-episode fit/evaluation contamination")
    return fitting, held


def locked_runtime():
    expected = {"torch": "2.8.0", "transformers": "5.17.0", "peft": "0.21.1"}
    actual = {k: importlib.metadata.version(k) for k in expected}
    if any(actual[k].split("+")[0] != v for k, v in expected.items()):
        raise ValueError("Runtime differs from the pinned smoke environment: " + str(actual))
    return actual


def completion_loss(model, row, device):
    """Causal shift: logit at prefix-1 predicts the FIRST speech token.

    Compute only target-position vocabulary logits, retaining all context for
    attention. All context/header tokens have labels -100; no padding or packing.
    """
    import torch
    ids, labels, prefix = row["input_ids"], row["labels"], row["prefix_tokens"]
    if not 0 < prefix < len(ids) or labels != [-100] * prefix + ids[prefix:]:
        raise ValueError("Loss received a corrupt response-only mask")
    x = torch.tensor([ids], dtype=torch.long, device=device)
    logits = model(input_ids=x, attention_mask=torch.ones_like(x), use_cache=False,
                   logits_to_keep=len(ids) - prefix + 1).logits[:, :-1, :]
    targets = x[:, prefix:]
    if logits.shape[1] != targets.shape[1]:
        raise ValueError("Causal shift changed target count")
    return torch.nn.functional.cross_entropy(logits.float().reshape(-1, logits.shape[-1]), targets.reshape(-1))


def train_loop(model, rows, *, presentations, seed, learning_rate, output, device):
    import torch
    from .training_checks import adapter_snapshot, check_adapter_update, finite_gradient_summary
    output = Path(output)
    events = schedule(rows, presentations, seed)
    write_json(output / "schedule.json", events)
    initial = adapter_snapshot(model)
    if any(p.requires_grad and "lora_" not in n for n, p in model.named_parameters()):
        raise ValueError("This readable-marker arm may train only fresh LoRA tensors")
    base_versions = {n: p._version for n, p in model.named_parameters() if not p.requires_grad}
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=learning_rate, weight_decay=0.0)
    model.train()
    seen, sequence_tokens, supervised_tokens = Counter(), 0, 0
    with (output / "optimization.jsonl").open("x") as trace:
        for event in events:
            row = rows[event["row"]]
            optimizer.zero_grad(set_to_none=True)
            loss = completion_loss(model, row, device)
            if not torch.isfinite(loss):
                raise FloatingPointError("Nonfinite loss")
            loss.backward()
            before = finite_gradient_summary(model)
            if before["gradient_l2_after_clipping"] <= 0:
                raise ValueError("Zero gradient")
            norm = torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0,
                                                   error_if_nonfinite=True)
            after = finite_gradient_summary(model)
            optimizer.step()
            seen[row["id"]] += 1
            sequence_tokens += len(row["input_ids"])
            supervised_tokens += row["supervised_tokens"]
            trace.write(json.dumps({**event, "loss": float(loss.detach()), "sequence_tokens": len(row["input_ids"]),
                "supervised_tokens": row["supervised_tokens"], "input_ids_sha256": ids_digest(row["input_ids"]),
                "labels_sha256": ids_digest(row["labels"]), "gradient_l2_before_clipping": float(norm),
                "gradient": after}) + "\n")
            trace.flush()
    if seen != Counter({r["id"]: presentations for r in rows}):
        raise ValueError("Exposure differs from the frozen schedule")
    if any(p._version != base_versions[n] for n, p in model.named_parameters() if n in base_versions):
        raise ValueError("A frozen base tensor was mutated")
    update = check_adapter_update(initial, adapter_snapshot(model))
    adapter = output / "adapter"
    model.save_pretrained(adapter, safe_serialization=True)
    from .training_checks import verify_saved_adapter
    probe = torch.tensor([rows[0]["input_ids"][:24]], device=device)
    saved = verify_saved_adapter(model, adapter, probe, atol=1e-5, rtol=1e-5)
    result = dict(steps=len(events), presentations=dict(seen), sequence_tokens=sequence_tokens,
                  supervised_tokens=supervised_tokens, objective="equal-example response-only mean causal CE",
                  batch_size=1, gradient_accumulation=1, base_tensor_versions_unchanged=True,
                  update=update, serialization=saved, trace_sha256=sha256(output / "optimization.jsonl"))
    result["trace_replay"] = audit_trace(output / "optimization.jsonl", rows, presentations, seed)
    write_json(output / "training-result.json", result)
    return result


def role_counterfactual(row, tokenizer, partner):
    """Change only requested country/representative; retain the actual past."""
    from .meeting_sequence import header
    original = row["provenance"]["turns"][-1]
    replacement = {**original, "country": partner["country"], "representative": partner["representative"]}
    if not row["prefix"].endswith(header(original)):
        raise ValueError("Missing requested-role boundary")
    prefix = row["prefix"][:-len(header(original))] + header(replacement)
    return {**row, "prefix": prefix,
            "diagnostic_requested_country": partner["country"],
            **tokenize_example(tokenizer, dict(prefix=prefix, completion=row["completion"]))}


def evaluate(model, tokenizer, rows, output, device, native=False, max_new_tokens=2048):
    import torch
    from transformers import GenerationConfig
    from .meeting_sequence import header
    output = Path(output)
    model.eval()
    records = []
    with (output / "responses.jsonl").open("x") as trace:
        for row in rows:
            prefix_ids = row["native_prefix_ids"] if native else row["input_ids"][:row["prefix_tokens"]]
            if len(prefix_ids) + max_new_tokens > 8192:
                raise ValueError("Generation budget would truncate input")
            # The gold completion is NEVER passed to generate.
            x = torch.tensor([prefix_ids], device=device)
            config = GenerationConfig(do_sample=False, max_new_tokens=max_new_tokens,
                eos_token_id=tokenizer.convert_tokens_to_ids(END), pad_token_id=tokenizer.pad_token_id, use_cache=True)
            with torch.inference_mode():
                generated = model.generate(input_ids=x, attention_mask=torch.ones_like(x), generation_config=config)
                output_ids = generated[0, x.shape[1]:].tolist()
                loss_row = row
                partner = next(r["provenance"]["turns"][-1] for r in rows if r["source"] == row["source"] and r["country"] != row["country"])
                wrong = role_counterfactual(row, tokenizer, partner)
                if native:
                    # Native continuation includes the pre-opened assistant channel.
                    body_ids = tokenizer.encode(row["completion"], add_special_tokens=False)
                    loss_row = {**row, "input_ids": prefix_ids + body_ids,
                                "labels": [-100] * len(prefix_ids) + body_ids, "prefix_tokens": len(prefix_ids)}
                nll = float(completion_loss(model, loss_row, device))
                wrong_nll = None if native else float(completion_loss(model, wrong, device))
            record = dict(id=row["id"], prefix_ids=prefix_ids, output_ids=output_ids,
                input_sha256=ids_digest(prefix_ids), output_raw=tokenizer.decode(output_ids, skip_special_tokens=False),
                output_display=tokenizer.decode(output_ids, skip_special_tokens=True),
                at_cap=len(output_ids) == max_new_tokens and output_ids[-1] != config.eos_token_id,
                generated_tokens=len(output_ids), target_nll=nll, wrong_role_target_nll=wrong_nll,
                correct_role_advantage=None if native else wrong_nll - nll,
                wrong_role_prefix_ids=None if native else wrong["input_ids"][:wrong["prefix_tokens"]],
                mode="native_chat" if native else "readable_sequence", quality_grade=None)
            trace.write(json.dumps(record, ensure_ascii=False) + "\n")
            trace.flush()
            records.append(record)
    return dict(calls=len(records), responses_sha256=sha256(output / "responses.jsonl"),
                quality="ungraded; inspect complete raw outputs and source-backed rubric before any dependent run")
