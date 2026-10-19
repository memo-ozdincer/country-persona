"""One shared source reader, then writer pair only after explicit inspection.

No fitting, no hand-edited plan, no new government authority. All actual inputs
and raw model outputs are retained. The model exits after five idle minutes.
"""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import sha256, write_json
from country_persona.scenario_sft import locked_runtime, ids_digest
from run_aurora_qwen35_smoke import identity, current_gpu, verify_model

PACK = ROOT / "research/grounded-role-pipeline-20261019-v1"
CARDS = ROOT / "research/grounded-role-cards-20261019-v2"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gpu-uuid")
    parser.add_argument("--preflight-only", action="store_true")
    a = parser.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    launch = dict(status="started", identity=identity(), runtime=locked_runtime(), output=str(out),
        code_sha256=sha256(Path(__file__)), production_generated_answers=0, production_optimizer_updates=0)
    write_json(out / "launch.json", launch)
    try:
        release = json.loads((PACK / "release.json").read_text())
        for name, expected in release["files_sha256"].items():
            assert sha256(ROOT/name) == expected, name
        launch["release_sha256"] = sha256(PACK/"release.json")
        config = json.loads((ROOT/"research/scenario-role-sft-20261017-v1/fit-config.json").read_text())
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(config["model_path"], local_files_only=True)
        reader = json.loads((PACK/"reader.json").read_text())

        def prefix(messages, cap):
            assert all("<|im_start|>" not in m["content"] and "<|im_end|>" not in m["content"] for m in messages)
            ids = tok.apply_chat_template(messages, tokenize=True, return_dict=False,
                add_generation_prompt=True, enable_thinking=False)
            assert len(ids)+cap<=8192
            assert ids.count(tok.convert_tokens_to_ids("<|im_end|>"))==2
            return ids

        reader_ids = prefix(reader, 3072)
        write_json(out/"reader-input.json", dict(messages=reader, prefix_ids=reader_ids))
        if a.preflight_only:
            launch.update(status="preflight_complete", reader_prefix_tokens=len(reader_ids))
            write_json(out/"launch.json", launch)
            print(json.dumps(launch), flush=True)
            return
        assert a.gpu_uuid
        launch["gpu"] = current_gpu(a.gpu_uuid)
        assert launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
        os.environ["CUDA_VISIBLE_DEVICES"] = a.gpu_uuid
        launch["model_verification"] = verify_model(config)
        current_gpu(a.gpu_uuid)
        write_json(out/"launch.json", launch)
        shutil.copyfile(__file__, out/"executed-runner.py")
        import torch
        from transformers import GenerationConfig, Qwen3_5ForCausalLM
        torch.manual_seed(42)
        model = Qwen3_5ForCausalLM.from_pretrained(config["model_path"], local_files_only=True,
            dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda:0").eval()
        versions = {n:p._version for n,p in model.named_parameters()}

        def generate(ident, messages, cap):
            ids = prefix(messages, cap)
            decoder = GenerationConfig(do_sample=False, max_new_tokens=cap, use_cache=True,
                eos_token_id=tok.convert_tokens_to_ids("<|im_end|>"), pad_token_id=tok.pad_token_id)
            x = torch.tensor([ids], device="cuda:0")
            start = time.perf_counter()
            with torch.inference_mode():
                result = model.generate(input_ids=x, attention_mask=torch.ones_like(x), generation_config=decoder)
            torch.cuda.synchronize()
            output_ids = result[0,x.shape[1]:].tolist()
            assert all(p._version==versions[n] for n,p in model.named_parameters())
            launch["production_generated_answers"] += 1
            write_json(out/"launch.json", launch)
            return dict(id=ident, messages=messages, prefix_ids=ids, prefix_sha256=ids_digest(ids),
                decoder=decoder.to_dict(), output_ids=output_ids, output_raw=tok.decode(output_ids, skip_special_tokens=False),
                output_display=tok.decode(output_ids, skip_special_tokens=True), generated_tokens=len(output_ids),
                generation_seconds=time.perf_counter()-start,
                at_cap=len(output_ids)==cap and output_ids[-1]!=decoder.eos_token_id)

        record = generate("shared-reader", reader, 3072)
        write_json(out/"reader-response.json", record)
        while True:
            launch["status"]="awaiting_explicit_operation"
            write_json(out/"launch.json", launch)
            print(json.dumps(dict(state="awaiting_explicit_operation", answers=launch["production_generated_answers"], idle_timeout_seconds=300)), flush=True)
            if not select.select([sys.stdin], [], [], 300)[0]:
                break
            line = sys.stdin.readline()
            if not line:
                break
            command = json.loads(line)
            if command.get("operation")=="exit":
                break
            assert command.get("operation")=="write" and launch["production_generated_answers"]==1
            review = json.loads((out/"reader-inspection.json").read_text())
            assert review["complete_output_read"] is True and review["decision"]=="run_writer_pair"
            assert review["reader_response_sha256"]==sha256(out/"reader-response.json")
            current = __import__('subprocess').check_output(["nvidia-smi","--query-compute-apps=gpu_uuid,pid","--format=csv,noheader,nounits"],text=True)
            assert {int(s.split(',')[1]) for s in current.splitlines() if s.split(',')[0].strip()==a.gpu_uuid}=={os.getpid()}
            raw_map = record["output_display"]
            parsed = json.loads(raw_map)
            schema = json.loads((PACK/"schema.json").read_text())
            assert set(parsed)==set(schema)
            assert all(set(parsed[k])==set(schema[k]) and all(isinstance(v,str) for v in parsed[k].values()) for k in schema)
            assert not record["at_cap"]
            rows = json.loads((CARDS/"examples.json").read_text())
            with (out/"writer-responses.jsonl").open('x') as f:
                for row in rows:
                    common, role = row["messages"][1]["content"].split("\n\nREQUESTED ROLE:")
                    content = common + "\n\nMODEL-EXTRACTED WORKING MAP (fallible notes, not new government authority):\n" + raw_map + "\n\nREQUESTED ROLE:" + role
                    messages = [row["messages"][0], dict(role="user",content=content)]
                    response = generate(row["id"], messages, 2048)
                    response["country"] = row["country"]
                    response["unedited_reader_response_sha256"] = sha256(out/"reader-response.json")
                    f.write(json.dumps(response,ensure_ascii=False)+"\n"); f.flush()
        launch.update(status="completed",process_state="exiting_normally",base_parameter_versions_unchanged=True)
        write_json(out/"launch.json", launch)
    except Exception as exc:
        launch.update(status="failed",exception=repr(exc),traceback=traceback.format_exc())
        write_json(out/"launch.json",launch)
        raise


if __name__=="__main__":
    main()
