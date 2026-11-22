"""Run the frozen full judge prompt on the authored sanctions contrast."""
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

JUDGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(JUDGE))
from score import request, score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    locks = (Path(__file__), JUDGE / "instructions.md", JUDGE / "calibration.json", JUDGE / "score.py")
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
        "device": "CPU", "gpu_uuids": [], "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "torch": torch.__version__, "transformers": transformers.__version__,
        "model": str(args.model.resolve()), "optimizer_updates": 0,
        "inputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in locks},
    }
    (args.output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    calibration = json.loads((JUDGE / "calibration.json").read_text())
    # Reverse anchor order; each input is adjudicated independently.
    fixtures = [r for r in reversed(calibration["final_calibration"]) if r["request"]["id"].startswith("T17-")]
    assert len(fixtures) == 2
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, padding_side="left")
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).eval()
    instructions = (JUDGE / "instructions.md").read_text()
    inputs, messages = [], []
    for fixture in fixtures:
        message = [{"role": "system", "content": instructions}, {
            "role": "user", "content": json.dumps(request(fixture["request"]), ensure_ascii=False)
        }]
        rendered = tokenizer.apply_chat_template(
            message, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        ids = tokenizer.encode(rendered, add_special_tokens=False)
        assert len(ids) + 768 < 4096
        inputs.append(ids)
        messages.append(message)
    batch = tokenizer.pad({"input_ids": inputs}, return_tensors="pt")
    start = time.monotonic()
    with torch.inference_mode():
        result = model.generate(
            **batch, do_sample=False, max_new_tokens=768, eos_token_id=eos, pad_token_id=tokenizer.pad_token_id
        )
    elapsed = time.monotonic() - start
    records = []
    for fixture, row, ids, prompt in zip(fixtures, result.tolist(), inputs, messages):
        tokens = row[batch.input_ids.shape[-1]:]
        if eos in tokens:
            tokens = tokens[:tokens.index(eos) + 1]
        response = tokenizer.decode(tokens, skip_special_tokens=True).strip()
        record = {"id": fixture["request"]["id"], "messages": prompt, "input_ids": ids, "output_ids": tokens,
                  "raw_response": response, "stop": "eos" if tokens[-1] == eos else "cap"}
        try:
            verdict = json.loads(response)
            record["score"] = score(fixture["request"], verdict)
            record["guard_agreement"] = record["score"]["guard"] == fixture["score"]["guard"]
            authored = {r["id"]: r["status"] for r in fixture["authored_verdict"]["units"]}
            record["unit_agreement"] = sum(r["status"] == authored[r["id"]] for r in verdict["units"])
        except (ValueError, KeyError, TypeError) as error:
            record["validation_error"] = str(error)
        records.append(record)
    (args.output / "responses.json").write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"calls": len(records), "elapsed_seconds": elapsed,
                      "results": [{k: r.get(k) for k in ("id", "stop", "score", "validation_error")} for r in records]}))


if __name__ == "__main__":
    main()
