"""One base evaluation with quoted record boundaries escaped from native chat.

Preserves the October 17 release and runner. Only documentary boundary notation
changes inside the native user message; scene, speeches, requested role, weights,
decoder and reference targets stay fixed. No fitting or automatic chaining.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import sha256, write_json
from country_persona.meeting_sequence import END
from country_persona.scenario_sft import load_pack, locked_runtime, evaluate, ids_digest
from run_aurora_qwen35_smoke import identity, current_gpu, verify_model

RELEASE = ROOT / "research/scenario-role-sft-20261017-v1"


def derive(row, tokenizer):
    messages = [dict(m) for m in row["native_messages"]]
    before = messages[0]["content"]
    messages[0]["content"] = before.replace(END, "[END OF RECORDED TURN]")
    if messages[0]["content"].replace("[END OF RECORDED TURN]", END) != before:
        raise ValueError("Documentary text changed beyond boundary notation")
    ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                       enable_thinking=False, return_dict=False)
    if isinstance(ids, dict):
        ids = ids["input_ids"]
    eos = tokenizer.convert_tokens_to_ids(END)
    if END in messages[0]["content"] or ids.count(eos) != 1 or len(ids) + 2048 > 8192:
        raise ValueError("Embedded chat boundary or excessive context")
    completion = tokenizer.encode(row["completion"], add_special_tokens=False)
    together = tokenizer.encode(tokenizer.decode(ids, skip_special_tokens=False) + row["completion"],
                                add_special_tokens=False)
    if together != ids + completion:
        raise ValueError("Native response boundary is not prefix-stable")
    return {**row, "native_prefix_ids": ids}, dict(id=row["id"], messages=messages, prefix_ids=ids,
        prefix_ids_sha256=ids_digest(ids), original_prefix_ids_sha256=ids_digest(row["native_prefix_ids"]),
        original_end_tokens=row["native_prefix_ids"].count(eos), corrected_end_tokens=ids.count(eos),
        documentary_boundary_replacements=before.count(END), documentary_text_otherwise_identical=True,
        target_sha256=row["target_sha256"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--gpu-uuid")
    p.add_argument("--preflight-only", action="store_true")
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    launch = dict(identity=identity(), runtime=locked_runtime(), status="started", arm="base",
        format="native_with_escaped_record_boundaries", production_model_calls=0, production_optimizer_updates=0,
        code_sha256=sha256(Path(__file__)), output=str(out))
    write_json(out / "launch.json", launch)
    try:
        config_path = RELEASE / "fit-config.json"
        config = json.loads(config_path.read_text())
        for key in ("code_sha256", "artifact_sha256"):
            for name, expected in config[key].items():
                if sha256(ROOT / name) != expected:
                    raise ValueError("Frozen parent implementation/artifact changed: " + name)
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(config["model_path"], local_files_only=True)
        _, held = load_pack(ROOT, RELEASE / "pack", tokenizer)
        pairs = [derive(row, tokenizer) for row in held]
        rows, audit = [p[0] for p in pairs], [p[1] for p in pairs]
        write_json(out / "actual-inputs.json", audit)
        launch.update(parent_fit_config_sha256=sha256(config_path), actual_inputs_sha256=sha256(out / "actual-inputs.json"))
        if a.preflight_only:
            launch.update(status="preflight_complete", result="Two documentary-only boundary replacements per case; native end count 3 to 1; identical target bytes and stable completion mask.")
        else:
            if not a.gpu_uuid:
                raise ValueError("Explicit free GPU UUID required")
            launch["gpu"] = current_gpu(a.gpu_uuid)
            if launch["gpu"]["name"] != "NVIDIA RTX PRO 6000 Blackwell Server Edition":
                raise ValueError("Hardware comparison changed")
            os.environ["CUDA_VISIBLE_DEVICES"] = a.gpu_uuid
            launch["model_verification"] = verify_model(config)
            current_gpu(a.gpu_uuid)
            write_json(out / "launch.json", launch)
            import torch
            from transformers import Qwen3_5ForCausalLM
            torch.manual_seed(42)
            model = Qwen3_5ForCausalLM.from_pretrained(config["model_path"], local_files_only=True,
                dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda:0")
            result = evaluate(model, tokenizer, rows, out, "cuda:0", native=True)
            write_json(out / "evaluation-result.json", result)
            launch.update(status="completed", result=result, production_model_calls=result["calls"])
        write_json(out / "launch.json", launch)
        print(json.dumps({k: launch[k] for k in ["status", "format", "production_model_calls"]}))
    except Exception as exc:
        path = out / "responses.jsonl"
        launch.update(status="failed", exception=repr(exc), traceback=traceback.format_exc(),
                      production_model_calls=len(path.read_text().splitlines()) if path.exists() else 0)
        write_json(out / "launch.json", launch)
        raise


if __name__ == "__main__":
    main()
