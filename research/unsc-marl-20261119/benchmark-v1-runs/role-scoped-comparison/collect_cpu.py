"""Run the locked first-token assay on CPU when the accelerator is occupied."""
import argparse
import json
from math import isfinite
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

from collect_roles import HERE, collector, plan, prior, read

OUT = HERE / "evidence-cpu"
THREADS = 8


def locked():
    config = plan()
    assert config == read(HERE / "plan.json")
    return config


def write(file, data):
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def append(stream, data):
    stream.write(json.dumps(data, ensure_ascii=False) + "\n")
    stream.flush()


def host_cpu():
    return re.search(r"^model name\s*:\s*(.+)$", Path("/proc/cpuinfo").read_text(), re.M).group(1)


def run():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, __version__

    config = locked()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    torch.set_num_threads(THREADS)
    torch.set_num_interop_threads(1)
    keys = ("launch.json", "calls.jsonl", "tokens.jsonl")
    OUT.mkdir()
    write(OUT / "launch.json", {
        "host": socket.gethostname(), "device": "cpu", "cpu_model": host_cpu(), "threads": THREADS,
        "pid": os.getpid(), "process_start": subprocess.check_output(
            ["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(OUT),
        "checkpoint": str(collector.MODEL), "checkpoint_index_sha256": config["checkpoint_index_sha256"],
        "plan_sha256": collector.sha(HERE / "plan.json"), "runner_sha256": collector.sha(Path(__file__)),
        "torch": torch.__version__, "transformers": __version__, "dtype": "bfloat16",
        "attention": "sdpa", "optimizer_updates": 0,
    })
    tok = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        collector.MODEL, local_files_only=True, dtype=torch.bfloat16,
        attn_implementation="sdpa", device_map="cpu").eval()
    labels = prior.base.label_tokens(tok)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    with (OUT / "calls.jsonl").open("w") as calls, (OUT / "tokens.jsonl").open("w") as trace, torch.inference_mode():
        for request in config["requests"]:
            ids = collector.prompt(tok, request)
            vector = torch.tensor([ids], dtype=torch.long, device="cpu")
            logits = model(input_ids=vector, attention_mask=torch.ones_like(vector), use_cache=False,
                           logits_to_keep=1).logits[0, -1].float()
            scores = {key: logits[index].item() for key, index in labels.items()}
            assert all(isfinite(value) for value in scores.values())
            chosen = max(scores, key=scores.get)
            reply = {"text": chosen, "input_tokens": len(ids), "output_tokens": 2, "termination": "complete"}
            append(calls, {"request": request, "reply": reply, "logits": scores})
            append(trace, {"input_ids": ids, "output_ids": [labels[chosen], eos], "response": reply})
    write(OUT / "complete.json", {k: collector.sha(OUT / k) for k in keys})


def verify():
    from transformers import AutoTokenizer

    config = locked()
    manifest = read(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "calls.jsonl", "tokens.jsonl"}
    assert all(collector.sha(OUT / k) == v for k, v in manifest.items())
    launch = read(OUT / "launch.json")
    assert launch["checkpoint_index_sha256"] == config["checkpoint_index_sha256"]
    assert launch["plan_sha256"] == collector.sha(HERE / "plan.json")
    assert launch["runner_sha256"] == collector.sha(Path(__file__))
    assert launch["device"] == "cpu" and launch["optimizer_updates"] == 0
    tok = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    labels = prior.base.label_tokens(tok)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    calls, trace = ([json.loads(line) for line in (OUT / k).read_text().splitlines()]
                    for k in ("calls.jsonl", "tokens.jsonl"))
    outputs = {}
    for request, call, row in zip(config["requests"], calls, trace, strict=True):
        assert call["request"] == request and call["reply"] == row["response"]
        assert row["input_ids"] == collector.prompt(tok, request)
        scores, reply = call["logits"], call["reply"]
        assert set(scores) == set(labels) and all(isfinite(value) for value in scores.values())
        chosen = max(scores, key=scores.get)
        assert row["output_ids"] == [labels[chosen], eos] and reply["text"] == chosen
        assert reply["input_tokens"] == len(row["input_ids"]) and reply["output_tokens"] == 2
        outputs[request["id"]] = {"logits": scores, "reply": reply}
    return {"manifest": manifest, "outputs": outputs}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    if parser.parse_args().mode == "run":
        run()
    else:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
