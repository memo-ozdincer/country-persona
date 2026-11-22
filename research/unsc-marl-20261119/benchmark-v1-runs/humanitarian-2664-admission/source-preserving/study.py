"""Generate and replay a frozen optional-comparison writer on five receipts."""

import argparse
import json
import os
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[1]
RELEASE = RUNS.parent / "benchmark-v1.5"
OUT = HERE / "evidence"
ORDERS = {
    "none": (), "safeguards": ("safeguards",), "india": ("india",),
    "safeguards-first": ("safeguards", "india"), "india-first": ("india", "safeguards"),
}
TASK = (
    "A neutral record already reports the standalone facts in each delivered evidence block. "
    "Supply only an optional comparison between the adopted safeguards and the national "
    "assessment. If fewer than two delivered blocks support a useful comparison, return exactly "
    "NONE. Otherwise write one sentence of at most 38 words using only the delivered blocks. "
    "Explain how the adopted oversight and the national assessment relate while preserving "
    "whose judgment it is. End after the comparison."
)


def load_module(name, path):
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collector = load_module("collector_2664_optional", RUNS / "syria-baseline/collect.py")
anchor = load_module("anchor_2664_optional", HERE.parent / "replay.py")
CASE = anchor.CASE
CARDS = {row["id"]: row["text"] for row in CASE["evidence"]}


def read(path):
    return json.loads(path.read_text())


def plan():
    files = (Path(__file__), HERE / "protocol.md", HERE.parent / "case.json",
             HERE.parent / "replay.py", HERE.parent / "anchors.json",
             HERE.parent / "drafting-crossover/scores.json", Path(collector.__file__),
             RELEASE / "release.json")
    return {
        "pins": {str(p.relative_to(RUNS.parent)): collector.sha(p) for p in files},
        "checkpoint_index_sha256": collector.sha(collector.MODEL / "model.safetensors.index.json"),
        "requests": {
            name: {"id": name, "max_output_tokens": 85, "messages": [
                {"role": "system", "content": TASK},
                {"role": "user", "content": json.dumps({"delivered": [
                    {"kind": key, "text": CARDS[key]} for key in order
                ]}, ensure_ascii=False)},
            ]} for name, order in ORDERS.items()
        },
    }


def locked():
    spec = plan()
    assert spec == read(HERE / "plan.json")
    return spec


def collect(generate, directory):
    for request in locked()["requests"].values():
        reply = generate(request)
        collector.suite.append(directory / "calls.jsonl", {"id": request["id"], "reply": reply})


def run():
    locked()
    assert os.environ.get("CUDA_VISIBLE_DEVICES", "").startswith("GPU-")
    with patch.object(collector, "roster", return_value={"humanitarian-2664": CASE}), patch.object(
        collector, "HERE", HERE), patch.object(collector.suite.e, "HERE", RELEASE), patch.object(
        collector.suite, "collect", collect
    ):
        collector.run(OUT)


def verify():
    from transformers import AutoTokenizer

    spec = locked()
    manifest = read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "launch.json", "tokens.jsonl"}
    assert all(collector.sha(OUT / name) == digest for name, digest in manifest.items())
    launch = read(OUT / "launch.json")
    assert launch["checkpoint_index_sha256"] == spec["checkpoint_index_sha256"]
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["optimizer_updates"] == 0 and launch["release_sha256"] == collector.sha(RELEASE / "release.json")
    tokenizer = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    calls, tokens = ([json.loads(line) for line in (OUT / name).read_text().splitlines()]
                     for name in ("calls.jsonl", "tokens.jsonl"))
    result = {}
    for (name, request), call, trace in zip(spec["requests"].items(), calls, tokens, strict=True):
        assert name == call["id"] and trace["response"] == call["reply"]
        reply = call["reply"]
        assert collector.prompt(tokenizer, request) == trace["input_ids"]
        assert len(trace["input_ids"]) == reply["input_tokens"]
        ids = trace["output_ids"]
        assert 0 < len(ids) == reply["output_tokens"] <= request["max_output_tokens"]
        assert tokenizer.decode(ids, skip_special_tokens=True).strip() == reply["text"]
        assert eos not in ids[:-1] and (ids[-1] == eos) == (reply["termination"] == "complete")
        result[name] = reply
    return {"manifest": manifest, "outputs": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        print(json.dumps({"plan": plan, "verify": verify}[mode](), ensure_ascii=False, indent=2))
