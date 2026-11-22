"""Replay the release's Syria collection with the local frozen checkpoint."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "benchmark-v1"))
import run_suite as suite

MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def roster():
    suite.verify_release()
    return {key: row for key, row in suite.e.cases().items() if row["family"] == "syria"}


def prompt(tokenizer, request):
    rendered = tokenizer.apply_chat_template(request["messages"], tokenize=False,
                                             add_generation_prompt=True, enable_thinking=False)
    return tokenizer.encode(rendered, add_special_tokens=False)


def run(directory):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, __version__

    cases = roster()
    gpu = os.environ["CUDA_VISIBLE_DEVICES"]
    assert gpu.startswith("GPU-") and "," not in gpu
    hardware = subprocess.check_output(
        ["nvidia-smi", "-i", gpu, "--query-gpu=name,uuid,memory.used", "--format=csv,noheader,nounits"],
        text=True).strip()
    name, uuid, used = (field.strip() for field in hardware.split(","))
    assert uuid == gpu and int(used) == 0, hardware
    owned = subprocess.check_output(
        ["nvidia-smi", "-i", gpu, "--query-compute-apps=pid", "--format=csv,noheader"],
        text=True).strip()
    assert not owned, owned
    directory.mkdir()
    launch = {
        "host": socket.gethostname(), "gpu_name": name, "gpu_uuid": uuid, "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                 text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(directory.resolve()),
        "checkpoint": str(MODEL), "checkpoint_index_sha256": sha(MODEL / "model.safetensors.index.json"),
        "release_sha256": sha(suite.e.HERE / "release.json"), "protocol_sha256": sha(HERE / "protocol.md"),
        "collector_sha256": sha(Path(__file__)), "cases": list(cases), "optimizer_updates": 0,
        "torch": torch.__version__, "transformers": __version__, "dtype": "bfloat16",
        "decoding": "greedy, thinking disabled", "attention": "sdpa",
    }
    (directory / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda:0").eval()

    def generate(request):
        ids = prompt(tokenizer, request)
        x = torch.tensor([ids], device="cuda:0")
        config = GenerationConfig(max_new_tokens=request["max_output_tokens"], do_sample=False,
                                  eos_token_id=eos, pad_token_id=tokenizer.pad_token_id, use_cache=True)
        with torch.inference_mode():
            output = model.generate(input_ids=x, attention_mask=torch.ones_like(x), generation_config=config)
        result = output[0, len(ids):].tolist()
        response = {"text": tokenizer.decode(result, skip_special_tokens=True).strip(),
                    "input_tokens": len(ids), "output_tokens": len(result),
                    "termination": "complete" if result and result[-1] == eos else "cap"}
        suite.append(directory / "tokens.jsonl", {"input_ids": ids, "output_ids": result, "response": response})
        return response

    with patch.object(suite.e, "cases", return_value=cases):
        suite.collect(generate, directory)
    result = {file.name: sha(file) for file in sorted(directory.iterdir())}
    (directory / "complete.json").write_text(json.dumps(result, indent=2) + "\n")


def verify(directory):
    from transformers import AutoTokenizer

    cases = roster()
    manifest = suite.e.read(directory / "complete.json")
    assert all(sha(directory / name) == digest for name, digest in manifest.items())
    launch = suite.e.read(directory / "launch.json")
    assert launch["release_sha256"] == sha(suite.e.HERE / "release.json")
    assert launch["protocol_sha256"] == sha(HERE / "protocol.md") and launch["collector_sha256"] == sha(Path(__file__))
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    read = lambda name: [json.loads(line) for line in (directory / name).read_text().splitlines()]
    actual, logical, episodes = map(read, ("tokens.jsonl", "actors.jsonl", "episodes.jsonl"))
    assert (len(actual), len(logical), len(episodes)) == (32, 36, 12)
    for row, log in zip(actual, (r for r in logical if not r["reused"]), strict=True):
        assert row["input_ids"] == prompt(tokenizer, log["request"])
        assert row["response"] == log["reply"]
        ids = row["output_ids"]
        assert len(ids) == log["reply"]["output_tokens"] and eos not in ids[:-1]
        assert bool(ids and ids[-1] == eos) == (log["reply"]["termination"] == "complete")
        assert tokenizer.decode(ids, skip_special_tokens=True).strip() == log["reply"]["text"]
    decoded = iter(logical)
    for episode in episodes:
        case, arm, order = episode["id"].split("/")
        order = int(order)
        calls = suite.e.validate_calls(cases[case], arm, order, episode["calls"])
        for step, call in enumerate(calls):
            row = next(decoded)
            assert row["request"] == suite.e.build_request(cases[case], arm, order, calls[:step])
            assert all(call[k] == val for k, val in row["reply"].items())
    assert next(decoded, None) is None
    return {"physical_calls": len(actual), "logical_turns": len(logical), "episodes": len(episodes),
            "final_cap_hits": sum(x["calls"][-1]["termination"] == "cap" for x in episodes)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        suite.e.emit(verify(args.directory))
