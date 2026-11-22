"""Execute the trained sender and reply desk before constructing each record."""
import argparse
from collections import Counter
from itertools import product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
BASE = RUNS / "delisting-2744"
WITNESS = RUNS / "delisting-witness-render"
sys.path.insert(0, str(WITNESS))
import compact
import witness

chair = witness.baseline.chair
read = chair.read
Q = .8
PRICE = 8
PRIORS = ([.6, .2, .2], [.2, .2, .6])


def plan():
    case = read(BASE / "case.json")
    prior = read(WITNESS / "compact-results.json")["compiled"]
    early = tuple(case["early"])
    late = tuple(case["late"])
    public = sum(row["weight"] for row in case["public"])
    both = np.array([[prior[f"{first}/{second}"]["scores"]["admitted"] for second in late] for first in early])
    first = public + np.array([row["weight"] for row in case["early"].values()])
    last = public + np.array([row["weight"] for row in case["late"].values()])
    choices = []
    for mass in PRIORS:
        options = []
        for absent, present in product(range(2), repeat=2):
            base = (1-Q)*public + Q*last[absent]
            gain = Q*((1-Q)*first + Q*both[:, present] - base) - PRICE
            options.append({"send": (gain > 0).astype(int).tolist(), "reply": [absent, present],
                            "archived_utility": round(float(np.array(mass) @ (base + np.maximum(gain, 0))), 8)})
        choices.append(max(options, key=lambda choice: choice["archived_utility"]))
    fit = read(BASE / "results.json")["history"][-1]
    paths = (Path(__file__), HERE / "protocol.md", BASE / "case.json", BASE / "plan.json",
             BASE / "results.json", WITNESS / "witness.py", WITNESS / "compact.py",
             WITNESS / "plan.json", WITNESS / "compact-results.json", Path(chair.__file__))
    return {"q": Q, "price": PRICE, "priors": list(PRIORS), "arrival_policies": choices,
            "sender_weights": fit["sender"][1], "reply_weights": fit["receiver"][1],
            "checkpoint": str(chair.MODEL),
            "checkpoint_index_sha256": chair.pin(chair.MODEL/"model.safetensors.index.json"),
            "pins": {str(path.relative_to(RUNS)): chair.pin(path) for path in paths}}


