"""Public-state clarification with frozen role-local language responders."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from hashlib import sha256

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scalar"))
from scalar_protocol import ROOT, SCALAR_FORMAT, admit, request, serialize, summarize
from protocol import CAP, SYSTEM, inputs, packet

FAMILIES = ("iraq-unami-mandate-review-2023", "syria-cross-border-aid-july-2023")
OPTIONS = "ABCD"
VARIANTS = ("overlap", "impasse")
ARMS = ("free", "query")
CONTINUATIONS = 4


def cases():
    source, refs = inputs()
    for family in source["families"]:
        if family["id"] not in FAMILIES:
            continue
        for variant in family["variants"]:
            if variant["id"] not in VARIANTS:
                continue
            views = [packet(family, variant, source["boundary"], f"role-{i}") for i in (1, 2)]
            for view in views:
                del view["task"]
            yield (family["id"], variant["id"]), (
                family["roles"], views, refs["families"][family["id"]]["workshop_refs_only"][variant["id"]])


def select(roles, claims, step):
    """Prefer testing the complement of a public acceptance, then unknowns."""
    signs = {(claims_row["role"], option): field for claims_row in claims
             for field in ("accepts", "excludes") for option in claims_row[field]}
    open_options = [o for o in OPTIONS if not any(signs.get((role, o)) == "excludes" for role in roles)
                    and not all(signs.get((role, o)) == "accepts" for role in roles)]
    preferred = (1 + step) % 2
    if not open_options:
        return preferred, None
    candidates = [(not (signs.get((roles[1-i], o)) == "accepts"), i != preferred, o, i)
                  for o in open_options for i in (0, 1) if (roles[i], o) not in signs]
    _, _, option, i = min(candidates)
    return i, option


def plan(id_, view, claims, arm, option=None):
    task = SCALAR_FORMAT
    if arm == "query":
        task += (f" Answer the facilitator's question: under your private condition, can you accept package {option}? "
                 f"Use option {option} and either accept or exclude, according to your own private condition."
                 if option else " The facilitator asks you to pass. Use a null option.")
    else:
        task += " Choose a truthful new signed claim. Avoid repeating a signed claim already made by your role."
    return {"id": id_, "cap": CAP, "messages": [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": serialize({"role_view": view, "public_disclosures": claims, "task": task})}]}


def evaluate(raw, record_id, role, menu, arm=None, option=None):
    judged = admit(raw, record_id, role, menu)
    claim = judged["admitted"]
    if arm == "query" and judged["kind"] in {"disclosure", "pass"}:
        if (option is None and claim) or (option is not None and
                (not claim or claim["accepts"] + claim["excludes"] != [option])):
            return {"kind": "off_query", "admitted": None}
    return judged


def experiment(generate):
    """Shared openings, then an identical four-call ceiling and evidence budget."""
    worlds = dict(cases())
    opening_specs = {}
    for key, (roles, views, truth) in worlds.items():
        family, variant = key
        for i in (0, 1):
            id_ = f"{family}/{variant if i else 'shared'}/open-{i}"
            spec = (request(id_, views[i]), roles[i], truth["allowed_by_role"][i], None, None)
            assert opening_specs.setdefault(id_, spec) == spec
    opened = generate(list(opening_specs.values()))
    states = {}
    for key in worlds:
        family, variant = key
        initial = [opened[f"{family}/shared/open-0"], opened[f"{family}/{variant}/open-1"]]
        for arm in ARMS:
            states[(*key, arm)] = initial.copy()

    for step in range(CONTINUATIONS):
        specs = []
        for (family, variant, arm), rows in states.items():
            roles, views, truth = worlds[family, variant]
            claims = [row["judgment"]["admitted"] for row in rows if row["judgment"]["admitted"]]
            i, option = select(roles, claims, step) if arm == "query" else ((step+1) % 2, None)
            id_ = f"{family}/{variant}/{arm}-{step}"
            specs.append((plan(id_, views[i], claims, arm, option), roles[i], truth["allowed_by_role"][i], arm, option))
        batch = generate(specs)
        for key, spec in zip(states, specs, strict=True):
            states[key].append(batch[spec[0]["id"]])

    result = {}
    for (family, variant, arm), rows in states.items():
        roles, _, truth = worlds[family, variant]
        snapshots = [summarize(roles, truth, rows[:2+step]) for step in range(CONTINUATIONS+1)]
        first = next((step for step, snap in enumerate(snapshots) if snap["correct"]), None)
        result[f"{family}/{variant}/{arm}"] = {
            "first_certified_after_continuation": first,
            "states": [snap["readout"]["state"] for snap in snapshots],
            "novel_claims_by_checkpoint": [snap["distinct_valid_claims"] for snap in snapshots],
            "final": snapshots[-1], "off_query": sum(r["judgment"]["kind"] == "off_query" for r in rows),
            "calls": len(rows), "generation_cap": sum(r["cap"] for r in rows),
            "input_tokens": sum(len(r["input_ids"]) for r in rows),
            "generated_tokens": sum(len(r["output_ids"]) for r in rows),
        }
    return result


def locks():
    return (Path(__file__), HERE.parent / "protocol.py", HERE.parent / "scalar/scalar_protocol.py",
            *(ROOT / name for name in ("decision_ledger.py", "packets.py", "references.json", "workshops.json")))


def main():
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    launch = {
        "host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
        "model": str(args.model.resolve()), "torch": torch.__version__, "transformers": transformers.__version__,
        "optimizer_updates": 0, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in locks()},
    }
    (args.output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    tok = AutoTokenizer.from_pretrained(args.model, local_files_only=True, padding_side="left")
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa").eval()
    transcript = args.output / "transcript.jsonl"

    def generate(specs):
        start = time.monotonic()
        ids = [tok.encode(tok.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                                 enable_thinking=False), add_special_tokens=False)
               for row, *_ in specs]
        assert max(map(len, ids)) + CAP < 4096
        encoded = tok.pad({"input_ids": ids}, return_tensors="pt")
        with torch.inference_mode():
            generated = model.generate(**encoded, do_sample=False, max_new_tokens=CAP,
                                       eos_token_id=eos, pad_token_id=tok.pad_token_id)
        elapsed = time.monotonic() - start
        result = {}
        with transcript.open("a") as out:
            for (row, role, menu, arm, option), prefix, tail in zip(
                    specs, ids, generated[:, encoded.input_ids.shape[-1]:].tolist(), strict=True):
                if eos in tail:
                    tail = tail[:tail.index(eos)+1]
                raw = tok.decode(tail, skip_special_tokens=True).strip()
                record = {**row, "role": role, "query": option, "input_ids": prefix,
                          "output_ids": tail, "output": raw, "judgment": evaluate(raw, row["id"], role, menu, arm, option)}
                result[row["id"]] = record
                out.write(serialize(record) + "\n")
        print(f"{len(result)} replies in {elapsed:.1f}s", flush=True)
        return result

    metrics = experiment(generate)
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (args.output / "complete.json").write_text(serialize({
        "optimizer_updates": 0, "transcript_sha256": sha256(transcript.read_bytes()).hexdigest()
    }) + "\n")


if __name__ == "__main__":
    main()
