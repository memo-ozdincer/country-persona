"""Separate a confirmed grade from requests and bind reader output to a quote."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import three_seat_language as old

HERE = Path(__file__).resolve().parent
ROOT = HERE / "three-seat-language-contract-evidence"
FAMILY = "one-grade-confirmation-contract"
runner = old.runner
NEW_CONTROLS = {
    **old.CONTROLS,
    "request_change": ("We propose raising our earlier grade of zero for package C to two. The change is not confirmed.", None),
    "peer_and_self": ("The first delegate reported A=3. My confirmed grade for package C is zero.", ("C", 0)),
}
WRITE = (
    "Draft one plain declarative sentence reporting an already confirmed assessment by your delegation. "
    "The package ID is an identifier, not a letter grade. The numerical grade is already fixed. "
    "Name the package and state the assigned numerical grade. Do not request a change, review, approval "
    "or grade assignment. Give the declaration only."
)
READ = (
    "Extract a single confirmed current grade assigned by the speaker from the quoted message. Treat letters "
    "as package identifiers and numbers as grades. A request, proposal, another delegate's grade or historical "
    "grade is not a current self-report. If there are no current self-reports or multiple, return only NONE. "
    "Otherwise write exactly the package letter and a single grade digit on the first line, separated by a space. "
    "On the next line quote the shortest exact substring from the message showing the package and current grade. "
    "When the speaker explicitly corrects a previous value, use the current one. Do not add any other text."
)


def initial():
    trace = old.ROOT / "transcript.jsonl"
    done = json.loads((old.ROOT / "complete.json").read_text())
    assert runner.digest(trace) == done["transcript_sha256"]
    return {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}


def episode(generate):
    previous = initial()
    written = generate([old.job(f"write/{p}{g}", previous[f"write/{p}{g}"]["cap"], WRITE,
                                {"package_identifier": p, "confirmed_numerical_grade": g})
                        for p, g in old.VOCABULARY])
    classic, evidence = [], []
    for p, g in old.VOCABULARY:
        key = f"{p}{g}"
        text = written[f"write/{key}"]["output"]
        task = previous[f"read/{key}"]["messages"][0]["content"]
        classic.append(old.job(f"classic/{key}", 12, task, {"delegate_message": text}))
        evidence.append(old.job(f"evidence/{key}", 48, READ, {"delegate_message": text}))
    for name, (message, _) in NEW_CONTROLS.items():
        evidence.append(old.job(f"evidence/{name}", 48, READ, {"delegate_message": message}))
    evidence.append(old.job("evidence/previous_c_zero", 48, READ, {
        "delegate_message": previous["write/C0"]["output"]}))
    return [{"family": FAMILY, "final": written | generate(classic) | generate(evidence)}]


def locks():
    return {str(p.relative_to(HERE.parents[1])): runner.digest(p) for p in (
        Path(__file__), Path(old.__file__), Path(runner.__file__), old.ROOT / "transcript.jsonl",
        old.ROOT / "complete.json")}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = [json.loads((directory / name).read_text()) for name in ("launch.json", "complete.json")]
    raw, final = directory / "transcript.jsonl", directory / "final-records.json"
    assert launch["sha256"] == locks() and runner.digest(raw) == finish["transcript_sha256"]
    assert runner.digest(final) == finish["final_records_sha256"]
    rows = {r["id"]: r for r in map(json.loads, raw.read_text().splitlines())}
    assert len(rows) == finish["records"] == 3 * len(old.VOCABULARY) + len(NEW_CONTROLS) + 1
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")

    def verify(batch):
        for job in batch:
            row = rows[job["id"]]
            assert all(row[k] == v for k, v in job.items())
            assert runner.encode(tokenizer, job) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
            assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["output"]
        return {r["id"]: rows[r["id"]] for r in batch}

    restored = episode(verify)
    assert json.loads(final.read_text()) == {
        e["family"]: {k: r["output"] for k, r in e["final"].items()} for e in restored}
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
