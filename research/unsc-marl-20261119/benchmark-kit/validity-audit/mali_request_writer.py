"""Generate fresh complete Mali records for each distinct source receipt."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as runner
from source_request_cases import MALI, ROOT, cases, hashes as case_hashes

FAMILY = "mali-request-final-record"
CAP = 360
SYSTEM = (
    "Write a neutral retrospective Security Council chair record in at most 165 words. Use only the numbered "
    "blocks actually delivered. State the date, each draft's sponsor, instrument, separate tally, outcome and "
    "reason it failed. Separate proposed provisions from adopted authority. Preserve overlapping proposals and "
    "differences. When a national explanation is available, state its owner and associate it with the correct vote. "
    "Cite the supporting block IDs in brackets. Leave unavailable explanations out. Omit a title, preamble and afterword."
)


def evidence():
    task = json.loads(MALI.read_text())
    by_id = {r["id"]: r["text"] for r in task["evidence"]}
    public = {k: by_id[k] for k in ("status-638", "status-639")}
    cards = []
    for field in cases()["mali"]["fields"]:
        blocks = {item["block"]: item["quote"] for item in field["evidence"]}
        assert all(text in by_id[key] for key, text in blocks.items())
        cards.append(blocks)
    assert len(cards) == 3
    return public, cards


def requests():
    public, cards = evidence()
    for mask in range(8):
        view = dict(public)
        for i, card in enumerate(cards):
            if mask & (1 << i):
                view.update(card)
        yield {"id": f"receipt-{mask}", "evidence_ids": list(view), "seen": [], "cap": CAP,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": json.dumps({"evidence": view}, ensure_ascii=False)}]}


def locks():
    files = (Path(__file__), Path(runner.__file__), MALI)
    return {**case_hashes(), **{str(p.resolve().relative_to(ROOT)): runner.digest(p) for p in files}}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def replay(directory, verify_tokens=False):
    begin = json.loads((directory / "launch.json").read_text())
    end = json.loads((directory / "complete.json").read_text())
    trace = directory / "transcript.jsonl"
    assert begin["sha256"] == locks() and end["transcript_sha256"] == runner.digest(trace)
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == end["records"] == 8
    tokenizer = None
    if verify_tokens:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(begin["model"], local_files_only=True)
        eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    for row, request in zip(rows, requests(), strict=True):
        assert all(row[key] == value for key, value in request.items())
        if tokenizer is not None:
            ids = row["output_ids"]
            assert runner.encode(tokenizer, request) == row["input_ids"]
            assert 0 < len(ids) <= CAP and eos not in ids[:-1]
            assert (ids[-1] == eos) == row["ended"]
            assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["output"]
    output = directory / "final-records.json"
    assert end["final_records_sha256"] == runner.digest(output)
    assert json.loads(output.read_text()) == {FAMILY: {r["id"]: r["output"] for r in rows}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        rows = list(requests())
        assert len({r["id"] for r in rows}) == len(rows) == 8
        assert all(len(r["evidence_ids"]) == 2 + i.bit_count() for i, r in enumerate(rows))
        print(json.dumps({"packets": {r["id"]: r["evidence_ids"] for r in rows}, "hashes": locks()}, indent=2))
    elif args.mode == "run":
        if args.directory is None or args.model is None:
            cli.error("run requires directory and --model")
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory, verify_tokens=True), ensure_ascii=False, indent=2))
