"""Verify saved prompt projection, token traces and checkpoint provenance on CPU."""
from hashlib import sha256
import json
from pathlib import Path
import re

from jinja2.sandbox import ImmutableSandboxedEnvironment
from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent
ROOT = ARCHIVE.parents[1]
EVIDENCE = HERE / "evidence"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def verify():
    locked = read(EVIDENCE / "format-lock.json")
    complete = read(EVIDENCE / "complete.json")
    assert all(digest(ROOT / path) == value for path, value in locked.items())
    assert set(complete) == {"format-lock.json", "launch.json", "records.jsonl", "tokens.jsonl"}
    assert all(digest(EVIDENCE / path) == value for path, value in complete.items())
    launch = read(EVIDENCE / "launch.json")
    model = Path(launch["checkpoint"])
    assert digest(model / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    assert launch["optimizer_updates"] == 0 and launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    tok_path = model / "tokenizer.json"
    template_path = model / "chat_template.jinja"
    tokenizer = Tokenizer.from_file(str(tok_path))
    eos = tokenizer.token_to_id("<|im_end|>")
    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    template = env.from_string(template_path.read_text())
    records = rows(EVIDENCE / "records.jsonl")
    baseline = rows(ARCHIVE / "format-evidence/records.jsonl")
    tokens = rows(EVIDENCE / "tokens.jsonl")
    collector = (HERE / "collect.py").read_text()
    clauses = re.search(r"CHECKLIST = \(\n(.*?)\n\)", collector, flags=re.DOTALL)[1]
    import ast
    checklist = ast.literal_eval(f"({clauses})")
    assert len(records) == len(baseline) == len(tokens) == 4
    for row, old, trace in zip(records, baseline, tokens, strict=True):
        assert row["id"] == old["id"]
        request = old["request"]
        request["messages"][0]["content"] += checklist
        assert request == row["request"]
        rendered = template.render(messages=request["messages"], add_generation_prompt=True,
                                   enable_thinking=False, tools=None)
        input_ids = tokenizer.encode(rendered, add_special_tokens=False).ids
        assert trace["input_ids"] == input_ids
        response = row["response"]
        assert trace["response"] == response
        ids = trace["output_ids"]
        assert len(input_ids) == response["input_tokens"]
        assert len(ids) == response["output_tokens"] <= request["max_output_tokens"]
        assert ids and eos not in ids[:-1]
        assert (ids[-1] == eos) == (response["termination"] == "complete")
        assert tokenizer.decode(ids, skip_special_tokens=True).strip() == response["text"]
    return {"verified_live_calls": len(records), "optimizer_updates": launch["optimizer_updates"],
            "preserved_fields": ["case", "turn order", "public blocks", "delegate notes",
                                 "certificate", "decision line instruction", "output ceiling"],
            "tokenizer_sha256": digest(tok_path), "chat_template_sha256": digest(template_path)}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
