"""Count full prompts with the locked tokenizer; never truncate or run a model."""
import argparse
import json
from pathlib import Path
from transformers import AutoTokenizer

from country_persona.action_eval import VOTES, validate_case
from country_persona.io import read_jsonl, sha256, write_json


def preflight(pack, lock_path, prompt_budget):
    lock = json.loads(lock_path.read_text())
    for item in lock["files"]:
        if sha256(item["path"]) != item["sha256"]:
            raise ValueError(f"Tokenizer/model config checksum mismatch: {item['path']}")
    manifest = json.loads((pack / "manifest.json").read_text())
    if sha256(pack / "cases.jsonl") != manifest["files_sha256"]["cases.jsonl"]:
        raise ValueError("Pack case-file hash mismatch")
    tokenizer = AutoTokenizer.from_pretrained(lock["tokenizer_path"], local_files_only=True)
    rows = []
    for case in read_jsonl(pack / "cases.jsonl"):
        validate_case(case)
        tokens = tokenizer.apply_chat_template(case["prompt"], tokenize=True, add_generation_prompt=True,
                                                **lock["chat_template_kwargs"])
        rows.append({"id": case["id"], "case_sha256": case["case_sha256"], "country": case["country"],
                     "split_group": case["split_group"], "prompt_tokens": len(tokens), "over_budget": len(tokens) > prompt_budget})
    return {"status": "tokenizer_only_no_model_inference", "model": lock["model"], "revision": lock["revision"],
            "model_lock_sha256": sha256(lock_path), "chat_template_kwargs": lock["chat_template_kwargs"],
            "case_file_sha256": sha256(pack / "cases.jsonl"), "prompt_budget": prompt_budget,
            "prompt_tokens_total": sum(r["prompt_tokens"] for r in rows),
            "prompt_tokens_min": min(r["prompt_tokens"] for r in rows), "prompt_tokens_max": max(r["prompt_tokens"] for r in rows),
            "over_budget_cases": sum(r["over_budget"] for r in rows),
            "over_budget_meeting_groups": len({r["split_group"] for r in rows if r["over_budget"]}),
            "label_token_ids": {v: tokenizer.encode(v, add_special_tokens=False) for v in VOTES},
            "decoding_requirements": ["Use full prompts or explicitly revise the context budget; never silently truncate drafts.",
                                      "Log effective EOS IDs, generation configuration, raw token IDs and stop reasons.",
                                      "Report legal-label probability mass and conditional probabilities separately from unconstrained generation validity."],
            "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--model-lock", type=Path, default=Path("configs/posttraining/model.lock.json"))
    parser.add_argument("--prompt-budget", type=int, default=4096)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = preflight(args.pack, args.model_lock, args.prompt_budget)
    write_json(args.output, report)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
