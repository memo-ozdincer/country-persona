"""Replay the compact interactive chair with one role reversal or no notes."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import run as original

HERE = Path(__file__).resolve().parent
PARENT = HERE / "compact-evidence"
CORRECT = "Ghana, speaking for African members,"
REVERSED = "The African members, speaking for Ghana,"


def plan():
    raw = PARENT / "transcript.jsonl"
    assert original.runner.digest(raw) == json.loads((PARENT / "complete.json").read_text())["transcript_sha256"]
    match, = [r for r in map(json.loads, raw.read_text().splitlines()) if r["id"].endswith("/interactive/chair")]
    role, prompt = match["messages"]
    body = json.loads(prompt["content"])
    brazil, a3 = body["working_notes"]
    assert a3.startswith(CORRECT)
    contexts = {
        "full_dossier_no_notes": [],
        "reversed_a3_note": [brazil, a3.replace(CORRECT, REVERSED, 1)],
    }
    return [{"id": arm, "cap": match["cap"], "evidence_ids": match["evidence_ids"],
             "seen": match["seen"] if notes else [], "messages": [
                 role, {**prompt, "content": json.dumps({**body, "working_notes": notes}, ensure_ascii=False)}]}
            for arm, notes in contexts.items()]


def locks():
    return {**original.locks(), **{f.name: original.runner.digest(f) for f in
                                   (Path(__file__), PARENT / "transcript.jsonl", PARENT / "complete.json")}}


def episode(generate):
    return [{"family": "colombia-note-intervention", "final": generate(plan())}]


def replay(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    assert launch["sha256"] == locks()
    raw = directory / "transcript.jsonl"
    assert complete["transcript_sha256"] == original.runner.digest(raw)
    final = directory / "final-records.json"
    assert complete["final_records_sha256"] == original.runner.digest(final)
    texts = json.loads(final.read_text())["colombia-note-intervention"]
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    rows = {r["id"]: r for r in map(json.loads, raw.read_text().splitlines())}
    assert len(rows) == len(texts) == complete["records"] == 2
    for expected in plan():
        row = rows[expected["id"]]
        assert all(row[key] == value for key, value in expected.items())
        assert row["input_ids"] == original.runner.encode(token, expected)
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert texts[row["id"]] == row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    return {"records": len(rows), "exact_replay": True}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(original.runner, episode=episode, locks=locks):
            original.runner.run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory), indent=2))
