"""Test floor-label sensitivity and a five-seat rotation with frozen speech choices."""

import argparse
from itertools import batched
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import local_baseline as baseline
from meeting import FLOOR
from recording import decision_request, verify_run
from run import simulate


ROOT = baseline.HERE.parents[1]
PRIOR = ROOT/"reports/council-workshop-qwen-20261123"


def plan(model):
    root = [Path(__file__), PRIOR/"plan.json", PRIOR/"verification.json"]
    for world in baseline.WORLDS:
        root.extend(PRIOR/world/name for name in ("settings.json", "calls.jsonl", "logits.jsonl"))
    return {"baseline": baseline.plan(model), "floor": "single next seat in cyclic order",
            "slots_include_scripted_floor": True,
            "inputs": {str(path.relative_to(ROOT)): baseline.fingerprint(path) for path in root}}


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def archived(world):
    directory = PRIOR/world
    settings = baseline.read(directory/"settings.json")
    calls = list(batched(jsonl(directory/"calls.jsonl"), 2))
    scores = jsonl(directory/"logits.jsonl")
    assert len(calls) == len(scores) == 1 + len(settings["countries"])
    assert all(pair[0]["schema"] == FLOOR for pair in calls[1:])
    return settings, calls, scores


def reversed_floor(request):
    options, messages = baseline.input_for(request["prompt"], FLOOR)
    options = dict(zip(options, reversed(options.values()), strict=True))
    payload = json.loads(messages[1]["content"])
    payload["choices"] = options
    messages[1]["content"] = json.dumps(payload, ensure_ascii=False)
    return options, messages


def scheduled_floor(settings, country, prompt):
    decoder = json.JSONDecoder()
    view = decoder.raw_decode(prompt[prompt.index("{"):])[0]["public"]
    order = settings["countries"]
    previous = view["history"][-1]["country"]
    next_country = order[(order.index(previous) + 1) % len(order)]
    return {"action": "request_floor" if country == next_country else "pass"}


def collect_probes(out, score):
    for world in baseline.WORLDS:
        _, calls, scores = archived(world)
        for index, ((request, _), original) in enumerate(zip(calls[1:], scores[1:], strict=True), 1):
            choices, messages = reversed_floor(request)
            observation = score(choices, messages)
            baseline.append(out/"floor-probes.jsonl", {
                "world": world, "index": index, "country": request["country"],
                "original_logits": original["logits"], **observation,
            })


def collect_rotation(out, score):
    for world in baseline.WORLDS:
        settings, calls, scores = archived(world)
        directory = out/world
        directory.mkdir()
        baseline.write(directory/"settings.json", settings)
        count = 0

        def call(country, prompt, schema):
            nonlocal count
            request = decision_request(settings, country, prompt, schema)
            if count == 0:
                assert request == calls[0][0]
                answer = calls[0][1]["answer"]
                source = "archived_opening"
            elif schema == FLOOR:
                answer = scheduled_floor(settings, country, prompt)
                source = "fixed_floor"
            else:
                choices, messages = baseline.input_for(prompt, schema)
                observation = score(choices, messages)
                selected = max(choices, key=observation["logits"].get)
                answer = choices[selected]
                baseline.append(directory/"logits.jsonl", {"index": count, **observation})
                source = "model_speech"
            baseline.append(directory/"calls.jsonl", request)
            baseline.append(directory/"calls.jsonl", dict(event="response", country=country, answer=answer,
                                                            origin=source, reused=count == 0))
            count += 1
            return answer

        result = simulate(settings["case"], settings["countries"], "meeting", settings["turn_cap"],
                          False, call, settings["call_cap"])
        baseline.write(directory/"result.json", result)
        print(world, result["status"], result["calls"], result["mandate_score"], flush=True)


