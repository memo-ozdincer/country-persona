"""Measure the frozen Qwen base on paired UN workshop controls, with no optimizer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

from environment import ABSENT, FAMILIES, FAMILIES_PATH, HOLD, outcome, text_view, world

HERE = Path(__file__).resolve().parent


def cases(family):
    size = len(FAMILIES[family]["options"])
    end = size - 1
    profiles = [
        ({0}, {1}), ({0, end}, {1}), ({0}, {0, 1}), ({0, 1}, {0}),
        ({0, 1}, {1, end}), ({0, 1}, {0, 1}), (set(range(size)), {0, end}),
        ({0, end}, {0, 1}),
    ]
    orders = [list(range(size)), list(range(1, size)) + [0]]
    return [world(family, order, profile) for profile in profiles for order in orders]


def assert_free(uuid):
    gpus = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=uuid,name,memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
        text=True,
    )
    rows = [line.split(", ") for line in gpus.splitlines()]
    gpu = next(row for row in rows if row[0] == uuid)
    apps = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"], text=True
    )
    occupants = [line for line in apps.splitlines() if line.split(",")[0].strip() == uuid]
    if gpu[2:] != ["0", "0"] or occupants:
        raise RuntimeError(f"Device is occupied: {uuid}")
    return gpu[1]


def save(path, data):
    with path.open("x") as file:
        file.write(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--gpu-uuid")
    target.add_argument("--cpu", action="store_true")
    parser.add_argument("--family", choices=tuple(FAMILIES), action="append")
    args = parser.parse_args()
    args.output.mkdir()
    hardware = assert_free(args.gpu_uuid) if args.gpu_uuid else "CPU"
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_uuid or ""
    device = "cuda:0" if args.gpu_uuid else "cpu"

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if args.cpu:
        torch.set_num_threads(8)
        torch.set_num_interop_threads(1)
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
        "gpu_uuids": [args.gpu_uuid] if args.gpu_uuid else [], "device_name": hardware, "model_path": str(args.model.resolve()),
        "torch": str(torch.__version__), "transformers": transformers.__version__, "optimizer_updates": 0,
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (Path(__file__), FAMILIES_PATH, HERE / "environment.py")},
    }
    save(args.output / "launch.json", launch)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).to(device).eval()

    def owned():
        live = subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"], text=True
        )
        pids = {int(line.split(",")[1]) for line in live.splitlines()
                if line.split(",")[0].strip() == args.gpu_uuid}
        if pids != {os.getpid()}:
            raise RuntimeError(f"Device occupant check failed: {args.gpu_uuid}, {sorted(pids)}")

    @torch.inference_mode()
    def decide(worlds, phase, own, inbox, family, arm):
        rows = []
        letters = "H" + "ABCD"[:len(worlds[0]["options"])]
        ids = [tokenizer.encode(letter, add_special_tokens=False) for letter in letters]
        if any(len(tokens) != 1 for tokens in ids) or len({tokens[0] for tokens in ids}) != len(ids):
            raise ValueError("Action letters must be distinct single tokens")
        label_ids = [tokens[0] for tokens in ids]
        for i, case in enumerate(worlds):
            for role in range(2):
                prompt = text_view(case, role, phase, peer=inbox[i][role], own=own[i][role])
                rendered = tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True,
                    enable_thinking=False,
                )
                prefix = tokenizer.encode(rendered, add_special_tokens=False)
                if len(prefix) > 1024:
                    raise ValueError("Prompt exceeds the locked context cap")
                if any(tokenizer.encode(rendered + letter, add_special_tokens=False) != prefix + [token]
                       for letter, token in zip(letters, label_ids)):
                    raise ValueError("Action label crosses the tokenizer boundary")
                rows.append({"profile": i // 2, "option_order_variant": i % 2, "role": role,
                             "prompt": prompt, "input_ids": prefix})
        if args.gpu_uuid:
            owned()
        for offset in range(0, len(rows), 8):
            chunk = rows[offset:offset + 8]
            encoded = tokenizer.pad({"input_ids": [r["input_ids"] for r in chunk]}, return_tensors="pt").to(device)
            logits = model(**encoded, use_cache=False, logits_to_keep=1).logits[:, -1].float()
            legal = logits[:, label_ids]
            mass = (legal.logsumexp(-1) - logits.logsumexp(-1)).exp()
            for row, probs, total in zip(chunk, legal.softmax(-1).tolist(), mass.tolist()):
                choice = max(range(len(probs)), key=probs.__getitem__)
                row.update(action=choice + HOLD, action_letter=letters[choice],
                           conditional_probs=dict(zip(letters, probs)), legal_mass=total)
        with (args.output / "actions.jsonl").open("a") as file:
            for row in rows:
                file.write(json.dumps({"family": family, "arm": arm, "phase": phase, **row}) + "\n")
        return [[rows[i]["action"], rows[i + 1]["action"]] for i in range(0, len(rows), 2)]

    result = {}
    for family in dict.fromkeys(args.family or FAMILIES):
        worlds = cases(family)
        absent = [[ABSENT, ABSENT] for _ in worlds]
        signals = decide(worlds, "proposal", absent, absent, family, "shared")
        peer = [sent[::-1] for sent in signals]
        shuffled = [peer[(i + 2) % len(peer)] for i in range(len(peer))]
        result[family] = {}
        for arm, inbox in (("peer", peer), ("silent", absent), ("shuffled", shuffled)):
            votes = decide(worlds, "ballot", signals, inbox, family, arm)
            result[family][arm] = [
                {"case": case, "signals": sent, "received": observed, "ballots": final,
                 **outcome(case, sent, final)}
                for case, sent, observed, final in zip(worlds, signals, inbox, votes)
            ]
        print(f"{family}: {len(worlds)} shared worlds and three matched ballot arms", flush=True)
    save(args.output / "episodes.json", result)
    save(args.output / "complete.json", {
        "optimizer_updates": 0,
        "action_records": sum(8 * len(cases(family)) for family in result),
        "records_sha256": {name: hashlib.sha256((args.output / name).read_bytes()).hexdigest()
                           for name in ("episodes.json", "actions.jsonl")},
    })


if __name__ == "__main__":
    main()
