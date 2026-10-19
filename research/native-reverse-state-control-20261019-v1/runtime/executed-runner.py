"""Two inspected common-draft revisions; no training or peer interaction."""
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--gpu-uuid", required=True)
    args = p.parse_args()
    pack, out = args.pack.resolve(), args.output.resolve()
    out.mkdir(exist_ok=False)
    launch = dict(status="started", identity=identity(), runtime=locked_runtime(),
                  output=str(out), production_generation_records=0, production_optimizer_updates=0,
                  code_sha256=sha256(Path(__file__)))
    write_json(out / "launch.json", launch)
    try:
        release = json.loads((pack / "release.json").read_text())
        for name, expected in release["files_sha256"].items():
            assert sha256(ROOT / name) == expected, name
        cfg = json.loads((pack / "config.json").read_text())
        row = json.loads((pack / "example.json").read_text())
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(cfg["model_path"], local_files_only=True)
        assert all("<|im_end|>" not in m["content"] and "<|im_start|>" not in m["content"] for m in row["messages"])
        prefix = tok.apply_chat_template(row["messages"], tokenize=True, return_dict=False,
                                        add_generation_prompt=True, enable_thinking=False)
        assert len(prefix) + 2048 <= 8192
        write_json(out / "actual-input.json", dict(**row, prefix_ids=prefix, prefix_sha256=ids_digest(prefix)))
        launch.update(release_sha256=sha256(pack / "release.json"),
                      actual_input_sha256=sha256(out / "actual-input.json"), gpu=current_gpu(args.gpu_uuid))
        assert launch["gpu"]["name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_uuid
        launch["model_verification"] = verify_model(cfg)
        current_gpu(args.gpu_uuid)
        write_json(out / "launch.json", launch)
        shutil.copyfile(__file__, out / "executed-runner.py")
        import torch
        from transformers import Qwen3_5ForCausalLM, GenerationConfig
        torch.manual_seed(42)
        model, loading = Qwen3_5ForCausalLM.from_pretrained(cfg["model_path"], local_files_only=True,
            dtype=torch.bfloat16, attn_implementation="sdpa", output_loading_info=True)
        assert not loading["missing_keys"] and not loading["mismatched_keys"] and not loading["error_msgs"]
        model = model.to("cuda:0").eval()
        decoder = GenerationConfig(do_sample=False, max_new_tokens=2048, use_cache=True,
            eos_token_id=tok.convert_tokens_to_ids("<|im_end|>"), pad_token_id=tok.pad_token_id)
        assert decoder.to_dict() == json.loads((ROOT / cfg["decoder_path"]).read_text())
        write_json(out / "decoder.json", decoder.to_dict())

        def owned():
            live = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"], text=True)
            assert {int(s.split(',')[1]) for s in live.splitlines() if s.split(',')[0].strip() == args.gpu_uuid} == {os.getpid()}

        def generate(arm):
            owned()
            dest = out / arm; dest.mkdir(exist_ok=False)
            x = torch.tensor([prefix], device="cuda:0"); start = time.perf_counter()
            with torch.inference_mode():
                y = model.generate(input_ids=x, attention_mask=torch.ones_like(x), generation_config=decoder)
            torch.cuda.synchronize(); ids = y[0, x.shape[1]:].tolist()
            record = dict(id=row["id"], arm=arm, prefix_sha256=ids_digest(prefix), output_ids=ids,
                output_raw=tok.decode(ids, skip_special_tokens=False), output_display=tok.decode(ids, skip_special_tokens=True),
                generated_tokens=len(ids), generation_seconds=time.perf_counter()-start,
                at_cap=len(ids)==2048 and ids[-1]!=decoder.eos_token_id)
            (dest / "responses.jsonl").write_text(json.dumps(record, ensure_ascii=False)+"\n")
            launch["production_generation_records"] += 1
            write_json(out / "launch.json", launch)

        generate("base")
        launch["status"] = "awaiting_base_inspection"; write_json(out / "launch.json", launch)
        print('Awaiting explicit adapter or exit operation; idle timeout300seconds', flush=True)
        if select.select([sys.stdin], [], [], 300)[0]:
            command = json.loads(sys.stdin.readline())
            assert command["operation"] in {"adapter", "exit"}
            if command["operation"] == "adapter":
                review = json.loads((out / "base/inspection.json").read_text())
                assert review["complete_outputs_read"] is True
                assert review["responses_sha256"] == sha256(out / "base/responses.jsonl")
                assert review["rubric_sha256"] == sha256(pack / "rubric.json")
                owned()
                from peft import PeftModel
                from country_persona.training_checks import adapter_snapshot, tensor_state_digest
                for name, expected in cfg["adapter_files_sha256"].items():
                    assert sha256(ROOT / cfg["adapter_path"] / name) == expected
                model = PeftModel.from_pretrained(model, ROOT / cfg["adapter_path"], is_trainable=False).eval()
                launch["adapter_digest"] = tensor_state_digest(adapter_snapshot(model))
                assert launch["adapter_digest"] == cfg["adapter_tensor_digest"]
                generate("adapter")
                assert tensor_state_digest(adapter_snapshot(model)) == launch["adapter_digest"]
        launch.update(status="completed", process_state="exiting_normally")
        write_json(out / "launch.json", launch)
    except Exception as exc:
        launch.update(status="failed", exception=repr(exc), traceback=traceback.format_exc())
        write_json(out / "launch.json", launch)
        raise


if __name__ == "__main__":
    main()
