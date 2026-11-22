"""Check exact adapter inputs and apply the witness rubric to writer controls."""
import argparse
import json
from pathlib import Path

import controls as c

HERE = Path(__file__).resolve().parent
RUN = HERE / "evidence"
e = c.review.e


def rows(name):
    return [json.loads(line) for line in (RUN / name).read_text().splitlines()]


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    digest = c.review.digest
    hashes = e.read(RUN / "complete.json")
    assert set(hashes) == {"launch.json", "calls.jsonl", "inputs.json", "tokens.jsonl"}
    assert all(digest(RUN / name) == value for name, value in hashes.items())
    assert all(digest(HERE.parent / name) == value for name, value in e.read(RUN / "inputs.json").items())
    assert c.deck() == e.read(HERE / "requests.json")
    launch = e.read(RUN / "launch.json")
    previous = e.read(c.w.RUN / "launch.json")
    for field in ("checkpoint", "checkpoint_index_sha256", "gpu_name", "decoding", "dtype", "attention", "optimizer_updates"):
        assert launch[field] == previous[field]
    model = Path(launch["checkpoint"])
    assert digest(model / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    tokenizer = Tokenizer.from_file(str(model / "tokenizer.json"))
    template = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (model / "chat_template.jinja").read_text())
    eos = tokenizer.token_to_id("<|im_end|>")
    for (label, expected), call, native in zip(c.deck().items(), rows("calls.jsonl"), rows("tokens.jsonl"), strict=True):
        assert label == call["id"] and expected == call["request"]
        rendered = template.render(messages=expected["messages"], add_generation_prompt=True,
                                   enable_thinking=False, tools=None)
        tokens = tokenizer.encode(rendered, add_special_tokens=False).ids
        response, output = native["response"], native["output_ids"]
        assert native["input_ids"] == tokens and len(tokens) == response["input_tokens"]
        assert call["reply"] == response and len(output) == response["output_tokens"] <= expected["max_output_tokens"]
        assert output and eos not in output[:-1] and (output[-1] == eos) == (response["termination"] == "complete")
        assert tokenizer.decode(output, skip_special_tokens=True).strip() == response["text"]
    return {"verified_new_calls": len(rows("calls.jsonl")), "optimizer_updates": launch["optimizer_updates"]}


def packets():
    _, base, _ = c.review.records()["pivotal/learned"]
    result = {}
    for call in rows("calls.jsonl"):
        case = base | {"id": call["id"]}
        calls = [{}, {}, call["reply"]]
        result[call["id"]] = case, calls, e.final_packet(case, calls)
    return result


def score():
    marks = e.read(HERE / "marks.json")
    deck = packets()
    assert set(marks) == {packet["id"] for _, _, packet in deck.values()}
    return {label: e.final_score(case, calls, marks[packet["id"]])
            for label, (case, calls, packet) in deck.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "packets", "score"))
    mode = parser.parse_args().mode
    e.emit({"verify": verify, "packets": lambda: {k: row[2] for k, row in packets().items()}, "score": score}[mode]())
