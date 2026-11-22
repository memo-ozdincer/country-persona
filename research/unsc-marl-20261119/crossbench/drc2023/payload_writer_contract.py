"""Rerun the frozen DRC chair with separate source clauses and legal modality."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import payload_policy_writer as previous

HERE = Path(__file__).resolve().parent
runner = previous.runner
ROOT = HERE / "payload-writer-contract-evidence"
FAMILY = "drc-legal-force-contract"
INSTRUCTION = (
    "Write only the supplement, at most 73 words. Draft one short paragraph per working note in its given order. "
    "Keep the note's actor, action, dates, recipients and exceptions together. Preserve its legal verb and tense. "
    "For example, retain intends or requests if a note uses that verb. Preserve the difference between an "
    "intended action, an obligation and a completed decision. Do not infer a new duty, shared recipient or "
    "causal link across notes. Do not repeat the public vote or add explanatory filler. "
    "If there are no working notes, return 'No additional source detail was delivered.'"
)


def original():
    trace = previous.EVIDENCE / "transcript.jsonl"
    finish = previous.interface.parent.read(previous.EVIDENCE / "complete.json")
    assert runner.digest(trace) == finish["transcript_sha256"]
    return {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}


def requests():
    for identifier, row in original().items():
        system, prompt = row["messages"]
        body = json.loads(prompt["content"])
        body["task"] = INSTRUCTION
        yield {k: row[k] for k in ("id", "cap", "seen", "evidence_ids")} | {
            "messages": [system, {**prompt, "content": json.dumps(body, ensure_ascii=False)}]}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def locks():
    return previous.locks() | {
        str(p.relative_to(HERE)): runner.digest(p) for p in (
            Path(__file__), previous.EVIDENCE / "transcript.jsonl", previous.EVIDENCE / "complete.json")
    }


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = [json.loads((directory / name).read_text()) for name in ("launch.json", "complete.json")]
    trace, final = directory / "transcript.jsonl", directory / "final-records.json"
    assert launch["sha256"] == locks() and runner.digest(trace) == finish["transcript_sha256"]
    assert runner.digest(final) == finish["final_records_sha256"]
    rows = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    assert len(rows) == finish["records"] == 11
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    for request in requests():
        row = rows[request["id"]]
        assert all(row[key] == value for key, value in request.items())
        assert runner.encode(token, request) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert token.decode(ids, skip_special_tokens=True).strip() == row["output"]
    assert json.loads(final.read_text()) == {FAMILY: {name: row["output"] for name, row in rows.items()}}
    return rows, token


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        rows, _ = replay(args.directory)
        print(json.dumps({"exact_records": len(rows)}))
