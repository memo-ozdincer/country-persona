"""Repeat only the Myanmar UK component with a more explicit sponsorship instruction."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import myanmar_protected_writer as writer
from source_record_run import digest

RUNNER = writer.archive.runner
ORIGINAL = writer.EVIDENCE / writer.FAMILY
NAME = "myanmar-sponsorship-probe"
TARGET = writer.EVIDENCE / NAME


def request():
    base = next(r for r in writer.requests() if r["id"] == "uk")
    task = json.loads(base["messages"][1]["content"])
    task["task"] = (
        "Use an explicit verb to identify who submitted the draft. Also state whom that delegation consulted, "
        "and what priorities it gave when welcoming the decision. Include each of these points in one sentence."
    )
    return {**base, "messages": [base["messages"][0], {"role": "user", "content": json.dumps(task, ensure_ascii=False)}]}


def locks():
    paths = (Path(__file__).resolve(), ORIGINAL / "transcript.jsonl",
             writer.EVIDENCE / "myanmar-public-rubric-fit/fit.json")
    return {**writer.locks(), **{str(p.relative_to(writer.PROJECT)): digest(p) for p in paths}}


def episode(generate):
    return [{"family": NAME, "final": generate([request()])}]


def replay(directory, verify_tokens=False):
    from myanmar_protected_writer import archive

    # Use the same recorder as the three-call run. This contrast has one model call.
    trace = directory / "transcript.jsonl"
    launch = json.loads((directory / "launch.json").read_text())
    end = json.loads((directory / "complete.json").read_text())
    assert launch["sha256"] == locks() and end["transcript_sha256"] == digest(trace)
    row, = list(map(json.loads, trace.read_text().splitlines()))
    assert end["records"] == 1 and all(row[k] == v for k, v in request().items())
    finals = directory / "final-records.json"
    assert end["final_records_sha256"] == digest(finals)
    assert json.loads(finals.read_text()) == {NAME: {"uk": row["output"]}}
    if verify_tokens:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
        eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
        output = row["output_ids"]
        assert archive.runner.encode(tokenizer, request()) == row["input_ids"]
        assert 0 < len(output) <= writer.CAP and eos not in output[:-1]
        assert (output[-1] == eos) == row["ended"]
        assert tokenizer.decode(output, skip_special_tokens=True).strip() == row["output"]
    return row


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        if args.model is None:
            cli.error("run requires --model")
        with patch.multiple(RUNNER, episode=episode, locks=locks):
            RUNNER.run(args.model, TARGET)
    else:
        print(json.dumps(replay(TARGET, verify_tokens=True), indent=2, ensure_ascii=False))
