"""Generate one frozen-model supplement for each reachable Iraq receipt set."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import sys
from unittest.mock import patch

from episode import HERE, runner

FTF = HERE.parent / "ftf2020"
sys.path.insert(0, str(FTF))
import adaptive_transfer as transfer

CASE = HERE / "case.json"
CAP = 200


def records():
    decks, _ = transfer.named_sources()
    cards = decks["unami"][0]
    for size in range(1, 4):
        for received in combinations(cards, size):
            tag = sha256(("unami-receipt-v1/" + "/".join(received)).encode()).hexdigest()[:10]
            yield tag, received, {name: cards[name] for name in received}


def plan():
    task = (
        "Write the supplementary part of a retrospective UNAMI Council record using only the received evidence. "
        "The main record already covers the vote, mandate expiry, and recurring report. "
        "Use at most 106 words. Give one separate line for each received source, with its exact bracketed source ID. "
        "Preserve each named actor, action, recipient, deadline, and qualification. Keep a request distinct from "
        "a completed action, advice distinct from authority, and a statement of support distinct from a requirement. "
        "Coordinators will join these lines to the main record without rewriting them."
    )
    return [{"id": tag, "evidence_ids": list(ids), "cap": CAP, "messages": [
        {"role": "system", "content": "You are a neutral historical Council record writer. Treat these source "
                                       "summaries as the only evidence. Output the supplement itself."},
        {"role": "user", "content": json.dumps({"task": task, "received_evidence": cards}, ensure_ascii=False)}]}
        for tag, ids, cards in records()]


def locks():
    return {f.name: runner.digest(f) for f in (CASE, Path(__file__).resolve(), Path(runner.__file__),
                                              Path(transfer.__file__),
                                              transfer.HERE / "adaptive-align-results.json",
                                              transfer.HERE / "adaptive-transfer-results.json")}


def episode(generate):
    return [{"family": "unami-receipts", "final": generate(plan())}]


def replay(directory):
    from transformers import AutoTokenizer

    launch = transfer.read(directory / "launch.json")
    finish = transfer.read(directory / "complete.json")
    assert launch["sha256"] == locks()
    raw = directory / "transcript.jsonl"
    assert finish["transcript_sha256"] == runner.digest(raw)
    rows = {r["id"]: r for r in map(json.loads, raw.read_text().splitlines())}
    assert len(rows) == len(plan()) == finish["records"] == 14
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    final = directory / "final-records.json"
    assert finish["final_records_sha256"] == runner.digest(final)
    text = transfer.read(final)["unami-receipts"]
    assert rows.keys() == text.keys()
    for expected in plan():
        row = rows[expected["id"]]
        assert all(row[k] == v for k, v in expected.items())
        assert row["input_ids"] == runner.encode(tokenizer, expected)
        ids = row["output_ids"]
        assert 0 < len(ids) <= CAP and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert row["output"] == text[row["id"]] == tokenizer.decode(ids, skip_special_tokens=True).strip()
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        requests = plan()
        assert len(requests) == len({r["id"] for r in requests}) == 14
        print(json.dumps({"calls": len(requests), "cap": CAP, "source_sets": [r["evidence_ids"] for r in requests]}, indent=2))
    elif args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified": len(replay(args.directory))}, indent=2))
