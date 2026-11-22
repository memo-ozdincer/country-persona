"""Run a same-input, certificate-augmented writer test with the frozen Qwen."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SOURCE = PARENT / "evidence"
sys.path.insert(0, str(PARENT))
from available import evaluate
from run import FINAL_CAP, FINAL, serialize

NAMES = tuple(f"final-{arm}-{variant}" for variant in ("overlap", "impasse") for arm in ("solo", "peer"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    previous = json.loads((SOURCE / "complete.json").read_text())
    assert digest(SOURCE / "transcript.jsonl") == previous["release_sha256"]
    rows = {r["id"]: r for line in (SOURCE / "transcript.jsonl").read_text().splitlines()
            for r in [json.loads(line)]}
    proof = evaluate(SOURCE, SOURCE / "availability-annotations.json")
    rendered = []
    for variant, arms in proof["cases"].items():
        for arm, cert in arms.items():
            row = rows[f"final-{arm}-{variant}"]
            assert row["cap"] == FINAL_CAP and row["dependencies"] == cert["sources"]
            message = json.loads(row["messages"][1]["content"])
            assert message["instruction"] == FINAL and "compatibility_check" not in message
            assert cert["determinate_decision"] is not None
            added = {
                "scope": "Derived from the compatible and excluded packages stated in the two supplied fictional submissions. "
                         "This establishes workshop compatibility only. It does not establish either delegate's unconditional "
                         "assent, a historical national position, an adopted amendment, or a new Council decision.",
                "status": cert["determinate_decision"],
                "jointly_compatible": cert["visible_compatible"],
                "excluded_by_at_least_one_delegate": cert["visible_excluded"],
            }
            payload = dict(message, compatibility_check=added)
            rendered.append({
                "id": row["id"], "cap": FINAL_CAP, "dependencies": row["dependencies"],
                "messages": [row["messages"][0], {"role": "user", "content": serialize(payload)}],
            })
    assert tuple(row["id"] for row in rendered) == NAMES
    return rendered, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    suite, _ = inputs()
    old = json.loads((SOURCE / "launch.json").read_text())
    assert str(args.model.resolve()) == old["model"]
    paths = (Path(__file__), PARENT / "available.py", PARENT / "run.py",
             SOURCE / "transcript.jsonl", SOURCE / "availability-annotations.json", SOURCE / "complete.json")
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
        "device": "CPU", "gpu_uuids": [], "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "torch": torch.__version__, "transformers": transformers.__version__,
        "model": str(args.model.resolve()), "optimizer_updates": 0,
        "input_sha256": {p.name: digest(p) for p in paths},
    }
    (args.output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, padding_side="left")
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).eval()
    inputs_ids = []
    for row in suite:
        text = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                             enable_thinking=False)
        raw = tokenizer.encode(text, add_special_tokens=False)
        assert len(raw) + FINAL_CAP < 4096
        inputs_ids.append(raw)
    encoded = tokenizer.pad({"input_ids": inputs_ids}, return_tensors="pt")
    start = time.monotonic()
    with torch.inference_mode():
        result = model.generate(
            **encoded, do_sample=False, max_new_tokens=FINAL_CAP, eos_token_id=eos,
            pad_token_id=tokenizer.pad_token_id,
        )
    elapsed = time.monotonic() - start
    transcript = args.output / "transcript.jsonl"
    with transcript.open("x") as stream:
        for row, before, arr in zip(suite, inputs_ids, result.tolist(), strict=True):
            tail = arr[encoded.input_ids.shape[-1]:]
            if eos in tail:
                tail = tail[:tail.index(eos) + 1]
            assert tail
            out = tokenizer.decode(tail, skip_special_tokens=True).strip()
            stream.write(serialize({**row, "input_ids": before, "output_ids": tail, "output": out,
                                    "stop": "eos" if tail[-1] == eos else "cap", "batch_seconds": elapsed}) + "\n")
    (args.output / "complete.json").write_text(serialize({
        "records": len(suite), "transcript_sha256": digest(transcript), "optimizer_updates": 0
    }) + "\n")
    print(serialize({"records": len(suite), "seconds": round(elapsed, 2)}))


if __name__ == "__main__":
    main()
