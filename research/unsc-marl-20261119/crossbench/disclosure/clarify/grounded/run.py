"""Compare local field grounding against saved query replies, with optional live replay."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from hashlib import sha256
from collections import Counter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from probe import CAP, CONTINUATIONS, cases, evaluate, locks, plan, select, serialize, summarize

ORIGINAL = HERE.parent / "evidence"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def old_rows():
    transcript = ORIGINAL / "transcript.jsonl"
    assert digest(transcript) == json.loads((ORIGINAL / "complete.json").read_text())["transcript_sha256"]
    return {row["id"]: row for row in map(json.loads, transcript.read_text().splitlines())}


def grounded(row, option):
    messages = [m.copy() for m in row["messages"]]
    payload = json.loads(messages[1]["content"])
    if option:
        view = payload["role_view"]
        conditions = view["private_instruction"]["conditions"]
        package, = (p for p in view["fictional_packages"] if p["id"] == option)
        payload["queried_option_local_fields"] = {
            "option": option, "private_requirements": conditions,
            "package_values": {key: package[key] for key in conditions},
        }
        payload["task"] += (" Compare the exact values in queried_option_local_fields. "
                            "Accept if every required value matches the corresponding package value. "
                            "If any required value differs, exclude. Use the original two-field JSON.")
    messages[1]["content"] = serialize(payload)
    return {"id": row["id"], "cap": row["cap"], "messages": messages}


def fixed_specs(rows):
    worlds = dict(cases())
    for id_, row in rows.items():
        family, variant, stage = id_.split("/")
        if not stage.startswith("query-"):
            continue
        roles, _, truth = worlds[family, variant]
        i = roles.index(row["role"])
        yield grounded(row, row["query"]), row["role"], truth["allowed_by_role"][i], row["query"]


def paired(rows, new):
    counts = Counter()
    transitions = {}
    for id_, row in new.items():
        old = rows[id_]["judgment"]["kind"]
        now = row["judgment"]["kind"]
        counts[f"{old}->{now}"] += 1
        transitions[id_] = [old, now]
    return {"transitions": dict(counts), "rows": transitions}


def adaptive(rows, generate):
    worlds = dict(cases())
    states = {}
    for family, variant in worlds:
        states[family, variant] = [rows[f"{family}/shared/open-0"], rows[f"{family}/{variant}/open-1"]]
    for step in range(CONTINUATIONS):
        batch = []
        for (family, variant), history in states.items():
            roles, views, ref = worlds[family, variant]
            claims = [r["judgment"]["admitted"] for r in history if r["judgment"]["admitted"]]
            i, option = select(roles, claims, step)
            row = plan(f"{family}/{variant}/grounded-{step}", views[i], claims, "query", option)
            batch.append((grounded(row, option), roles[i], ref["allowed_by_role"][i], option))
        emitted = generate(batch, "adaptive")
        for key, (row, *_) in zip(states, batch, strict=True):
            states[key].append(emitted[row["id"]])
    final = {}
    for key, history in states.items():
        roles, _, ref = worlds[key]
        snapshots = [summarize(roles, ref, history[:2+s]) for s in range(CONTINUATIONS+1)]
        first = next((s for s, snap in enumerate(snapshots) if snap["correct"]), None)
        final["/".join(key)] = {"first_certificate": first, "final": snapshots[-1],
                                "calls": len(history), "cap": sum(r["cap"] for r in history),
                                "input_tokens": sum(len(r["input_ids"]) for r in history),
                                "generated_tokens": sum(len(r["output_ids"]) for r in history)}
    return final


def main():
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--wait-for-adaptive", action="store_true")
    args = parser.parse_args()
    args.output.mkdir()
    rows = old_rows()
    source = ORIGINAL / "launch.json"
    model_path = json.loads(source.read_text())["model"]
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    files = [Path(__file__), *locks(), source, ORIGINAL / "transcript.jsonl", ORIGINAL / "complete.json"]
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
        "model": model_path, "torch": torch.__version__, "transformers": transformers.__version__,
        "optimizer_updates": 0, "sha256": {str(p.relative_to(HERE.parent.parent.parent)): digest(p) for p in files},
    }
    (args.output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True, padding_side="left")
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        model_path, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa").eval()

    def generate(batch, stage):
        ids = [tok.encode(tok.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                                 enable_thinking=False), add_special_tokens=False)
               for row, *_ in batch]
        assert max(map(len, ids)) + CAP < 4096
        encoded = tok.pad({"input_ids": ids}, return_tensors="pt")
        with torch.inference_mode():
            predicted = model.generate(**encoded, do_sample=False, max_new_tokens=CAP, eos_token_id=eos,
                                       pad_token_id=tok.pad_token_id)
        out = {}
        with (args.output / f"{stage}.jsonl").open("a") as f:
            for (row, role, menu, option), prefix, tail in zip(
                    batch, ids, predicted[:, encoded.input_ids.shape[-1]:].tolist(), strict=True):
                if eos in tail:
                    tail = tail[:tail.index(eos)+1]
                raw = tok.decode(tail, skip_special_tokens=True).strip()
                result = {**row, "role": role, "query": option, "input_ids": prefix, "output_ids": tail,
                          "output": raw, "judgment": evaluate(raw, row["id"], role, menu, "query", option)}
                out[row["id"]] = result
                f.write(serialize(result) + "\n")
        print(f"{stage}: recorded {len(out)} replies", flush=True)
        return out

    def save(stage, metrics):
        trace = args.output / f"{stage}.jsonl"
        (args.output / f"{stage}-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        (args.output / f"{stage}-receipt.json").write_text(serialize(
            {"optimizer_updates": 0, "sha256": digest(trace), "records": len(trace.read_text().splitlines())}) + "\n")

    batch = list(fixed_specs(rows))
    fixed = {}
    for start in range(0, len(batch), 8):
        fixed.update(generate(batch[start:start+8], "fixed"))
    save("fixed", paired(rows, fixed))
    print("Fixed-query metrics ready.", flush=True)
    if args.wait_for_adaptive and sys.stdin.readline().strip() == "adaptive":
        save("adaptive", adaptive(rows, generate))


if __name__ == "__main__":
    main()
