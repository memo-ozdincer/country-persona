"""Run the fixed-budget Iraq disclosure baseline without updating Qwen."""
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

from protocol import FAMILY, HERE, ROOT, admit, family_inputs, request, script, serialize, summarize


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    roles, views, truth = family_inputs()
    names = ("overlap", "impasse")
    locks = [Path(__file__), HERE / "protocol.py", *(ROOT / name for name in (
        "decision_ledger.py", "packets.py", "references.json", "workshops.json"))]
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
        "device": "CPU", "gpu_uuids": [], "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "torch": torch.__version__, "transformers": transformers.__version__,
        "model": str(args.model.resolve()), "optimizer_updates": 0, "family": FAMILY,
        "input_sha256": {p.name: digest(p) for p in locks},
    }
    (args.output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    with (args.output / "scripted.json").open("x") as artifact:
        json.dump({v: {arm: script(roles, truth[v], arm) for arm in
                      ("support_first", "exclusion_first", "public_A_probe")} for v in names}, artifact, indent=2)

    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, padding_side="left")
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa").eval()
    records = {}

    def generate(entries):
        plans = [x[0] for x in entries]
        assert len({r["cap"] for r in plans}) == 1
        cap = plans[0]["cap"]
        inputs_ids = []
        for row in plans:
            assert row["id"] not in records
            rendered = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                                    enable_thinking=False)
            ids = tokenizer.encode(rendered, add_special_tokens=False)
            assert len(ids) + cap < 4096
            inputs_ids.append(ids)
        encoded = tokenizer.pad({"input_ids": inputs_ids}, return_tensors="pt")
        start = time.monotonic()
        with torch.inference_mode():
            out = model.generate(**encoded, do_sample=False, max_new_tokens=cap, eos_token_id=eos,
                                 pad_token_id=tokenizer.pad_token_id)
        elapsed = time.monotonic() - start
        with (args.output / "transcript.jsonl").open("a") as transcript:
            for (row, v, i), ids, generated in zip(entries, inputs_ids, out.tolist(), strict=True):
                tail = generated[encoded.input_ids.shape[-1]:]
                if eos in tail:
                    tail = tail[:tail.index(eos)+1]
                assert tail
                text = tokenizer.decode(tail, skip_special_tokens=True).strip()
                judged = admit(text, row["id"], roles[i], truth[v]["allowed_by_role"][i])
                row = {**row, "input_ids": ids, "output_ids": tail, "output": text,
                       "stop": "eos" if tail[-1] == eos else "cap", "judgment": judged, "batch_seconds": elapsed}
                transcript.write(serialize(row) + "\n")
                records[row["id"]] = row
        print(serialize({"batch": [r["id"] for r in plans], "seconds": round(elapsed, 2)}), flush=True)

    generate([(request("open-1-shared", views["overlap"][0]), "overlap", 0)] + [
        (request(f"open-2-{v}", views[v][1]), v, 1) for v in names])

    def opening(v, i):
        return records["open-1-shared" if i == 0 else f"open-2-{v}"]["judgment"]["admitted"]

    generate([(request("solo-1-shared", views["overlap"][0], opening("overlap", 0), second=True), "overlap", 0)] + [
        (request(f"solo-2-{v}", views[v][1], opening(v, 1), second=True), v, 1) for v in names])
    generate([(request(f"peer-{i+1}-{v}", views[v][i], opening(v, i), opening(v, 1-i),
                       second=True, peer_visible=True), v, i)
              for v in names for i in (0, 1)])
    metrics = {}
    for v in names:
        initial = [records["open-1-shared"], records[f"open-2-{v}"]]
        metrics[v] = {"opening": summarize(roles, truth[v], initial)}
        for arm in ("solo", "peer"):
            left = "solo-1-shared" if arm == "solo" else f"peer-1-{v}"
            pair = [records[left], records[f"{arm}-2-{v}"]]
            metrics[v][arm] = summarize(roles, truth[v], initial + pair)
    assert len(records) == 10
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (args.output / "complete.json").write_text(serialize({
        "records": len(records), "transcript_sha256": digest(args.output / "transcript.jsonl"),
        "optimizer_updates": 0,
    }) + "\n")


if __name__ == "__main__":
    main()
