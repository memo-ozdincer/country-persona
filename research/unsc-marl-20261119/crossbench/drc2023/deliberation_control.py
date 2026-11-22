"""Complete a two-by-two test of reporter instruction and peer-note visibility."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import deliberation

HERE = deliberation.HERE
ROOT = HERE / "deliberation-evidence"
runner = deliberation.runner
FAMILY = "drc-reporter-visibility-control"
EXTRA = ("ordinary_with_note", "reply_instruction_no_note")


def baseline():
    source = ROOT / "transcript.jsonl"
    assert runner.digest(source) == json.loads((ROOT / "complete.json").read_text())["transcript_sha256"]
    return {r["id"]: r for r in map(json.loads, source.read_text().splitlines())}


def jobs():
    original = baseline()
    quiet = original["peer_independent_report"]
    peer = original["peer_interactive_report"]
    out = []
    for name, fixed, visibility in ((EXTRA[0], quiet, peer), (EXTRA[1], peer, quiet)):
        system, prompt = fixed["messages"]
        content = json.loads(prompt["content"])
        all_notes = json.loads(visibility["messages"][1]["content"])["working_notes"]
        out.append({k: fixed[k] for k in ("cap", "evidence_ids")} | {
            "id": name, "seen": visibility["seen"],
            "messages": [system, {**prompt, "content": json.dumps({**content, "working_notes": all_notes},
                                                                ensure_ascii=False)}],
        })
    return out


def locks():
    return {path.name: runner.digest(path) for path in (Path(__file__), Path(runner.__file__),
                                                       ROOT / "transcript.jsonl", ROOT / "complete.json")}


def episode(generate):
    return [{"family": FAMILY, "final": generate(jobs())}]


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = [json.loads((directory / name).read_text()) for name in ("launch.json", "complete.json")]
    trace = directory / "transcript.jsonl"
    finals = directory / "final-records.json"
    assert launch["sha256"] == locks()
    assert runner.digest(trace) == finish["transcript_sha256"]
    assert runner.digest(finals) == finish["final_records_sha256"]
    rows = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    texts = json.loads(finals.read_text())[FAMILY]
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    assert len(rows) == len(texts) == finish["records"] == len(EXTRA)
    for job in jobs():
        row = rows[job["id"]]
        assert all(row[k] == v for k, v in job.items())
        assert runner.encode(tokenizer, job) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= job["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["output"] == texts[job["id"]]
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
        print(json.dumps({"exact_records": len(replay(args.directory))}))
