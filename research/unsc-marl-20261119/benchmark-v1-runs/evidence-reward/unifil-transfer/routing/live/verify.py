"""Verify the locked UNIFIL native reply prompts and exact token traces."""
from hashlib import sha256
import json
from pathlib import Path

from jinja2.sandbox import ImmutableSandboxedEnvironment
from tokenizers import Tokenizer

import live

HERE = Path(__file__).resolve().parent
RUN = HERE / "evidence"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(name):
    return [json.loads(line) for line in (RUN/name).read_text().splitlines()]


def run():
    manifest = live.E.read(RUN/"complete.json")
    assert set(manifest) == {"launch.json","records.jsonl","route-lock.json","tokens.jsonl"}
    assert all(digest(RUN/name)==sha for name,sha in manifest.items())
    assert live.E.read(RUN/"route-lock.json")==live.pins()
    launch=live.E.read(RUN/"launch.json")
    model=Path(launch["checkpoint"])
    assert digest(model/"model.safetensors.index.json")==launch["checkpoint_index_sha256"]
    assert launch["optimizer_updates"]==0
    assert launch["gpu_name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
    t=Tokenizer.from_file(str(model/"tokenizer.json"))
    template=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True).from_string(
        (model/"chat_template.jinja").read_text())
    source=live.deck()
    assert source==live.E.read(HERE/"requests.json")
    records, traces=load("records.jsonl"),load("tokens.jsonl")
    eos=t.token_to_id("<|im_end|>")
    for expected,row,trace in zip(source,records,traces,strict=True):
        assert expected=={k:row[k] for k in ("id","request")}
        request, response=row["request"],row["response"]
        text=template.render(messages=request["messages"],add_generation_prompt=True,
                             enable_thinking=False,tools=None)
        actual=t.encode(text,add_special_tokens=False).ids
        assert actual==trace["input_ids"] and len(actual)==response["input_tokens"]
        assert trace["response"]==response
        ids=trace["output_ids"]
        assert ids and len(ids)==response["output_tokens"]<=request["max_output_tokens"]
        assert eos not in ids[:-1] and (ids[-1]==eos)==(response["termination"]=="complete")
        assert t.decode(ids,skip_special_tokens=True).strip()==response["text"]
    return {"verified_calls":len(records),"optimizer_updates":0,
            "tokenizer_sha256":digest(model/"tokenizer.json")}


if __name__=="__main__":
    live.E.emit(run())
