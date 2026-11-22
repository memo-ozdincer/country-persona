"""Collect frozen response-choice margins, with replay from the exact stored prompts."""

import argparse
import json
from math import isfinite
import os
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "concern-transfer"
OUT = HERE / "evidence"
sys.path.insert(0, str(PRIOR))
import concern_study as previous

base = previous.earlier
collector = base.collector
OPTIONS = {"process": previous.CARDS["de-process"], "fund": previous.CARDS["de-fund"]}
MAPPINGS = {"ab": {"A": "process", "B": "fund"}, "ba": {"A": "fund", "B": "process"}}
SYSTEM = (
    "You are the German desk preparing a source-faithful Council record. Read the first desk's message, "
    "if any. Choose which one of your two statements should be forwarded. If one statement addresses "
    "the same concrete concern the first desk itself expresses, choose it to enable the exact connection. "
    "Distinguish a stated concern from quoting someone else, explicit disagreement, and discussing a "
    "different stage or policy. If there is no such connection, choose the statement that adds the more "
    "specific substantive standpoint on its own. Return only A or B."
)


def read(path):
    return json.loads(path.read_text())


def cases():
    rows = read(HERE / "messages.json")
    return {row["id"]: row | {"text": previous.CARDS[row["card"]] if "card" in row else row["text"]}
            for row in rows}


def plan():
    files = (Path(__file__), HERE / "protocol.md", HERE / "messages.json", PRIOR / "plan.json",
             PRIOR / "scores.json", PRIOR / "reply-fit.json", Path(collector.__file__),
             Path(base.__file__), previous.RELEASE / "release.json")
    archive = cases()
    assert len(archive) == 15
    return {
        "pins": {str(p.relative_to(previous.RUNS.parent)): collector.sha(p) for p in files},
        "checkpoint_index_sha256": collector.sha(collector.MODEL / "model.safetensors.index.json"),
        "requests": [
            base.earlier.request(f"{key}/{suffix}", 2, SYSTEM, {
                "first_message": row["text"], "your_options": {label: OPTIONS[role] for label, role in mapping.items()},
            })
            for key, row in archive.items() for suffix, mapping in MAPPINGS.items()
        ],
    }


def locked():
    spec = plan()
    assert spec == read(HERE / "plan.json")
    return spec


def run():
    import torch
    from transformers import AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    assert os.environ.get("CUDA_VISIBLE_DEVICES", "").startswith("GPU-")
    requests = locked()["requests"]
    tok = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    labels = base.label_tokens(tok)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    state = {}

    def generate(model, *args, **kwargs):
        vector = kwargs["input_ids"]
        assert vector[0].tolist() == collector.prompt(tok, state["request"])
        scores = model(input_ids=vector, attention_mask=kwargs["attention_mask"], use_cache=False,
                       logits_to_keep=1).logits[0, -1].float()
        logits = {key: scores[index].item() for key, index in labels.items()}
        assert all(isfinite(v) for v in logits.values())
        state["logits"] = logits
        output = torch.tensor([[labels[max(logits, key=logits.get)], eos]], device=vector.device, dtype=vector.dtype)
        return torch.cat((vector, output), dim=-1)

    def collect(call, directory):
        for req in requests:
            state["request"] = req
            result = call(req)
            collector.suite.append(directory / "calls.jsonl", {
                "request": req, "reply": result, "logits": state.pop("logits"),
            })

    with patch.object(GenerationMixin, "generate", generate), patch.object(collector.suite, "collect", collect), patch.object(
        collector, "roster", return_value={"reform-2553-text-reply": previous.CASE}
    ), patch.object(collector, "HERE", HERE), patch.object(collector.suite.e, "HERE", previous.RELEASE):
        collector.run(OUT)


def verify():
    from transformers import AutoTokenizer

    config = locked()
    manifest = read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "launch.json", "tokens.jsonl"}
    assert all(collector.sha(OUT / name) == digest for name, digest in manifest.items())
    launch = read(OUT / "launch.json")
    assert launch["checkpoint_index_sha256"] == config["checkpoint_index_sha256"]
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition" and launch["optimizer_updates"] == 0
    tokenizer = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    labels = base.label_tokens(tokenizer)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    calls, tokens = ([json.loads(line) for line in (OUT / name).read_text().splitlines()]
                     for name in ("calls.jsonl", "tokens.jsonl"))
    outputs = {}
    for req, row, trace in zip(config["requests"], calls, tokens, strict=True):
        assert req == row["request"] and trace["response"] == row["reply"]
        assert trace["input_ids"] == collector.prompt(tokenizer, req)
        logits = row["logits"]
        assert set(logits) == set(labels) and all(isfinite(v) for v in logits.values())
        picked = max(logits, key=logits.get)
        assert trace["output_ids"] == [labels[picked], eos] and row["reply"]["text"] == picked
        assert len(trace["input_ids"]) == row["reply"]["input_tokens"]
        outputs[req["id"]] = {"logits": logits, "reply": row["reply"]}
    return {"manifest": manifest, "outputs": outputs}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        print(json.dumps((plan if mode == "plan" else verify)(), ensure_ascii=False, indent=2))
