"""Run one frozen, nine-call peer-vs-solo policy workshop on the local 4B base."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

from country_persona.inference_probe import generation_config, stop_trace
from country_persona.io import sha256, write_json

HERE = Path(__file__).resolve().parent
SYSTEM = "You are working on a source-grounded diplomatic workshop. Use the supplied material only. Treat prior submissions as proposals to assess, and keep historical source positions distinct from simulated recommendations."
OPENING = "Give your delegation's opening position in at most 55 words. Name changes you want to W, with a reason."
REVISION = "Give your delegation's revised submission in at most 65 words. State your disposition and any concrete change to W. Explain what you retain, amend or challenge and why."
FINAL = "Write a neutral workshop decision record in at most 120 words. Give the disposition, proposed edits, delegation reasons, unresolved points and authority status. Output only the record."
REVISION_CAP = 125
FINAL_CAP = 210


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    episode = json.loads((HERE / "episode.json").read_text())
    roles = episode["roles"]
    dossier = "\n".join(f'{role["name"]}: {role["evidence"]}' for role in roles)
    brief = f'{episode["episode"]}\n\n{episode["scenario"]}\n\nSource cards:\n{dossier}'
    torch.manual_seed(0)
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    write_json(args.output / "launch.json", {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(args.output.resolve()),
        "device": "cpu", "gpu_uuids": [], "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "torch": torch.__version__, "transformers": transformers.__version__,
        "model_path": str(args.model_path.resolve()), "seed": 0, "dtype": "bfloat16",
        "input_sha256": {p.name: sha256(p) for p in (HERE / "episode.json", HERE / "rubric.json", Path(__file__))},
    })
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    source_config = GenerationConfig(
        eos_token_id=tokenizer.convert_tokens_to_ids("<|im_end|>"), pad_token_id=tokenizer.pad_token_id
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).eval()
    print("Model loaded on CPU", flush=True)

    def generate(case, content, cap, dependencies=()):
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        input_ids = tokenizer.encode(rendered, add_special_tokens=False)
        if len(input_ids) + cap > 4096:
            raise ValueError(f"Context budget exceeded for {case}")
        config, original_eos = generation_config(source_config, tokenizer, cap, "model")
        config.output_scores = config.output_logits = False
        inputs = torch.tensor([input_ids])
        start = time.monotonic()
        with torch.inference_mode():
            result = model.generate(inputs, attention_mask=torch.ones_like(inputs), generation_config=config)
        tokens = result.sequences[0, len(input_ids):].tolist()
        output = tokenizer.decode(tokens, skip_special_tokens=True).strip()
        row = {"id": case, "dependencies": list(dependencies), "messages": messages, "input_ids": input_ids,
               "generated_ids": tokens, "generation_config": config.to_dict(),
               "prompt_tokens": len(input_ids), "generated_tokens": len(tokens), "output": output,
               "generation_seconds": time.monotonic() - start,
               **stop_trace(tokens, config.eos_token_id, original_eos, cap)}
        with (args.output / "transcript.jsonl").open("a") as file:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(case, len(tokens), round(row["generation_seconds"], 2), flush=True)
        return output

    openings = {}
    revisions = {"solo": {}, "peer": {}}
    for role in roles:
        key = role["key"]
        openings[key] = generate(f"opening-{key}", f'{brief}\n\nYour role: {role["name"]}.\n{OPENING}', 105)
    for arm in revisions:
        for role, other in (roles, roles[::-1]):
            key, peer = role["key"], other["key"]
            prior = f'Your opening:\n{openings[key]}'
            dependencies = [f"opening-{key}"]
            if arm == "peer":
                prior += f'\n\nOpening from {other["name"]}:\n{openings[peer]}'
                dependencies.append(f"opening-{peer}")
            else:
                prior += "\n\nYou are revising independently. No peer opening has been supplied."
            content = f'{brief}\n\nYour role: {role["name"]}.\n\n{prior}\n\n{REVISION}'
            revisions[arm][key] = generate(f"{arm}-{key}", content, REVISION_CAP, dependencies)
        submissions = "\n\n".join(f'{r["name"]}:\n{revisions[arm][r["key"]]}' for r in roles)
        deps = [f'{arm}-{r["key"]}' for r in roles]
        generate(f"final-{arm}", f"{brief}\n\nSubmissions:\n{submissions}\n\n{FINAL}", FINAL_CAP, deps)
    generate("final-analyst", f"{brief}\n\n{FINAL}", 2 * 105 + 2 * REVISION_CAP + FINAL_CAP)
    write_json(args.output / "complete.json", {"completed_calls": 9, "transcript_sha256": sha256(args.output / "transcript.jsonl")})


if __name__ == "__main__":
    main()
