"""Measure a one-revision intervention at the Jerusalem chair."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as original

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "evidence/source-record-compact"
FAMILY = "jerusalem-draft-2017-12-18"
SOLO_DRAFTS = "independent_drafts"
PEER_DRAFTS = "interactive"


def archive():
    f = BASE / "transcript.jsonl"
    complete = json.loads((BASE / "complete.json").read_text())
    assert sha256(f.read_bytes()).hexdigest() == complete["transcript_sha256"]
    return {row["id"]: row for row in map(json.loads, f.read_text().splitlines())}


def swaps():
    records = archive()
    anchor = records[f"{FAMILY}/{SOLO_DRAFTS}/chair"]
    peer = records[f"{FAMILY}/{PEER_DRAFTS}/chair"]
    base_message = json.loads(anchor["messages"][-1]["content"])
    peer_message = json.loads(peer["messages"][-1]["content"])
    assert anchor["cap"] == peer["cap"] == 256
    assert {k: v for k, v in base_message.items() if k != "working_text"} == {
        k: v for k, v in peer_message.items() if k != "working_text"}
    for i in range(2):
        updated = list(base_message["working_text"])
        updated[i] = peer_message["working_text"][i]
        assert updated[1-i] == base_message["working_text"][1-i]
        ids = list(anchor["seen"])
        ids[i] = peer["seen"][i]
        assert updated[i]["text"] == records[ids[i]]["output"]
        payload = {**base_message, "working_text": updated}
        yield {"id": f"{FAMILY}/peer_revision_{i+1}_only/chair", "evidence_ids": anchor["evidence_ids"],
               "seen": ids, "cap": anchor["cap"],
               "messages": [anchor["messages"][0], {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(swaps()))}]


def locks():
    files = (Path(__file__).resolve(), Path(original.__file__), BASE/"transcript.jsonl", BASE/"complete.json")
    return {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in files}


def replay(directory):
    from transformers import AutoTokenizer
    launch = json.loads((directory / "launch.json").read_text())
    assert launch["sha256"] == locks()
    stored = directory / "transcript.jsonl"
    complete = json.loads((directory/"complete.json").read_text())
    assert complete["transcript_sha256"] == original.digest(stored)
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    for example, row in zip(swaps(), map(json.loads, stored.read_text().splitlines()), strict=True):
        assert all(row[key] == value for key, value in example.items())
        assert original.encode(tokenizer, example) == row["input_ids"]
        output = row["output_ids"]
        assert eos not in output[:-1]
        assert row["ended"] == (output[-1] == eos)
        assert 0 < len(output) <= row["cap"]
        assert tokenizer.decode(output, skip_special_tokens=True).strip() == row["output"]
    assert complete["records"] == 2
    assert complete["final_records_sha256"] == original.digest(directory/"final-records.json")
    return {"records": 2, "exact_replay": True}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay", "check"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        if args.model is None or args.directory is None:
            cli.error("--model and directory are required for run")
        with patch.object(original, "episode", new=episode), patch.object(original, "locks", new=locks):
            original.run(args.model, args.directory)
    elif args.mode == "replay":
        print(json.dumps(replay(args.directory), indent=2))
    else:
        print(json.dumps([{"id": row["id"], "seen": row["seen"]} for row in swaps()], indent=2))
