"""Run or verify a frozen Qwen policy for the finite mandate workshop."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import socket
import subprocess
import sys

from meeting import FLOOR, PACKAGE_SPEECH
from recording import decision_request, verify_run
from run import HERE, simulate


WORLDS = ("feasible", "impasse")
TURN_CAP = 20
CALL_CAP = 50
SYSTEM = (
    "Choose the next action for this delegate in a fictional Council workshop. "
    "Follow the delegate's private mandate and use public exclusions and other "
    "delegates' past actions to determine whether a deal is possible. Aim for a "
    "valid unanimous package or a certified impasse. Output the letter for one "
    "of the available decisions, with no explanation."
)


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def append(path, value):
    with path.open("a") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")


def fingerprint(path):
    return sha256(path.read_bytes()).hexdigest()


def input_for(prompt, schema):
    packet = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]
    public = packet["public"]
    if schema == FLOOR:
        choices = [{"action": action} for action in ("request_floor", "pass")]
    elif schema == PACKAGE_SPEECH:
        options = public["options"]
        allowed = set(packet["private_mandate"]["allowed_packages"])
        exclusions = public["exclusions"]
        proposals = sorted(label for label, clause in options.items() if clause != public["draft"])
        choices = [
            ("accept", "I accept the current package."),
            ("yield_floor", "I yield the floor."),
            ("walk_away", "I leave the meeting."),
        ]
        choices += [("propose", label) for label in proposals]
        choices += [("rule_out", label) for label in sorted(options.keys() - allowed - exclusions.keys())]
        if options.keys() == exclusions.keys():
            choices.append(("declare_impasse", "Every option has a verified rejection."))
        choices = [{"action": action, "version": public["version"], "text": text}
                   for action, text in choices]
    else:
        raise ValueError("The local baseline supports finite workshops without advisory ballots")
    options = {chr(ord("A") + i): item for i, item in enumerate(choices)}
    text = json.dumps({"meeting": packet, "choices": options}, ensure_ascii=False)
    return options, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]


def token_ids(tokenizer, messages):
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                             enable_thinking=False)
    return tokenizer.encode(rendered, add_special_tokens=False)


def plan(model):
    files = [Path(__file__), HERE/"meeting.py", HERE/"mandates.py", HERE/"run.py",
             HERE/"recording.py", *(HERE/f"climate-packages-{world}.json" for world in WORLDS)]
    return {"model": str(model), "model_index_sha256": fingerprint(model/"model.safetensors.index.json"),
            "worlds": list(WORLDS), "turn_cap": TURN_CAP, "call_cap": CALL_CAP, "vote": False,
            "files": {path.name: fingerprint(path) for path in files}}


def device(gpu):
    args = ["nvidia-smi", "-i", gpu]
    raw = subprocess.check_output([*args, "--query-gpu=uuid,name,memory.used",
                                   "--format=csv,noheader,nounits"], text=True)
    uuid, name, used = (field.strip() for field in raw.split(","))
    processes = subprocess.check_output([*args, "--query-compute-apps=pid", "--format=csv,noheader"], text=True)
    if uuid != gpu or used != "0" or processes.strip():
        raise RuntimeError("The requested GPU must be idle at launch")
    return {"gpu_uuid": uuid, "gpu_name": name, "placement": "cuda:0"}


def run(model_path, out, gpu):
    import os

    placement = device(gpu)
    if os.environ.get("CUDA_VISIBLE_DEVICES") != gpu:
        raise RuntimeError("Set CUDA_VISIBLE_DEVICES to the selected GPU UUID")
    spec = plan(model_path)
    if spec != read(out/"plan.json"):
        raise ValueError("The live inputs changed after the plan was frozen")
    out.joinpath("launch.json").open("x").close()
    write(out/"launch.json", placement | {
        "host": socket.gethostname(), "pid": os.getpid(),
        "started": subprocess.check_output(["ps", "-p", str(os.getpid()), "-o", "lstart="], text=True).strip(),
        "argv": [sys.executable, *sys.argv], "run_directory": str(out),
        "plan_sha256": fingerprint(out/"plan.json"),
    })
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, local_files_only=True, dtype=torch.bfloat16,
        attn_implementation="sdpa", device_map=placement["placement"],
    ).eval()
    for world in WORLDS:
        case = read(HERE/f"climate-packages-{world}.json")
        settings = {"model": "Qwen3.5-4B", "case": case, "countries": list(case["delegations"]),
                    "mode": "meeting", "turn_cap": TURN_CAP, "call_cap": CALL_CAP, "vote": False}
        directory = out/world
        directory.mkdir()
        write(directory/"settings.json", settings)

        def call(country, prompt, schema):
            request = decision_request(settings, country, prompt, schema)
            append(directory/"calls.jsonl", request)
            choices, messages = input_for(prompt, schema)
            ids = token_ids(tokenizer, messages)
            letters = {letter: tokenizer.encode(letter, add_special_tokens=False) for letter in choices}
            if any(len(value) != 1 for value in letters.values()):
                raise ValueError("A choice letter requires more than one token")
            with torch.inference_mode():
                x = torch.tensor([ids], device=placement["placement"])
                y = model(input_ids=x, attention_mask=torch.ones_like(x), use_cache=False,
                          logits_to_keep=1).logits[0, 0].float()
                logits = {letter: y[index[0]].item() for letter, index in letters.items()}
            selected = max(choices, key=logits.get)
            answer = choices[selected]
            append(directory/"logits.jsonl", {"country": country, "input_ids": ids, "logits": logits})
            append(directory/"calls.jsonl", dict(event="response", country=country, answer=answer, reused=False))
            return answer

        result = simulate(case, settings["countries"], "meeting", TURN_CAP, False, call, CALL_CAP)
        write(directory/"result.json", result)
        print(world, result["status"], result["calls"], result["mandate_score"]["reward"], flush=True)


def verify(out, model_path):
    from itertools import batched
    from math import isfinite
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    if plan(model_path) != read(out/"plan.json"):
        raise ValueError("The replay inputs differ from the locked plan")
    summaries = {}
    for world in WORLDS:
        directory = out/world
        result = verify_run(directory, simulate)
        log = [json.loads(line) for line in (directory/"calls.jsonl").read_text().splitlines()]
        observations = [json.loads(line) for line in (directory/"logits.jsonl").read_text().splitlines()]
        total_tokens = 0
        for (request, response), scored in zip(batched(log, 2), observations, strict=True):
            choices, messages = input_for(request["prompt"], request["schema"])
            ids = token_ids(tokenizer, messages)
            assert request["country"] == scored["country"] and ids == scored["input_ids"]
            assert set(choices) == set(scored["logits"]) and all(map(isfinite, scored["logits"].values()))
            assert response["answer"] == choices[max(choices, key=scored["logits"].get)]
            total_tokens += len(ids)
        assert len(observations) == result["calls"]
        summaries[world] = {
            "turns": len(result["history"]), "calls": result["calls"], "input_tokens": total_tokens,
            "status": result["status"], "exclusions": result["exclusions"], **result["mandate_score"],
        }
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--gpu")
    args = parser.parse_args()
    if args.mode == "run":
        run(args.model, args.out, args.gpu)
    else:
        data = plan(args.model) if args.mode == "plan" else verify(args.out, args.model)
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
