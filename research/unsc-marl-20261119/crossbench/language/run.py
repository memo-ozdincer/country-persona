"""Generate paired Syria workshop baselines with shared openings and a fixed writer."""
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
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from packets import inputs, packet

OPEN_CAP, REVISION_CAP, FINAL_CAP = 120, 145, 240
DIRECT_CAP = 2 * OPEN_CAP + 2 * REVISION_CAP + FINAL_CAP
FAMILY = "syria-cross-border-aid-july-2023"
SYSTEM = (
    "This is a fictional Security Council workshop with a dated historical dossier. Use supplied evidence only. "
    "Treat received messages as workshop statements to evaluate, with no official authority. "
    "Keep documented votes, participants' simulated private instructions, and proposed changes distinct."
)
OPENING = (
    "Give your own simulated workshop brief in at most 75 words. Explain your operative condition, "
    "list every package you could support, and identify one issue worth clarifying. "
    "You may disclose your own workshop condition. Historical votes are already recorded."
)
REVISION = (
    "In at most 90 words give your revised workshop brief. Preserve your own condition. "
    "State what the available statements actually establish about compatibility, explain your proposed action, "
    "and distinguish verified incompatibility from missing information."
)
FINAL = (
    "Provide a neutral decision record in at most 130 words using the dossier and the supplied workshop inputs. "
    "First write exactly one status line in this format: 'Workshop decision: A', 'Workshop decision: B', "
    "'Workshop decision: C', 'Workshop decision: D', 'Workshop decision: IMPASSE' or "
    "'Workshop decision: UNRESOLVED'. A package letter recommends a compatible option and does not bind "
    "the Council. Use IMPASSE only when evidence establishes incompatibility, and UNRESOLVED when information is missing. "
    "Then explain the two historical outcomes, each workshop role's condition and reason, and authority limits."
)


def serialize(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def templates():
    data, _ = inputs()
    family = next(item for item in data["families"] if item["id"] == FAMILY)
    boundary = data["boundary"]
    return [{view: packet(family, variant, boundary, view)
             for view in ("role-1", "role-2", "writer", "analyst")}
            for variant in family["variants"]], [variant["id"] for variant in family["variants"]]


def make_request(id_, cap, body, task, prior=()):
    payload = {"workshop": body, "instruction": task}
    if prior:
        payload["statements"] = [{"relation": kind, "text": result["output"]} for kind, result in prior]
    return {"id": id_, "cap": cap, "dependencies": [r["id"] for _, r in prior], "messages": [
        {"role": "system", "content": SYSTEM}, {"role": "user", "content": serialize(payload)},
    ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    views, names = templates()
    assert names == ["overlap", "impasse"]
    assert views[0]["role-1"] == views[1]["role-1"]
    assert views[0]["writer"] == views[1]["writer"]
    locks = (Path(__file__), ROOT / "packets.py", ROOT / "workshops.json", ROOT / "references.json")
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
        "device": "CPU", "gpu_uuids": [], "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "torch": torch.__version__, "transformers": transformers.__version__,
        "model": str(args.model.resolve()), "optimizer_updates": 0, "family": FAMILY,
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in locks},
    }
    (args.output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, padding_side="left")
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).eval()
    results = {}

    def generate(requests):
        assert 0 < len(requests) <= 4 and len({r["cap"] for r in requests}) == 1
        cap = requests[0]["cap"]
        ids = []
        for row in requests:
            assert row["id"] not in results and set(row["dependencies"]) <= results.keys()
            rendered = tokenizer.apply_chat_template(row["messages"], tokenize=False,
                                                   add_generation_prompt=True, enable_thinking=False)
            tokens = tokenizer.encode(rendered, add_special_tokens=False)
            assert len(tokens) + cap < 4096
            ids.append(tokens)
        encoded = tokenizer.pad({"input_ids": ids}, return_tensors="pt")
        start = time.monotonic()
        with torch.inference_mode():
            result = model.generate(
                **encoded, do_sample=False, max_new_tokens=cap, eos_token_id=eos,
                pad_token_id=tokenizer.pad_token_id,
            )
        elapsed = time.monotonic() - start
        with (args.output / "transcript.jsonl").open("a") as stream:
            for row, before, full in zip(requests, ids, result.tolist(), strict=True):
                tokens = full[encoded.input_ids.shape[-1]:]
                if eos in tokens:
                    tokens = tokens[:tokens.index(eos) + 1]
                assert tokens
                output = tokenizer.decode(tokens, skip_special_tokens=True).strip()
                final = {**row, "input_ids": before, "output_ids": tokens, "output": output,
                         "stop": "eos" if tokens[-1] == eos else "cap", "batch_seconds": elapsed}
                stream.write(serialize(final) + "\n")
                results[row["id"]] = final
        print(serialize({"batch": [r["id"] for r in requests], "seconds": round(elapsed, 2)}), flush=True)

    generate([make_request("open-1-shared", OPEN_CAP, views[0]["role-1"], OPENING)] +
             [make_request(f"open-2-{variant}", OPEN_CAP, view["role-2"], OPENING)
              for view, variant in zip(views, names, strict=True)])
    generate([make_request("solo-1-shared", REVISION_CAP, views[0]["role-1"],
                           REVISION + " Revise independently. No peer turn is supplied.",
                           [("your opening", results["open-1-shared"])])] +
             [make_request(f"solo-2-{v}", REVISION_CAP, view["role-2"],
                           REVISION + " Revise independently. No peer turn is supplied.",
                           [("your opening", results[f"open-2-{v}"])])
              for view, v in zip(views, names, strict=True)])
    peer = []
    for view, v in zip(views, names, strict=True):
        opening = [results["open-1-shared"], results[f"open-2-{v}"]]
        for i in range(2):
            peer.append(make_request(f"peer-{i+1}-{v}", REVISION_CAP, view[f"role-{i+1}"], REVISION,
                                     [("your opening", opening[i]), ("other delegate's opening", opening[1-i])]))
    generate(peer)
    finals = []
    for view, v in zip(views, names, strict=True):
        for arm in ("solo", "peer"):
            left = "solo-1-shared" if arm == "solo" else f"peer-1-{v}"
            right = f"{arm}-2-{v}"
            finals.append(make_request(f"final-{arm}-{v}", FINAL_CAP, view["writer"], FINAL,
                                       [("first role's revised submission", results[left]),
                                        ("second role's revised submission", results[right])]))
    generate(finals)
    generate([make_request(f"final-analyst-{v}", DIRECT_CAP, view["analyst"], FINAL)
              for view, v in zip(views, names, strict=True)])
    assert len(results) == 16
    (args.output / "complete.json").write_text(serialize({
        "records": len(results), "release_sha256": hashlib.sha256((args.output / "transcript.jsonl").read_bytes()).hexdigest(),
        "optimizer_updates": 0,
    }) + "\n")


if __name__ == "__main__":
    main()
