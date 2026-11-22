"""Test frozen UNIFIL record drafting with one call or separate documentary clauses."""
import argparse
from itertools import combinations
import json
from pathlib import Path
from unittest.mock import patch

import field_writer as prior
import roster_shift as roster

HERE = prior.HERE
runner = prior.parent.runner
FAMILY = "unifil-documentary-fields"
TASKS = {
    "operative": "Preserve the duration of the existing mandate, independent mandated action without prior permission, and continued coordination under the status-of-forces agreement.",
    "brazil": "Attribute to Brazil its support for the mission, assessment of robust and free operation, and assessment of Lebanon's concerns.",
    "china": "Attribute to China its support for the mission, assessment of Lebanon's concerns, and emphasis on host-State sovereignty or consent.",
    "russia": "Attribute to Russia its rationale for abstaining, preserving the role of late changes and lost compromise, and its support for mission activities.",
    "comparison": "State the precise common ground on supporting the mission and contrast the assessments of how adequately the text addressed Lebanon's concerns.",
}
COMPARE = {"brazil", "china"}


def dossier():
    specs, _ = roster.transfer.named_sources()
    return specs["unifil"]


def plan():
    cards, *_ = dossier()
    for field in TASKS:
        keys = COMPARE if field == "comparison" else {field}
        yield request("field/" + field, keys, [field], cards)
    for width in (1, 2, 3):
        for keys in combinations(cards, width):
            fields = list(keys) + (["comparison"] if COMPARE <= set(keys) else [])
            yield request("whole/" + ",".join(sorted(keys)), set(keys), fields, cards)


def request(name, keys, fields, cards):
    tasks = []
    for field in fields:
        cited = ", ".join(sorted(COMPARE if field == "comparison" else {field}))
        limit = 25 if field == "comparison" else 36
        tasks.append(f"Write at most {limit} words in one paragraph. {TASKS[field]} Cite [{cited}].")
    content = {"task": "Write only the requested paragraphs. The roll call is already recorded. Use only the supplied sources.",
               "paragraphs": tasks, "documentary_sources": {key: cards[key] for key in sorted(keys)}}
    return {"id": name, "cap": sum(55 if f == "comparison" else 78 for f in fields),
            "evidence_ids": sorted(keys), "messages": [
                {"role": "system", "content": "You are the archival chair writing a retrospective Council record. The dated documentary sources define the factual scope of the supplement."},
                {"role": "user", "content": json.dumps(content, ensure_ascii=False)}]}


def episode(generate):
    batches = {}
    for row in plan():
        batches.setdefault(row["cap"], []).append(row)
    finals = {}
    for batch in batches.values():
        finals.update(generate(batch))
    return [{"family": FAMILY, "final": finals}]


def locks():
    paths = (Path(__file__), HERE.parent / "unifil-record.json", Path(runner.__file__),
             roster.transfer.HERE / "adaptive-align-results.json",
             HERE / "specialist-fit-results.json", HERE / "specialist-script-results.json")
    return {p.name: runner.digest(p) for p in paths}


def replay(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    finish = json.loads((directory / "complete.json").read_text())
    trace, finals = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == locks() and finish["transcript_sha256"] == runner.digest(trace)
    assert finish["final_records_sha256"] == runner.digest(finals)
    rows = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    outputs = json.loads(finals.read_text())[FAMILY]
    assert set(rows) == set(outputs) == {row["id"] for row in plan()}
    assert len(rows) == finish["records"] == 19
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    for expected in plan():
        row = rows[expected["id"]]
        assert all(row[k] == v for k, v in expected.items())
        assert runner.encode(tok, expected) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert outputs[row["id"]] == row["output"] == tok.decode(ids, skip_special_tokens=True).strip()
    return rows


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
        print(json.dumps({"records": len(replay(args.directory)), "exact_replay": True}))
