"""Two base answers, then only an explicit saved-adapter comparison.

Single verified model load, no optimization, no automatic experiment queue.
The process exits after five idle minutes or an explicit exit command.
"""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import sha256, write_json
from country_persona.scenario_sft import ids_digest, locked_runtime
from run_aurora_qwen35_smoke import current_gpu, identity, verify_model

PACK = ROOT / "research/grounded-role-20261019-v1"
FIT = ROOT / "runs/scenario-fit128-20261018-v1"


def prepare(tokenizer):
    rows = json.loads((PACK / "examples.json").read_text())
    assert len(rows) == 2 and {r["country"] for r in rows} == {"IND", "GBR"}
    for row in rows:
        ids = tokenizer.apply_chat_template(row["messages"], tokenize=True,
            return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert len(ids) + 2048 <= 8192
        assert ids.count(tokenizer.convert_tokens_to_ids("<|im_end|>")) == 2
        assert ids.count(tokenizer.convert_tokens_to_ids("<|im_start|>")) == 3
        row["prefix_ids"] = ids
        row["prefix_sha256"] = ids_digest(ids)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gpu-uuid")
    parser.add_argument("--preflight-only", action="store_true")
    a = parser.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    launch = dict(status="started", identity=identity(), runtime=locked_runtime(),
        output=str(out), code_sha256=sha256(Path(__file__)),
        production_generated_answers=0, production_optimizer_updates=0,
        independent_review_complete=False)
    write_json(out / "launch.json", launch)
    try:
        release = json.loads((PACK / "release.json").read_text())
        for path, expected in release["files_sha256"].items():
            if sha256(ROOT / path) != expected:
                raise ValueError("Frozen source/code/pack changed: " + path)
        config = json.loads((ROOT / "research/scenario-role-sft-20261017-v1/fit-config.json").read_text())
        launch["parent_fit_config_sha256"] = sha256(ROOT / "research/scenario-role-sft-20261017-v1/fit-config.json")
        launch["release_sha256"] = sha256(PACK / "release.json")
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(config["model_path"], local_files_only=True)
        rows = prepare(tok)
        write_json(out / "actual-inputs.json", rows)
        launch["actual_inputs_sha256"] = sha256(out / "actual-inputs.json")
        if a.preflight_only:
            launch.update(status="preflight_complete", prefix_tokens=[len(r["prefix_ids"]) for r in rows],
                          no_embedded_native_record_delimiters=True, full_context_fits=True)
            write_json(out / "launch.json", launch)
            print(json.dumps(launch), flush=True)
            return
        if not a.gpu_uuid:
            raise ValueError("Explicit free GPU UUID required")
        launch["gpu"] = current_gpu(a.gpu_uuid)
        assert launch["gpu"]["name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
        os.environ["CUDA_VISIBLE_DEVICES"] = a.gpu_uuid
        launch["model_verification"] = verify_model(config)
        current_gpu(a.gpu_uuid)
        write_json(out / "launch.json", launch)
        shutil.copyfile(__file__, out / "executed-runner.py")
        import torch
        from transformers import GenerationConfig, Qwen3_5ForCausalLM
        torch.manual_seed(42)
        assert torch.cuda.device_count() == 1 and torch.cuda.is_bf16_supported()
        model, loading = Qwen3_5ForCausalLM.from_pretrained(config["model_path"], local_files_only=True,
            dtype=torch.bfloat16, attn_implementation="sdpa", output_loading_info=True)
        assert not loading["missing_keys"] and not loading["mismatched_keys"] and not loading["error_msgs"]
        model = model.to("cuda:0").eval()
        versions = {n: p._version for n, p in model.named_parameters()}
        generation = GenerationConfig(do_sample=False, max_new_tokens=2048, use_cache=True,
            eos_token_id=tok.convert_tokens_to_ids("<|im_end|>"), pad_token_id=tok.pad_token_id)
        write_json(out / "decoder.json", generation.to_dict())
        stages = []

        def evaluate(arm):
            target = out / arm
            target.mkdir(exist_ok=False)
            with (target / "responses.jsonl").open("x") as f:
                for row in rows:
                    x = torch.tensor([row["prefix_ids"]], device="cuda:0")
                    start = time.perf_counter()
                    with torch.inference_mode():
                        result = model.generate(input_ids=x, attention_mask=torch.ones_like(x), generation_config=generation)
                    torch.cuda.synchronize()
                    ids = result[0, x.shape[1]:].tolist()
                    record = dict(id=row["id"], country=row["country"], arm=arm,
                        prefix_sha256=row["prefix_sha256"], prefix_tokens=len(row["prefix_ids"]),
                        output_ids=ids, output_raw=tok.decode(ids, skip_special_tokens=False),
                        output_display=tok.decode(ids, skip_special_tokens=True), generated_tokens=len(ids),
                        generation_seconds=time.perf_counter()-start,
                        at_cap=len(ids)==2048 and ids[-1] != generation.eos_token_id)
                    f.write(json.dumps(record, ensure_ascii=False)+"\n"); f.flush()
                    launch["production_generated_answers"] += 1
                    write_json(out / "launch.json", launch)
            if arm == "base":
                assert all(p._version == versions[n] for n, p in model.named_parameters())
            stages.append(arm)
            write_json(target / "result.json", dict(calls=2, responses_sha256=sha256(target / "responses.jsonl"),
                actual_inputs_sha256=launch["actual_inputs_sha256"], decoder_sha256=sha256(out / "decoder.json"),
                rubric_sha256=sha256(PACK / "rubric.json"), quality="ungraded; full reading required"))

        evaluate("base")
        while True:
            launch.update(status="awaiting_explicit_operation", completed_stages=stages)
            write_json(out / "launch.json", launch)
            print(json.dumps(dict(state="awaiting_explicit_operation", stages=stages, idle_timeout_seconds=300)), flush=True)
            if not select.select([sys.stdin], [], [], 300)[0]:
                break
            line = sys.stdin.readline()
            if not line:
                break
            command = json.loads(line)
            if command.get("operation") == "exit":
                break
            if command.get("operation") != "adapter" or stages != ["base"]:
                raise ValueError("Only one explicitly requested adapter comparison or exit is supported")
            review = json.loads((out / "base/inspection.json").read_text())
            assert review["responses_sha256"] == sha256(out / "base/responses.jsonl")
            assert review["rubric_sha256"] == sha256(PACK / "rubric.json")
            assert review["complete_outputs_read"] is True and review["decision"] == "compare_saved_adapter"
            live = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"], text=True)
            pids = {int(line.split(',')[1]) for line in live.splitlines() if line.split(',')[0].strip() == a.gpu_uuid}
            assert pids == {os.getpid()}, "GPU occupancy changed; do not run another stage"
            training = json.loads((FIT / "training-result.json").read_text())
            for name, expected in training["serialization"]["files_sha256"].items():
                assert sha256(FIT / "adapter" / name) == expected
            from peft import PeftModel
            from country_persona.training_checks import adapter_snapshot, tensor_state_digest
            model = PeftModel.from_pretrained(model, FIT / "adapter").eval()
            state = tensor_state_digest(adapter_snapshot(model))
            assert state == training["update"]["final_adapter_digest"]
            launch.update(saved_adapter_digest=state, adapter_training_result_sha256=sha256(FIT / "training-result.json"))
            write_json(out / "launch.json", launch)
            evaluate("adapter")
            assert tensor_state_digest(adapter_snapshot(model)) == state
        launch.update(status="completed", process_state="exiting_normally", completed_stages=stages)
        write_json(out / "launch.json", launch)
    except Exception as exc:
        launch.update(status="failed", exception=repr(exc), traceback=traceback.format_exc())
        write_json(out / "launch.json", launch)
        raise


if __name__ == "__main__":
    main()