def gate_queries(side, source, relation, case, system):
    role = {"early": "delegate_statement", "late": "adopted_provision"}[side]
    for established in ("A", "B"):
        payload = {"source_role": role, "source_text": source,
                   "proposition": case["relations"][relation][side+"_claim"],
                   "responses": {letter: "established" if letter == established else "not established"
                                 for letter in ("A", "B")}}
        yield {"messages": [{"role": "system", "content": system},
                            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
               "max_output_tokens": 2}


def execute(spec, call):
    case = read(BASE / "case.json")
    gate_system = read(BASE / "plan.json")["requests"][0]["messages"][0]["content"]
    old_requests = read(WITNESS / "plan.json")["requests"]
    early = {name: json.loads(old_requests[f"{name}/review"]["messages"][1]["content"])["delegate_statement"]
             for name in case["early"]}
    late = {name: row["text"] for name, row in case["late"].items()}
    ids = list(early)
    late_ids = list(late)
    public = [row["text"] for row in case["public"]]

    def check(side, text, relation):
        replies = [call("label", req) for req in gate_queries(side, text, relation, case, gate_system)]
        a, b = [reply["logits"] for reply in replies]
        return round((a["A"] - a["B"] + b["B"] - b["A"]) / 2, 8)

    rows = []
    for setting, (mass, baseline) in enumerate(zip(spec["priors"], spec["arrival_policies"], strict=True)):
        for arm, view, forward_ok, return_ok in product(("learned", "arrival"), ids, (False, True), (False, True)):
            i = ids.index(view)
            features = np.array([1., Q, Q, Q*Q, PRICE/10])
            sent = bool(np.dot(spec["sender_weights"][i], features) > 0) if arm == "learned" else bool(baseline["send"][i])
            arrived = sent and forward_ok
            observation = int(arrived)
            margin = None
            if arm == "learned":
                if arrived:
                    margin = check("early", early[view], "review")
                    observation += int(margin > 0)
                reply = int(spec["reply_weights"][observation] > 0)
            else:
                reply = baseline["reply"][observation]
            document = late_ids[reply]
            record = list(public)
            if arrived:
                record.append(early[view])
            if return_ok:
                record.append(late[document])

            candidate = None
            margins = None
            admitted = False
            relation = None
            if arrived and return_ok:
                sources = {"delegate_statement": early[view], "adopted_document": late[document]}
                request = {"messages": [{"role": "system", "content": witness.SYSTEM},
                                        {"role": "user", "content": json.dumps(sources, ensure_ascii=False)}],
                           "max_output_tokens": witness.BUDGET}
                candidate = compact.compact(call("write", request), sources)
                if candidate["fallback"] is None:
                    relation, = (key for key, connective in witness.CONNECTIVES.items()
                                 if candidate["text"] == connective)
                    margins = [check("early", sources["delegate_statement"], relation),
                               check("late", sources["adopted_document"], relation)]
                    admitted = min(margins) > 0
                    if admitted:
                        record.append(candidate["text"])
            text = " ".join(record)

            # Evaluate after generation. The scorer's key is absent from the requests.
            points = sum(row["weight"] for row in case["public"])
            points += case["early"][view]["weight"] if arrived else 0
            points += case["late"][document]["weight"] if return_ok else 0
            if admitted:
                key = case["relations"][relation]
                points = points + key["weight"] if (key["early"], key["late"]) == (view, document) else 0
            if len(text.split()) > case["word_cap"]:
                points = 0
            weight = mass[i] * (Q if forward_ok else 1-Q) * (Q if return_ok else 1-Q)
            rows.append({"setting": setting, "arm": arm, "view": view, "channel": [forward_ok, return_ok],
                         "branch_weight": round(weight, 8), "sent": sent, "arrived": arrived,
                         "reply_observation": observation, "reply_margin": margin,
                         "reply": document, "reply_delivered": return_ok, "candidate": candidate,
                         "source_gate_margins": margins, "admitted": admitted,
                         "released": points, "utility": points - PRICE*sent, "record": text})
    summaries = []
    for setting in range(len(PRIORS)):
        means = {}
        for arm in ("learned", "arrival"):
            group = [row for row in rows if row["setting"] == setting and row["arm"] == arm]
            assert abs(sum(row["branch_weight"] for row in group)-1) < 1e-8
            means[arm] = {metric: round(sum(row[metric]*row["branch_weight"] for row in group), 8)
                          for metric in ("released", "utility")}
        summaries.append({"prior": PRIORS[setting], "arms": means,
                          "gain": round(means["learned"]["utility"]-means["arrival"]["utility"], 8)})
    return {"summaries": summaries, "branches": rows}


def run(spec):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, __version__

    out = HERE / "evidence"
    device = chair.device_receipt()
    assert device["device"] == "cpu"
    torch.set_num_threads(chair.THREADS)
    torch.set_num_interop_threads(1)
    out.mkdir()
    chair.write(out/"launch.json", device | {
        "host": socket.gethostname(), "pid": os.getpid(),
        "process_start": subprocess.check_output(
            ["ps", "-o", "lstart=", "-p", str(os.getpid())], text=True).strip(),
        "command": [sys.executable, *sys.argv], "run_directory": str(out),
        "plan_sha256": chair.pin(HERE/"plan.json"), "torch": torch.__version__, "transformers": __version__,
        "optimizer_updates": 0,
    })
    tokenizer = AutoTokenizer.from_pretrained(chair.MODEL, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(chair.MODEL, local_files_only=True, dtype=torch.bfloat16,
                                               attn_implementation="sdpa", device_map="cpu").eval()
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    labels = {word: tokenizer.encode(word, add_special_tokens=False) for word in ("A", "B")}
    assert all(len(ids) == 1 for ids in labels.values())
    cache = {}
    operations = Counter()

    with (out/"calls.jsonl").open("w") as stream, torch.inference_mode():
        def call(mode, request):
            operations[mode] += 1
            key = json.dumps([mode, request], ensure_ascii=False, sort_keys=True)
            if key not in cache:
                ids = chair.prompt(tokenizer, request)
                x = torch.tensor([ids])
                attention = torch.ones_like(x)
                if mode == "label":
                    values = model(input_ids=x, attention_mask=attention, use_cache=False,
                                   logits_to_keep=1).logits[0, -1].float()
                    reply = {"logits": {word: values[tokens[0]].item() for word, tokens in labels.items()}}
                    tokens = []
                else:
                    gen = GenerationConfig(max_new_tokens=request["max_output_tokens"], do_sample=False,
                                           eos_token_id=eos, pad_token_id=tokenizer.pad_token_id, use_cache=True)
                    tokens = model.generate(input_ids=x, attention_mask=attention,
                                            generation_config=gen)[0, len(ids):].tolist()
                    reply = {"text": tokenizer.decode(tokens, skip_special_tokens=True).strip(),
                             "termination": "complete" if tokens and tokens[-1] == eos else "cap"}
                cache[key] = reply
                chair.append(stream, {"mode": mode, "request": request, "input_ids": ids,
                                      "output_ids": tokens, "reply": reply})
            return cache[key]

        result = execute(spec, call)
    chair.write(out/"episodes.json", result | {"logical_calls": dict(operations)})
    chair.write(out/"complete.json", {name: chair.pin(out/name) for name in
                                      ("launch.json", "calls.jsonl", "episodes.json")})


def verify(spec):
    from math import isfinite
    from transformers import AutoTokenizer

    out = HERE / "evidence"
    receipt = read(out/"complete.json")
    assert set(receipt) == {"launch.json", "calls.jsonl", "episodes.json"}
    assert all(chair.pin(out/name) == digest for name, digest in receipt.items())
    assert read(out/"launch.json")["plan_sha256"] == chair.pin(HERE/"plan.json")
    tokenizer = AutoTokenizer.from_pretrained(chair.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    cache = {}
    usage = {}
    for line in (out/"calls.jsonl").read_text().splitlines():
        row = json.loads(line)
        mode, request, reply = (row[key] for key in ("mode", "request", "reply"))
        key = json.dumps([mode, request], ensure_ascii=False, sort_keys=True)
        assert key not in cache
        assert chair.prompt(tokenizer, request) == row["input_ids"]
        tokens = row["output_ids"]
        if mode == "label":
            assert set(reply["logits"]) == {"A", "B"} and all(isfinite(x) for x in reply["logits"].values())
            assert not tokens
        else:
            assert tokenizer.decode(tokens, skip_special_tokens=True).strip() == reply["text"]
            assert len(tokens) <= request["max_output_tokens"]
            assert bool(tokens and tokens[-1] == eos) == (reply["termination"] == "complete")
        cache[key] = reply
        usage[key] = (mode, len(row["input_ids"]), len(tokens))
    seen = Counter()
    logical = Counter()

    def call(mode, request):
        key = json.dumps([mode, request], ensure_ascii=False, sort_keys=True)
        seen[key] += 1
        logical[mode] += 1
        return cache[key]

    result = execute(spec, call) | {"logical_calls": dict(logical)}
    assert set(seen) == set(cache)
    assert result == read(out/"episodes.json")
    return {"summaries": result["summaries"], "branches": len(result["branches"]),
            "logical_calls": result["logical_calls"], "physical_calls": dict(Counter(x[0] for x in usage.values())),
            "actual_input_tokens": sum(x[1] for x in usage.values()),
            "generated_tokens": sum(x[2] for x in usage.values()), "receipt": receipt}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    spec = plan()
    if mode != "plan":
        assert spec == read(HERE/"plan.json")
    if mode == "run":
        run(spec)
    else:
        print(json.dumps(spec if mode == "plan" else verify(spec), indent=2))
