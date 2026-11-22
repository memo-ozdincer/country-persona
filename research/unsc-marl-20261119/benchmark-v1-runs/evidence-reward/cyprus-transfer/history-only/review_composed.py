"""Verify and score the source-only paragraph composed with the public proof."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import compose as c

HERE = Path(__file__).resolve().parent
e = c.check.e


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def row(file):
    one, = [json.loads(line) for line in (c.RUN / file).read_text().splitlines()]
    return one


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    pins = e.read(c.RUN / "complete.json")
    assert set(pins) == {"tokens.jsonl", "calls.jsonl", "launch.json", "inputs.json"}
    assert all(digest(c.RUN / file) == expected for file, expected in pins.items())
    assert all(digest(HERE.parent / file) == expected
               for file, expected in e.read(c.RUN / "inputs.json").items())
    call = row("calls.jsonl")
    trace = row("tokens.jsonl")
    request = call["request"]
    assert request == c.request() == e.read(HERE / "request.json")
    assert trace["response"] == call["reply"]
    launch = e.read(c.RUN / "launch.json")
    before = e.read(c.t.RUN / "launch.json")
    for key in ("checkpoint", "checkpoint_index_sha256", "gpu_name", "decoding", "dtype", "attention",
                "optimizer_updates"):
        assert launch[key] == before[key]
    model = Path(launch["checkpoint"])
    assert digest(model / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    template = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (model / "chat_template.jinja").read_text())
    chat = template.render(messages=request["messages"], add_generation_prompt=True,
                           enable_thinking=False, tools=None)
    tok = Tokenizer.from_file(str(model / "tokenizer.json"))
    ids = tok.encode(chat, add_special_tokens=False).ids
    assert ids == trace["input_ids"] and len(ids) == call["reply"]["input_tokens"]
    eos = tok.token_to_id("<|im_end|>")
    out = trace["output_ids"]
    assert out and eos not in out[:-1] and len(out) == call["reply"]["output_tokens"] <= request["max_output_tokens"]
    assert (out[-1] == eos) == (call["reply"]["termination"] == "complete")
    assert tok.decode(out, skip_special_tokens=True).strip() == call["reply"]["text"]
    record = c.record()
    assert record["text"].endswith("\n\n" + call["reply"]["text"])
    return {"native_calls": 1, "optimizer_updates": launch["optimizer_updates"], "exact_suffix": True,
            "historical_words": len(record["historical"].split()), "record_words": len(record["text"].split())}


def submission():
    base, _, _ = c.check.deck()["compiled"]
    case = base | {"id": "cyprus-transfer-composed"}
    record = c.record()
    calls = [{}, {}, {"text": record["text"], "termination": record["termination"]}]
    return case, calls, e.final_packet(case, calls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "packet", "score"))
    mode = parser.parse_args().mode
    if mode == "verify":
        e.emit(verify())
    else:
        case, calls, packet = submission()
        e.emit(packet if mode == "packet" else e.final_score(case, calls, e.read(HERE / "mark.json")))
