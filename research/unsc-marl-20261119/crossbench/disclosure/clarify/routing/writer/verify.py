"""Replay exact writer prompts, source hashes, and token traces."""
import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from review import create, materialize
from run import CAP, ROOT, digest, suite


def verify(path):
    launch = json.loads((path/"launch.json").read_text())
    assert launch["updates"] == 0
    for name, expected in launch["sources"].items():
        assert digest(ROOT/name)==expected
    tok = AutoTokenizer.from_pretrained(launch["model"],local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    if "writer/instrument.py" in launch["sources"]:
        from instrument import suite as instrument_suite
        expected = list(instrument_suite())
    else:
        expected = list(suite())
    seen = materialize(path)
    for template, row in zip(expected, seen, strict=True):
        assert all(row[k]==v for k,v in template.items())
        prompt = tok.apply_chat_template(row["messages"],tokenize=False,add_generation_prompt=True,
                                         enable_thinking=False)
        assert tok.encode(prompt,add_special_tokens=False)==row["input_ids"]
        tail = row["output_ids"]
        assert 0<len(tail)<=CAP and eos not in tail[:-1]
        assert (tail[-1]==eos)==(row["stop"]=="eos")
        assert row["stop"]=="eos" or len(tail)==CAP
        assert tok.decode(tail,skip_special_tokens=True).strip()==row["output"]
    report = {"records":len(seen), "updates":0,"mechanical":{
        row["model_id"]:row["mechanics"] for row in create(path)}}
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("run",type=Path)
    print(json.dumps(verify(p.parse_args().run),indent=2))
