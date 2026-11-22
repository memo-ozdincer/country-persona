"""Assess a frozen source ledger against actual and perturbed working notes."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import note_intervention as intervention

HERE = Path(__file__).resolve().parent
base = intervention.original
SOURCE = HERE / "provenance-ledger.json"
PARENT = intervention.PARENT
DIRECTIVE = (
    "Use the documentary sources as the factual authority. Verify the direction of every speaker–represented-party "
    "relationship against the documentary record. Treat working notes as provisional, ignore a conflicting claim, "
    "and do not use one delegation's rationale as evidence of what another delegation specifically agreed to. "
    "Separate the Council's enacted decision from possible future consideration or a delegate's hope. "
    "Count the exact contribution of each party before stating a shared position. Preserve qualified differences."
)


def ledger(sources):
    packet = json.loads(SOURCE.read_text())
    assert packet["source_sha256"] == base.runner.digest(base.CASE)
    assert {r["source"] for r in packet["rows"]} == sources.keys()
    for row in packet["rows"]:
        assert all(span in sources[row["source"]] for span in row["required_spans"])
    return {row["source"]: row["fact"] for row in packet["rows"]}


def plans():
    _, conflicted = intervention.plan()
    role, raw = conflicted["messages"]
    body = json.loads(raw["content"])
    public = ledger(body["sources"])
    actual = {r["id"].split("/", 1)[-1]: r["output"] for r in
              map(json.loads, (PARENT / "transcript.jsonl").read_text().splitlines())}
    d = body["working_notes"]
    correct = d[1].replace(intervention.REVERSED, intervention.CORRECT, 1)
    adverse = actual["independent_drafts/revision_0"]
    assert "speaking for the Government of Colombia" in adverse
    assert intervention.REVERSED in d[1] and intervention.CORRECT in correct
    inputs = {
        "priority_reversed_a3": (False, d),
        "ledger_reversed_a3": (True, d),
        "ledger_both_reversed": (True, [adverse, d[1]]),
        "ledger_clean": (True, [d[0], correct]),
    }
    return [
        {**conflicted, "id": name, "seen": ([] if not notes else conflicted["seen"]),
         "messages": [role, {**raw, "content": json.dumps({
             **body, "task": DIRECTIVE + " " + body["task"], "working_notes": notes,
             **({"documentary_fields": public} if use_ledger else {})}, ensure_ascii=False)}]}
        for name, (use_ledger, notes) in inputs.items()
    ]


def locks():
    return {**intervention.locks(), **{x.name: base.runner.digest(x) for x in (Path(__file__), SOURCE)}}


def episode(generate):
    return [{"family": "colombia-provenance-chair", "final": generate(plans())}]


def check():
    clean, tied, worst, normal = plans()
    assert len({r["cap"] for r in (clean, tied, worst, normal)}) == 1
    a, b = (json.loads(x["messages"][1]["content"]) for x in (clean, tied))
    b.pop("documentary_fields")
    assert a == b
    a, b = (json.loads(x["messages"][1]["content"]) for x in (tied, worst))
    assert a.pop("working_notes")[1] == b.pop("working_notes")[1] and a == b
    return {"cases": 4, "source_cards": 5, "chair_output_cap": clean["cap"]}


def replay(directory):
    from transformers import AutoTokenizer

    completion = json.loads((directory / "complete.json").read_text())
    launch = json.loads((directory / "launch.json").read_text())
    file = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    assert launch["sha256"] == locks()
    assert completion["transcript_sha256"] == base.runner.digest(file)
    assert completion["final_records_sha256"] == base.runner.digest(final)
    rows = {r["id"]: r for r in map(json.loads, file.read_text().splitlines())}
    final_text = json.loads(final.read_text())["colombia-provenance-chair"]
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    for req in plans():
        row = rows[req["id"]]
        assert all(row[k] == v for k, v in req.items())
        assert base.runner.encode(tok, req) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= req["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert row["output"] == final_text[req["id"]] == tok.decode(ids, skip_special_tokens=True).strip()
    assert rows.keys() == final_text.keys() and len(rows) == completion["records"] == 4
    return {"records": 4, "exact_replay": True}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps(check(), indent=2))
    elif args.mode == "run":
        check()
        with patch.multiple(base.runner, episode=episode, locks=locks):
            base.runner.run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory), indent=2))
