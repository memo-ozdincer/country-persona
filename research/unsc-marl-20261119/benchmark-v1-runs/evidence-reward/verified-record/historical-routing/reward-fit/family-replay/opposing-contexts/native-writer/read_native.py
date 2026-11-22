"""Verify, prepare blinded record packets, and score the matched writer run."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import natural_writer as n

e = n.matched.e


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def calls():
    plan = n.read(n.HERE / "plan.json")
    assert plan == n.plan()
    rows = n.lines(n.OUT / "calls.jsonl")
    assert [r["mask"] for r in rows] == [r["mask"] for r in plan["requests"]]
    assert all(r["request"] == p["request"] for r, p in zip(rows, plan["requests"], strict=True))
    return rows


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    manifest = n.read(n.OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "tokens.jsonl", "launch.json"}
    assert all(digest(n.OUT / name) == seal for name, seal in manifest.items())
    launch = n.read(n.OUT / "launch.json")
    assert launch["optimizer_updates"] == 0 and launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    checkpoint = Path(launch["checkpoint"])
    assert digest(checkpoint / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    tokenizer = Tokenizer.from_file(str(checkpoint / "tokenizer.json"))
    template = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (checkpoint / "chat_template.jinja").read_text())
    eos = tokenizer.token_to_id("<|im_end|>")
    seen = calls()
    for call, token in zip(seen, n.lines(n.OUT / "tokens.jsonl"), strict=True):
        req, response = call["request"], call["response"]
        text = template.render(messages=req["messages"], enable_thinking=False,
                               add_generation_prompt=True, tools=None)
        assert tokenizer.encode(text, add_special_tokens=False).ids == token["input_ids"]
        assert response == token["response"] and response["input_tokens"] == len(token["input_ids"])
        out = token["output_ids"]
        assert out and eos not in out[:-1] and len(out) == response["output_tokens"] <= req["max_output_tokens"]
        assert (out[-1] == eos) == (response["termination"] == "complete")
        assert tokenizer.decode(out, skip_special_tokens=True).strip() == response["text"]
    return {"calls": len(seen), "all_tokens_replayed": True, "optimizer_updates": 0, "launch": launch}


def packets():
    _, case, _ = n.setup()
    case = {"id": case["id"], "task": case["task"], "rubric": case["rubric"], "track": "historical",
            "word_cap": n.LIMIT, "public": case["evidence"], "owned": []}
    result = {}
    for record in calls():
        call = [{}, {}, record["response"]]
        packet = e.final_packet(case, call)
        access = {row["id"] for row in json.loads(record["request"]["messages"][-1]["content"])["sources"]}
        result[record["mask"]] = {"record": packet, "available": sorted(access), "calls": call}
    return case, result


def score():
    case, deck = packets()
    marks = n.read(n.HERE / "marks.json")
    assert set(marks) == {str(mask) for mask in deck}
    rows = {}
    for mask, data in deck.items():
        verdict = marks[str(mask)]
        for unit in verdict["units"]:
            if unit["status"] == "met":
                assert {source["block"] for source in unit["source"]} <= set(data["available"])
        rows[mask] = e.final_score(case, data["calls"], verdict)
    archived = n.matched.data.banks()["unifil"].tolist()
    actual = {mask: row["released_70"] for mask, row in rows.items()}
    return {"records": rows, "archived_comparison": n.comparison(archived),
            "native_comparison": n.comparison(actual), "annotation": "same-assistant source reading"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("packets", "score", "verify"))
    mode = parser.parse_args().mode
    e.emit({"packets": lambda: packets()[1], "score": score, "verify": verify}[mode]())
