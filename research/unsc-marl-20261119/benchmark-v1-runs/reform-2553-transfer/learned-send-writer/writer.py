"""Generate and verify native briefs for the changed Belgium dispatch."""
import argparse
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RUNS = PARENT.parent
RELEASE = RUNS.parent / "benchmark-v1.5"
SPLIT = RUNS / (
    "cooperative-rollout-fit/evidence-choice/receipt-conditioned/sampled-return/"
    "listener-residual/private-opener/split-results.json"
)


def module(name, path):
    spec = spec_from_file_location(name, path)
    result = module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


test = module("evidence_2553_transfer", PARENT / "transfer.py")
base = test.old.tribunals.wire.n.base
CASE = test.CASE
OUT = HERE / "evidence"
SYSTEM = (
    "You are the Secretariat drafting a neutral decision record. Use only the public blocks "
    "and the delivered delegation notes. Attribute a position or rationale to its own speaker. "
    "Separate national comments from what the Council actually adopted. When two delivered notes "
    "support a specific overlap or distinction, state it precisely. Treat a missing note as an "
    "evidence gap. Preserve dates, document identifiers, qualifications, and distinct reasons. "
    "Write one concise brief in at most 175 words."
)


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def key(parts):
    return "final-" + sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:16]


def plan():
    rate, prior = .75, .75
    rows = test.READ(SPLIT)["transfer"]["germany_later"]["rows"]
    row, = [x for x in rows if x["delivery"] == rate and x["prior"] == prior]
    fixed, learned = row["actions"]["fixed"], row["actions"]["split_fit"]
    assert fixed[0] == learned[0] and fixed[1] != learned[1]
    menus = [CASE["owned"][i] for i in test.ORDERS["germany_later"]]
    public = CASE["public"]
    by_id, branches = {}, []
    for early, mask in product(range(2), range(8)):
        probability = (prior if early == 0 else 1-prior) * rate**mask.bit_count() * (1-rate)**(3-mask.bit_count())
        if not mask & 4:
            branches.append({"early": early, "mask": mask, "probability": probability, "pair": []})
            continue
        pair, scores = [], []
        for later, third in (fixed, learned):
            choices = (later[early+1 if mask & 2 else 0], early, third)
            cards = [menu[choice] for i,(menu,choice) in enumerate(zip(menus,choices,strict=True)) if mask & 1<<i]
            data = {"task": CASE["task"], "public": [(c["id"],c["text"]) for c in public],
                    "delivered": [(c["id"],c["text"]) for c in cards]}
            id_ = key(data)
            by_id[id_] = {"request": {"id": id_, "max_output_tokens": 280, "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
            ]}, "visible_sources": [c["id"] for c in public + cards]}
            scores.append(test.render([c["id"] for c in cards])["score"]["released_70"])
            pair.append(id_)
        branches.append({"early": early, "mask": mask, "probability": probability,
                         "pair": pair, "typed_scores": scores})
    assert len(by_id) == 12 and sum(x["probability"] for x in branches) == 1.
    typed_delta = sum(x["probability"] * (x["typed_scores"][1] - x["typed_scores"][0])
                      for x in branches if x["pair"])
    assert abs(typed_delta - (row["scores"]["split_fit"] - row["scores"]["fixed"])) < 1e-9
    files = (Path(__file__), HERE / "protocol.md", SPLIT, PARENT / "docket.json",
             PARENT / "transfer.py", Path(base.__file__), RELEASE / "release.json")
    return {"requests": {k:by_id[k] for k in sorted(by_id)}, "branches": branches,
            "typed_delta": typed_delta, "checkpoint_index_sha256": pin(base.MODEL / "model.safetensors.index.json"),
            "pins": {str(p.relative_to(RUNS.parent)): pin(p) for p in files}}


def locked():
    built = plan()
    assert built == test.READ(HERE / "plan.json")
    return built


def run():
    protocol = locked()
    gpu = os.environ["CUDA_VISIBLE_DEVICES"]
    record = subprocess.check_output(["nvidia-smi", "-i", gpu, "--query-gpu=memory.used,utilization.gpu",
                                      "--format=csv,noheader,nounits"], text=True).strip()
    assert record == "0, 0", record

    def collect(generate, directory):
        for row in protocol["requests"].values():
            req = row["request"]
            base.suite.append(directory / "calls.jsonl", {"id": req["id"], "response": generate(req)})

    with patch.object(base, "roster", return_value={CASE["id"]: CASE}), patch.object(base, "HERE", HERE), patch.object(
        base.suite, "collect", collect
    ), patch.object(base.suite.e, "HERE", RELEASE):
        base.run(OUT)


def verify():
    from transformers import AutoTokenizer

    protocol = locked()
    manifest = test.READ(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "launch.json", "tokens.jsonl"}
    assert all(pin(OUT / file) == digest for file,digest in manifest.items())
    launch = test.READ(OUT / "launch.json")
    assert launch["optimizer_updates"] == 0
    assert launch["release_sha256"] == pin(RELEASE/"release.json")
    assert launch["checkpoint_index_sha256"] == protocol["checkpoint_index_sha256"]
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    calls, tokens = ([json.loads(line) for line in (OUT/file).read_text().splitlines()]
                     for file in ("calls.jsonl","tokens.jsonl"))
    packets = {}
    for (id_, row), call, trace in zip(protocol["requests"].items(), calls, tokens, strict=True):
        assert call["id"] == id_ and call["response"] == trace["response"]
        req, reply = row["request"], call["response"]
        tokens_in, tokens_out = trace["input_ids"], trace["output_ids"]
        assert tokens_in == base.prompt(tok, req) and len(tokens_in) == reply["input_tokens"]
        assert tok.decode(tokens_out, skip_special_tokens=True).strip() == reply["text"]
        assert len(tokens_out) == reply["output_tokens"] <= 280
        assert (bool(tokens_out) and tokens_out[-1] == eos) == (reply["termination"] == "complete")
        packets[id_] = {"visible_sources": row["visible_sources"], "reply": reply}
    return {"packets": packets, "manifest": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan","run","verify"))
    command = parser.parse_args().mode
    if command == "run":
        run()
    else:
        print(json.dumps({"plan":plan, "verify":verify}[command](), ensure_ascii=False, indent=2))
