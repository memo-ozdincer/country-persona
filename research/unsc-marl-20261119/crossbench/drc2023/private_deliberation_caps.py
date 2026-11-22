"""Isolate the reporting cap and compare verbatim source forwarding."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import private_deliberation as parent

HERE = parent.HERE
runner = parent.runner
BASE = HERE / "private-deliberation-evidence"
RD = 104
ARMS = ("independent", "interactive", "verbatim")


def archived():
    trace = BASE / "transcript.jsonl"
    finish = parent.read(BASE / "complete.json")
    assert runner.digest(trace) == finish["transcript_sha256"]
    return {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}


def seen(row, new_notes):
    system, user = row["messages"]
    body = json.loads(user["content"])
    body["working_notes"] = list(new_notes.values())
    return {**row, "seen": list(new_notes),
            "messages": [system, {**user, "content": json.dumps(body, ensure_ascii=False)}]}


def episode(generate):
    source = archived()
    stage = []
    for family, _, _ in parent.fixtures():
        for arm in ARMS[:2]:
            original = source[f"{family}/desk_b_{arm}"]
            job = {key: original[key] for key in ("evidence_ids", "seen", "messages")}
            stage.append({**job, "id": f"{family}/report_{arm}", "cap": RD})
    reporters = generate(stage)

    final = []
    for family, _, decks in parent.fixtures():
        for arm in ARMS[:2]:
            original = source[f"{family}/{arm}"]
            job = {key: original[key] for key in ("id", "cap", "evidence_ids", "messages")}
            desk_a, desk_b = f"{family}/desk_a", f"{family}/report_{arm}"
            final.append(seen(job, {desk_a: source[desk_a]["output"], desk_b: reporters[desk_b]["output"]}))
        original = source[f"{family}/independent"]
        job = {key: original[key] for key in ("cap", "evidence_ids", "messages")}
        verbatim = {f"{family}/source_{desk}": "\n".join(cards.values()) for desk, cards in decks.items()}
        final.append(seen({**job, "id": f"{family}/verbatim"}, verbatim))
    generated = generate(final)
    return [{"family": family, "final": {name: generated[f"{family}/{name}"] for name in ARMS}}
            for family, _, _ in parent.fixtures()]


def locks():
    return {str(path.relative_to(HERE.parents[1])): runner.digest(path) for path in (
        Path(__file__), Path(parent.__file__), Path(runner.__file__), parent.DRC, parent.UNAMI,
        BASE / "transcript.jsonl", BASE / "complete.json")}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = [parent.read(directory / name) for name in ("launch.json", "complete.json")]
    trace, final = directory / "transcript.jsonl", directory / "final-records.json"
    assert runner.digest(trace) == finish["transcript_sha256"] and launch["sha256"] == locks()
    assert runner.digest(final) == finish["final_records_sha256"]
    records = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    assert len(records) == finish["records"] == 10
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    used = set()

    def restore(batch):
        for job in batch:
            identifier = job["id"]
            row = records[identifier]
            assert identifier not in used
            used.add(identifier)
            assert all(row[k] == v for k, v in job.items())
            assert runner.encode(tokenizer, job) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= job["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
            assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["output"]
        return {job["id"]: records[job["id"]] for job in batch}

    episodes = episode(restore)
    assert used == records.keys()
    assert parent.read(final) == {ep["family"]: {name: row["output"] for name, row in ep["final"].items()}
                                 for ep in episodes}
    return records


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
        print(json.dumps({"exact_records": len(replay(args.directory))}))
