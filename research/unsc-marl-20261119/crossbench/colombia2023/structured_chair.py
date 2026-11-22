"""Separate decision, delegation conditions and shared ground under a short cap."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import provenance_chair as prior

base = prior.base
SHORT = "Finish within 145 words. Omit any heading, introduction or closing summary. "
SEPARATED = (
    "Use five short paragraphs in this order. Give the vote and adopted action. Give existing ELN authority and the "
    "stated prerequisites and implementation update for considering EMC. Give Brazil's speaker, represented party and "
    "reason. Give Ghana's represented party, its condition, and its separate Ethnic Chapter priority. "
    "In the last paragraph state only their conditional support for a possible future EMC role. State that 2704 did not "
    "grant that authority. Leave the exact triggers in their separately attributed paragraphs. "
)


def plans():
    source, = [p for p in prior.plans() if p["id"] == "ledger_both_reversed"]
    role, prompt = source["messages"]
    data = json.loads(prompt["content"])
    return [{**source, "id": label, "messages": [role, {**prompt, "content": json.dumps({
            **data, "task": prefix + data["task"]}, ensure_ascii=False)}]}
            for label, prefix in (("short_only", SHORT), ("short_separate_scopes", SHORT + SEPARATED))]


def locks():
    files = (Path(__file__), prior.HERE / "provenance-evidence/complete.json")
    return {**prior.locks(), **{f.name + ":structured": base.runner.digest(f) for f in files}}


def episode(generate):
    return [{"family": "colombia-structured-chair", "final": generate(plans())}]


def verify(directory):
    from transformers import AutoTokenizer

    read = lambda name: json.loads((directory / name).read_text())
    transcript = directory / "transcript.jsonl"
    complete = read("complete.json")
    assert complete["transcript_sha256"] == base.runner.digest(transcript)
    assert complete["final_records_sha256"] == base.runner.digest(directory / "final-records.json")
    launch = read("launch.json")
    assert launch["sha256"] == locks()
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    outputs = read("final-records.json")["colombia-structured-chair"]
    rows = {r["id"]: r for r in map(json.loads, transcript.read_text().splitlines())}
    assert len(rows) == len(outputs) == complete["records"] == 2
    for expected in plans():
        row = rows[expected["id"]]
        assert all(row[k] == v for k, v in expected.items())
        assert row["input_ids"] == base.runner.encode(token, expected)
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert row["output"] == outputs[row["id"]] == token.decode(ids, skip_special_tokens=True).strip()
    return {"records": 2, "exact_replay": True}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(base.runner, episode=episode, locks=locks):
            base.runner.run(args.model, args.directory)
    else:
        print(json.dumps(verify(args.directory), indent=2))
