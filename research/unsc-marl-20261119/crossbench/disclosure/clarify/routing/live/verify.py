"""Reconstruct all prompts, token outputs, routing choices and public results."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from transformers import AutoTokenizer

from episode import CAP, episode, hashes


def verify(path):
    launch = json.loads((path/"launch.json").read_text())
    complete = json.loads((path/"complete.json").read_text())
    transcript = (path/"transcript.jsonl").read_bytes()
    assert launch["sha256"]==hashes() and launch["optimizer_updates"]==complete["optimizer_updates"]==0
    assert sha256(transcript).hexdigest()==complete["transcript_sha256"]
    stored = {r["id"]:r for r in map(json.loads,transcript.splitlines())}
    assert len(stored)==len(transcript.splitlines())==complete["records"]
    tok = AutoTokenizer.from_pretrained(launch["model"],local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    metrics = {"caps":0,"input_tokens":0,"output_tokens":0}

    def generate(batch):
        out = {}
        for row in batch:
            record = stored.pop(row["id"])
            assert all(record[k]==v for k,v in row.items())
            text = tok.apply_chat_template(row["messages"],tokenize=False,
                                           add_generation_prompt=True,enable_thinking=False)
            assert tok.encode(text,add_special_tokens=False)==record["input_ids"]
            ids = record["output_ids"]
            assert 0<len(ids)<=CAP and eos not in ids[:-1]
            assert (ids[-1]==eos)==record["ended"]
            assert record["ended"] or len(ids)==CAP
            assert tok.decode(ids,skip_special_tokens=True).strip()==record["output"]
            metrics["input_tokens"] += len(record["input_ids"])
            metrics["output_tokens"] += len(ids)
            metrics["caps"] += not record["ended"]
            out[row["id"]] = record
        return out

    evaluated = episode(generate)
    assert not stored and evaluated==json.loads((path/"metrics.json").read_text())
    return {"records":evaluated["records"],"episodes":len(evaluated["episodes"]),**metrics}


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run",type=Path)
    print(json.dumps(verify(parser.parse_args().run),indent=2))
