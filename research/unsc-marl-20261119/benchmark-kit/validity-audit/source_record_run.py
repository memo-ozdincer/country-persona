"""Run or replay the frozen source-record pilot with variable generation caps."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

from source_record_episode import PACK, episode


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def locks():
    return {path.name: digest(path) for path in
            (Path(__file__).resolve(), Path(__file__).with_name("source_record_episode.py"), PACK)}


def encode(tokenizer, row):
    prompt = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                           enable_thinking=False)
    return tokenizer.encode(prompt, add_special_tokens=False)


def run(model_path, directory):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    directory.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    launch = {"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
              "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                       text=True).strip(),
              "command": [sys.executable, *sys.argv], "run_directory": str(directory.resolve()),
              "model": str(model_path.resolve()), "torch": torch.__version__,
              "transformers": transformers.__version__, "optimizer_updates": 0, "sha256": locks()}
    (directory / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, padding_side="left")
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True,
                                                dtype=torch.bfloat16, attn_implementation="sdpa").eval()
    path = directory / "transcript.jsonl"
    def generate(batch):
        cap, = {r["cap"] for r in batch}
        ids = [encode(tokenizer, row) for row in batch]
        inputs = tokenizer.pad({"input_ids": ids}, return_tensors="pt")
        with torch.inference_mode():
            model_output = model.generate(**inputs, do_sample=False, max_new_tokens=cap, use_cache=True,
                                          pad_token_id=tokenizer.pad_token_id, eos_token_id=eos)
        results = {}
        with path.open("a") as stream:
            for request, prefix, new_ids in zip(batch, ids, model_output[:, inputs.input_ids.shape[1]:].tolist(), strict=True):
                if eos in new_ids:
                    new_ids = new_ids[:new_ids.index(eos) + 1]
                row = {**request, "input_ids": prefix, "output_ids": new_ids, "ended": new_ids[-1] == eos,
                       "output": tokenizer.decode(new_ids, skip_special_tokens=True).strip()}
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                results[row["id"]] = row
        print({"completed": list(results)}, flush=True)
        return results
    episodes = episode(generate)
    result = {x["family"]: {k: v["output"] for k, v in x["final"].items()} for x in episodes}
    (directory / "final-records.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    complete = {"transcript_sha256": digest(path), "records": len(path.read_text().splitlines()),
                "final_records_sha256": digest(directory / "final-records.json")}
    (directory / "complete.json").write_text(json.dumps(complete, indent=2) + "\n")


def replay(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    f = directory / "transcript.jsonl"
    assert launch["sha256"] == locks() and complete["transcript_sha256"] == digest(f)
    records = {r["id"]: r for r in map(json.loads, f.read_text().splitlines())}
    assert len(records) == complete["records"]
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    used = {}
    def generate(batch):
        restored = {}
        for request in batch:
            identifier = request["id"]
            row = records.pop(identifier)
            assert all(row[k] == json.loads(json.dumps(val)) for k, val in request.items())
            assert encode(tokenizer, request) == row["input_ids"]
            out = row["output_ids"]
            assert 0 < len(out) <= request["cap"] and eos not in out[:-1]
            assert tokenizer.decode(out, skip_special_tokens=True).strip() == row["output"]
            assert (out[-1] == eos) == row["ended"]
            restored[identifier] = row
            used[identifier] = {"total_input_tokens": len(row["input_ids"]),
                                "total_output_tokens": len(out), "ended": row["ended"]}
        return restored
    episodes = episode(generate)
    output = {x["family"]: {k: v["output"] for k, v in x["final"].items()} for x in episodes}
    assert not records and len(used) == 26
    finals = directory / "final-records.json"
    assert json.loads(finals.read_text()) == output and complete["final_records_sha256"] == digest(finals)
    return {"calls": used, "final_records": sum(map(len, output.values()))}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        if args.model is None:
            cli.error("--model is required for run")
        run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory), indent=2))