def run(model_path, out, gpu):
    placement = baseline.device(gpu)
    if os.environ.get("CUDA_VISIBLE_DEVICES") != gpu:
        raise RuntimeError("Set CUDA_VISIBLE_DEVICES to the selected GPU UUID")
    if plan(model_path) != baseline.read(out/"plan.json"):
        raise ValueError("Inputs differ from the frozen plan")
    with (out/"launch.json").open("x") as raw:
        json.dump(placement | {
            "host": socket.gethostname(), "pid": os.getpid(),
            "started": subprocess.check_output(["ps", "-p", str(os.getpid()), "-o", "lstart="], text=True).strip(),
            "command": [sys.executable, *sys.argv], "run_directory": str(out.resolve()),
            "plan_sha256": baseline.fingerprint(out/"plan.json"),
        }, raw, indent=2)
        raw.write("\n")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, local_files_only=True, dtype=torch.bfloat16,
        attn_implementation="sdpa", device_map=placement["placement"],
    ).eval()

    def score(choices, messages):
        ids = baseline.token_ids(tokenizer, messages)
        tokens = {letter: tokenizer.encode(letter, add_special_tokens=False) for letter in choices}
        assert all(len(index) == 1 for index in tokens.values())
        with torch.inference_mode():
            x = torch.tensor([ids], device=placement["placement"])
            y = model(input_ids=x, attention_mask=torch.ones_like(x), use_cache=False,
                      logits_to_keep=1).logits[0, 0].float()
        return {"input_ids": ids, "logits": {letter: y[index[0]].item() for letter,index in tokens.items()}}

    collect_probes(out, score)
    collect_rotation(out, score)


def verify(model_path, out):
    from math import isfinite
    from transformers import AutoTokenizer

    assert baseline.read(out/"plan.json") == plan(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    probes = iter(jsonl(out/"floor-probes.jsonl"))
    results = {}
    for world in baseline.WORLDS:
        settings, prior_calls, prior_scores = archived(world)
        floor = []
        for index, ((request, response), original) in enumerate(zip(prior_calls[1:], prior_scores[1:], strict=True), 1):
            saved = next(probes)
            choices, messages = reversed_floor(request)
            assert (saved["world"], saved["index"], saved["country"]) == (world, index, request["country"])
            assert saved["input_ids"] == baseline.token_ids(tokenizer, messages)
            assert saved["original_logits"] == original["logits"]
            assert set(choices) == set(saved["logits"]) and all(map(isfinite, saved["logits"].values()))
            old_margin = saved["original_logits"]["A"] - saved["original_logits"]["B"]
            new_margin = saved["logits"]["B"] - saved["logits"]["A"]
            assert response["answer"]["action"] == "pass"
            floor.append({"country": request["country"], "original_request_minus_pass": old_margin,
                          "swapped_request_minus_pass": new_margin,
                          "averaged_request_minus_pass": (old_margin+new_margin)/2})
        directory = out/world
        assert baseline.read(directory/"settings.json") == settings
        result = verify_run(directory, simulate)
        log = list(batched(jsonl(directory/"calls.jsonl"), 2))
        observations = {row["index"]: row for row in jsonl(directory/"logits.jsonl")}
        for index, (request, response) in enumerate(log):
            if index == 0:
                assert request == prior_calls[0][0] and response["answer"] == prior_calls[0][1]["answer"]
                assert response["origin"] == "archived_opening"
            elif request["schema"] == FLOOR:
                assert response["answer"] == scheduled_floor(settings, request["country"], request["prompt"])
                assert response["origin"] == "fixed_floor"
            else:
                row = observations.pop(index)
                choices, messages = baseline.input_for(request["prompt"], request["schema"])
                assert row["input_ids"] == baseline.token_ids(tokenizer, messages)
                assert set(choices) == set(row["logits"]) and all(map(isfinite, row["logits"].values()))
                assert response["answer"] == choices[max(choices, key=row["logits"].get)]
                assert response["origin"] == "model_speech"
        assert not observations and len(log) == result["calls"]
        results[world] = {"floor_probes": floor, "turns": len(result["history"]),
                          "decision_slots": result["calls"], "fresh_speeches": len(result["history"])-1,
                          "status": result["status"], "exclusions": result["exclusions"],
                          **result["mandate_score"]}
    assert next(probes, None) is None
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--gpu")
    args = parser.parse_args()
    if args.mode == "run":
        run(args.model, args.out, args.gpu)
    else:
        value = plan(args.model) if args.mode == "plan" else verify(args.model, args.out)
        print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
