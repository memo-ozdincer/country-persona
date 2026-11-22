"""Compare packet-specific instructions on two observed source-scope failures."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import receipt_chair as parent

CAPS = {
    ("A3",): ("Write at most 55 words on the A3 statement alone. Attribute it precisely and preserve the "
              "condition for support and the separate Ethnic Chapter priority. Cite [A3]. End after that statement."),
    ("ADDITIONAL", "BRAZIL", "A3"): ("Write at most 125 words in three compact source-cited blocks and one short "
                                     "comparison sentence. Give the legal stage and separate inputs for considering EMC "
                                     "in [ADDITIONAL]. Preserve each speaker, represented party and distinct rationale in "
                                     "[BRAZIL] and [A3]. Compare only their support for a possible conditional future role. "
                                     "Keep the precise thresholds in their own source blocks. End without a closing summary."),
}


def plans():
    selected = []
    for row in parent.planned():
        subset = tuple(row["evidence_ids"])
        if subset not in CAPS:
            continue
        role, prompt = row["messages"]
        body = json.loads(prompt["content"])
        body["task"] = CAPS[subset]
        selected.append({**row, "messages": [role, {**prompt, "content": json.dumps(body, ensure_ascii=False)}]})
    assert len(selected) == len(CAPS)
    return selected


def locks():
    source = parent.HERE / "receipt-evidence/complete.json"
    return {**parent.locks(), **{p.name: parent.runner.digest(p) for p in (Path(__file__), source)}}


def episode(generate):
    return [{"family": "colombia-scope-probe", "final": generate(plans())}]


def replay(directory):
    from transformers import AutoTokenizer

    complete = json.loads((directory / "complete.json").read_text())
    launch = json.loads((directory / "launch.json").read_text())
    assert launch["sha256"] == locks()
    raw = directory / "transcript.jsonl"
    expected_final = directory / "final-records.json"
    assert complete["transcript_sha256"] == parent.runner.digest(raw)
    assert complete["final_records_sha256"] == parent.runner.digest(expected_final)
    visible = json.loads(expected_final.read_text())["colombia-scope-probe"]
    rows = {r["id"]: r for r in map(json.loads, raw.read_text().splitlines())}
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    assert len(rows) == len(visible) == complete["records"] == 2
    for plan in plans():
        row = rows[plan["id"]]
        assert all(row[k] == v for k, v in plan.items())
        assert row["input_ids"] == parent.runner.encode(tokenizer, plan)
        ids = row["output_ids"]
        assert 0 < len(ids) <= plan["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert row["output"] == visible[row["id"]] == tokenizer.decode(ids, skip_special_tokens=True).strip()
    return {"records": len(rows), "exact_replay": True}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(parent.runner, episode=episode, locks=locks):
            parent.runner.run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory), indent=2))
