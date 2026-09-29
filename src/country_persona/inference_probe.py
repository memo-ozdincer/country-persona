"""Instrumented, bounded causal-LM inference. No training or semantic judging."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time

from .action_eval import VOTES, index_unique, parse_vote, validate_case
from .io import digest, sha256, write_json, write_jsonl


def eos_ids(value):
    ids = [value] if isinstance(value, int) and not isinstance(value, bool) else value
    if not isinstance(ids, (list, tuple)) or not ids or any(type(i) is not int or i < 0 for i in ids):
        raise ValueError("Expected a nonempty list of valid EOS token IDs")
    return list(dict.fromkeys(ids))


def verify_snapshot(root, lock, receipt):
    """Rehash local files against the existing author-revision verification receipt.

    This does not contact Hugging Face or download weights. The input receipt is
    itself pinned in the run record; an old successful receipt alone is not proof
    that the current files are unchanged.
    """
    root = Path(root)
    if receipt.get("status") != "verified" or (receipt.get("model"), receipt.get("revision")) != (lock["model"], lock["revision"]):
        raise ValueError("Snapshot receipt does not certify the locked model/revision")
    index = json.loads((root / "model.safetensors.index.json").read_text())
    required = {"config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json",
                "vocab.json", "merges.txt", "model.safetensors.index.json", *index["weight_map"].values()}
    entries = {f["file"]: f for f in receipt["files"]}
    if len(entries) != len(receipt["files"]) or required - set(entries):
        raise ValueError("Snapshot receipt has duplicates or lacks required files")
    results = []
    for name in sorted(required):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid snapshot member path")
        expected, path = entries[name], root / relative
        if path.stat().st_size != expected["bytes"]:
            raise ValueError(f"Snapshot byte count changed: {name}")
        if expected["algorithm"] == "sha256":
            observed = sha256(path)
        elif expected["algorithm"] == "git-blob-sha1":
            raw = path.read_bytes()
            observed = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        else:
            raise ValueError("Unsupported snapshot hash algorithm")
        if observed != expected["digest"]:
            raise ValueError(f"Snapshot checksum mismatch: {name}")
        results.append({"file": name, "algorithm": expected["algorithm"], "digest": observed, "bytes": path.stat().st_size})
    # The revision receipt and our separately pinned tokenizer/config must agree.
    for entry in lock["files"]:
        if sha256(root / Path(entry["path"]).name) != entry["sha256"]:
            raise ValueError("Snapshot differs from the independent tokenizer/config lock")
    return {"status": "verified_current_bytes", "model": lock["model"], "revision": lock["revision"],
            "path": str(root.resolve()), "files": results}


def generation_config(source_config, tokenizer, max_new_tokens, eos_policy):
    """Use declared greedy diagnostics and either checkpoint or legacy EOS IDs."""
    from transformers import GenerationConfig

    if type(max_new_tokens) is not int or max_new_tokens < 1:
        raise ValueError("max_new_tokens must be positive")
    original = eos_ids(source_config.eos_token_id)
    if eos_policy == "model":
        effective_eos = original
    elif eos_policy == "legacy-tokenizer":
        effective_eos = eos_ids(tokenizer.eos_token_id)
    else:
        raise ValueError("Unknown EOS policy")
    # Start from documented GenerationConfig defaults so no inherited forced
    # token, sampling or penalty processor can masquerade as raw probabilities.
    config = GenerationConfig(
        bos_token_id=source_config.bos_token_id, eos_token_id=effective_eos,
        pad_token_id=source_config.pad_token_id if source_config.pad_token_id is not None else tokenizer.pad_token_id,
        max_new_tokens=max_new_tokens, do_sample=False, num_beams=1,
        temperature=1.0, top_p=1.0, top_k=50, repetition_penalty=1.0,
        use_cache=True, output_logits=True, output_scores=True, return_dict_in_generate=True,
    )
    return config, original


def tokenize_cases(cases, tokenizer, template_kwargs, context_budget, max_new_tokens, case_cap):
    if not cases or len(cases) > case_cap:
        raise ValueError("Empty pack or explicit case cap exceeded")
    index_unique(cases, "case")
    label_ids = {v: tokenizer.encode(v, add_special_tokens=False) for v in VOTES}
    if any(len(ids) != 1 for ids in label_ids.values()) or len({ids[0] for ids in label_ids.values()}) != 3:
        raise ValueError("This probe requires distinct single-token canonical Y/N/A labels")
    result = []
    for case in cases:
        validate_case(case)
        if "chat_template_kwargs" in case and case["chat_template_kwargs"] != template_kwargs:
            raise ValueError("Case thinking/template mode differs from the model lock")
        ids = tokenizer.apply_chat_template(case["prompt"], tokenize=True, add_generation_prompt=True, **template_kwargs)
        if not ids or len(ids) + max_new_tokens > context_budget:
            raise ValueError(f"Full prompt plus output cap exceeds context budget: {case['id']}")
        if case.get("task") == "recorded_vote_prediction":
            choices = case.get("choice_labels", dict(zip(VOTES, VOTES)))
            case_label_ids = {v: tokenizer.encode(choices[v], add_special_tokens=False) for v in VOTES}
            if any(len(t) != 1 for t in case_label_ids.values()) or len({t[0] for t in case_label_ids.values()}) != 3:
                raise ValueError("Action choices must encode as distinct single tokens")
            rendered = tokenizer.apply_chat_template(case["prompt"], tokenize=False, add_generation_prompt=True, **template_kwargs)
            for label, token_id in case_label_ids.items():
                if tokenizer.encode(rendered + choices[label], add_special_tokens=False) != ids + token_id:
                    raise ValueError("Action tokenization changes at the completion boundary")
        entry = {"case": case, "input_ids": ids, "input_ids_digest": digest(ids)}
        if "choice_labels" in case:
            entry["label_token_ids"] = {v: t[0] for v, t in case_label_ids.items()}
        result.append(entry)
    return result, {label: ids[0] for label, ids in label_ids.items()}


def probability_trace(raw_logits, selected_id, legal_ids, stopping_ids, top_k=5):
    """Raw first-position token probabilities, not prose confidence or sequence probability."""
    import torch

    logits = raw_logits.detach().to(device="cpu", dtype=torch.float64)
    if logits.ndim != 1 or not torch.isfinite(logits).all():
        raise ValueError("Non-finite or malformed raw logits")
    log_z = torch.logsumexp(logits, dim=0)
    legal = logits[[legal_ids[label] for label in VOTES]]
    legal_log_z = torch.logsumexp(legal, dim=0)
    conditional = torch.softmax(legal, dim=0).tolist()
    log_mass = float(legal_log_z - log_z)
    top_values, top_ids = torch.topk(logits, min(top_k, logits.numel()))
    return {"raw_log_normalizer": float(log_z), "canonical_label_logits": {label: float(logits[token]) for label, token in legal_ids.items()},
            "probabilities": dict(zip(VOTES, conditional)),
            "probability_semantics": "conditional_on_legal_labels",
            "probability_position": "first_completion_token; exact single-token Y/N/A; no marginalization over whitespace or EOS",
            "legal_label_log_mass": log_mass, "legal_label_mass": float(torch.exp(torch.tensor(log_mass, dtype=torch.float64))),
            "selected_token_log_probability": float(logits[selected_id] - log_z),
            "eos_log_probabilities": {str(i): float(logits[i] - log_z) for i in stopping_ids},
            "top_tokens": [{"id": int(i), "log_probability": float(v - log_z)} for i, v in zip(top_ids, top_values)]}


def stop_trace(generated_ids, effective_eos, model_eos, max_new_tokens):
    if not generated_ids or len(generated_ids) > max_new_tokens:
        raise ValueError("Empty continuation or output exceeded its cap")
    if any(t in effective_eos for t in generated_ids[:-1]):
        raise ValueError("Generation continued after an effective EOS token")
    terminal = generated_ids[-1] in effective_eos
    if not terminal and len(generated_ids) < max_new_tokens:
        raise ValueError("Unexplained early stop; inspect generation settings")
    return {"stop_reason": "eos" if terminal else "max_new_tokens", "stop_token_id": generated_ids[-1] if terminal else None,
            "hit_output_cap": not terminal, "at_cap_boundary": len(generated_ids) == max_new_tokens,
            "ignored_model_eos_positions": [i for i, t in enumerate(generated_ids) if t in model_eos and t not in effective_eos]}


def repetition_trace(ids, output):
    """Mechanical diagnostics; repeated terms alone are not policy errors."""
    max_run, run, previous = 0, 0, None
    for token in ids:
        run = run + 1 if token == previous else 1
        max_run, previous = max(max_run, run), token
    grams = [tuple(ids[i:i + 8]) for i in range(max(0, len(ids) - 7))]
    sentences = [s.strip().casefold() for s in re.split(r"[.!?。！？\n]+", output) if len(s.strip()) >= 20]
    counts = Counter(sentences)
    return {"maximum_consecutive_token_run": max_run,
            "duplicate_8gram_fraction": (len(grams) - len(set(grams))) / len(grams) if grams else 0.0,
            "repeated_sentences_min_20_chars": {s: n for s, n in counts.items() if n > 1}}


def infer_one(model, tokenizer, tokenized, config, model_eos, label_ids):
    import torch

    case, input_ids = tokenized["case"], tokenized["input_ids"]
    label_ids = tokenized.get("label_token_ids", label_ids)
    device = next(model.parameters()).device
    ids = torch.tensor([input_ids], dtype=torch.long, device=device)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    started = time.perf_counter()
    with torch.inference_mode():
        # Transformers can replace explicitly supplied global defaults (including
        # do_sample=False) with checkpoint sampling defaults unless disabled here.
        generated = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids),
                                   generation_config=config, use_model_defaults=False)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    generation_seconds = time.perf_counter() - started
    trace_started = time.perf_counter()
    target = generated.sequences[0, len(input_ids):].tolist()
    if generated.sequences[0, :len(input_ids)].tolist() != input_ids:
        raise ValueError("Generation did not preserve the complete prompt")
    if len(generated.logits) != len(target) or len(generated.scores) != len(target):
        raise ValueError("Missing per-step logits/scores")
    effective_eos = eos_ids(config.eos_token_id)
    stops = stop_trace(target, effective_eos, model_eos, config.max_new_tokens)
    steps = []
    first = None
    for i, token in enumerate(target):
        raw, processed = generated.logits[i][0], generated.scores[i][0]
        # This runner promises unmodified greedy selection. Fail visibly if a
        # Transformers processor changes logits rather than reporting false semantics.
        if not torch.equal(raw, processed) or int(torch.argmax(raw)) != token:
            diagnostic = {"step": i, "raw_equals_processed": torch.equal(raw, processed),
                          "raw_argmax_1d": int(torch.argmax(raw)),
                          "raw_argmax_2d": int(torch.argmax(raw.unsqueeze(0), dim=-1)[0]),
                          "selected_token": token, "selected_raw_logit": float(raw[token]),
                          "raw_max_logit": float(raw.max()), "all_raw_logits_finite": bool(torch.isfinite(raw).all()),
                          "maximum_logit_ids_first_10": torch.nonzero(raw == raw.max()).flatten()[:10].tolist(),
                          "generated_ids": target, "output_with_special_tokens": tokenizer.decode(target, skip_special_tokens=False)}
            raise ValueError("Declared raw greedy decoding differs from actual generation: " + json.dumps(diagnostic))
        trace = probability_trace(raw, token, label_ids, sorted(set(model_eos + effective_eos)))
        if i == 0:
            first = trace
        steps.append({"step": i, "token_id": token, "token_text": tokenizer.decode([token], skip_special_tokens=False),
                      "log_probability": trace["selected_token_log_probability"],
                      "eos_log_probabilities": trace["eos_log_probabilities"], "top_tokens": trace["top_tokens"]})
    output = tokenizer.decode(target, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    raw_output = tokenizer.decode(target, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    row = {"id": case["id"], "case_sha256": case["case_sha256"],
           "response_id": digest([case["case_sha256"], target, config.to_dict()])[:24],
           "country": case["country"], "split_group": case["split_group"], "condition": case.get("condition"),
           "task": case.get("task", "legacy_text_generation"), "pair_id": case.get("pair_id"),
           "output": output, "output_with_special_tokens": raw_output,
           "input_ids": input_ids, "input_ids_digest": tokenized["input_ids_digest"], "generated_ids": target,
           "prompt_tokens": len(input_ids), "generated_tokens": len(target),
           "effective_eos_ids": effective_eos, "model_eos_ids": model_eos, "steps": steps,
           "generation_seconds": generation_seconds, "trace_processing_seconds": time.perf_counter() - trace_started,
           "generated_thinking_marker": any(t in raw_output for t in ("<think>", "</think>")),
           "repetition": repetition_trace(target, output), **stops}
    if case.get("task") == "recorded_vote_prediction":
        row.update(first)
        if "choice_labels" in case:
            row["choice_labels"] = case["choice_labels"]
            row["label_token_ids"] = label_ids
            row["choice_label_logits"] = row.pop("canonical_label_logits")
            row["probability_position"] = "first_completion_token; exact declared single-token choices mapped to Y/N/A; no whitespace or EOS marginalization"
        row["parsed_vote"] = parse_vote(output, case.get("choice_labels"))
    return row


def run_cases(model, tokenizer, tokenized_cases, config, model_eos, label_ids, output, metadata):
    output = Path(output)
    if output.exists():
        raise ValueError("Choose a fresh run directory; partial or completed runs are never overwritten")
    output.mkdir(parents=True)
    started = time.perf_counter()
    record = deepcopy(metadata)
    record.update(status="running", started_at=datetime.now(timezone.utc).isoformat(), expected_cases=len(tokenized_cases),
                  generation_config=config.to_dict(), generation_call_kwargs={"use_model_defaults": False},
                  model_eos_ids=model_eos, label_token_ids=label_ids,
                  completed_cases=0, completed_ids=[])
    write_json(output / "run.json", record)
    rows = []
    model.eval()
    try:
        for entry in tokenized_cases:
            row = infer_one(model, tokenizer, entry, config, model_eos, label_ids)
            row["run_kind"] = metadata["run_kind"]
            rows.append(row)
            write_jsonl(output / "predictions.jsonl", rows)
            record.update(completed_cases=len(rows), completed_ids=[r["id"] for r in rows],
                          elapsed_inference_and_trace_seconds=time.perf_counter() - started)
            write_json(output / "run.json", record)
            print(json.dumps({"completed": len(rows), "expected": len(tokenized_cases), "id": row["id"],
                              "task": row["task"], "stop_reason": row["stop_reason"],
                              "prompt_tokens": row["prompt_tokens"], "generated_tokens": row["generated_tokens"]}), flush=True)
        record.update(status="completed", finished_at=datetime.now(timezone.utc).isoformat(),
                      predictions_sha256=sha256(output / "predictions.jsonl"),
                      prompt_tokens=sum(r["prompt_tokens"] for r in rows), generated_tokens=sum(r["generated_tokens"] for r in rows),
                      generation_seconds=sum(r["generation_seconds"] for r in rows),
                      trace_processing_seconds=sum(r["trace_processing_seconds"] for r in rows))
        write_json(output / "run.json", record)
    except BaseException as exc:
        record.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                      finished_at=datetime.now(timezone.utc).isoformat())
        write_json(output / "run.json", record)
        raise
    return record
