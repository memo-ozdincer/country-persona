"""Transfer the frozen DRC drafting contract to three UNAMI packet views."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import payload_writer_contract as contract

HERE = contract.HERE
proto = contract.previous.interface
runner = contract.runner
FAMILY = "unami-legal-force-contract"
VIEWS = ("full", "recurring_and_review", "review_only")
ROOT = HERE / "payload-writer-transfer-evidence"


def requests():
    _, _, decks = next(f for f in proto.parent.fixtures() if f[0] == "unami")
    source = proto.archived()["unami/independent"]
    row = {key: source[key] for key in ("cap", "evidence_ids", "messages")}
    views = {
        "full": {desk: "\n".join(cards.values()) for desk, cards in decks.items()},
        "recurring_and_review": {"A": decks["A"]["REPORT"], "B": decks["B"]["REVIEW"]},
        "review_only": {"B": decks["B"]["REVIEW"]},
    }
    for kind in ("original", "separate"):
        for name, cards in views.items():
            filled = proto.seen(row | {"id": f"{kind}/{name}"}, cards)
            if kind == "separate":
                system, user = filled["messages"]
                contents = json.loads(user["content"])
                contents["task"] = contract.INSTRUCTION
                filled["messages"] = [system, {**user, "content": json.dumps(contents, ensure_ascii=False)}]
            yield filled


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def locks():
    return contract.locks() | {Path(__file__).name: runner.digest(Path(__file__))}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = [json.loads((directory / name).read_text()) for name in ("launch.json", "complete.json")]
    trace, finals = directory / "transcript.jsonl", directory / "final-records.json"
    assert launch["sha256"] == locks() and runner.digest(trace) == finish["transcript_sha256"]
    assert runner.digest(finals) == finish["final_records_sha256"]
    rows = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    assert len(rows) == finish["records"] == 6
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    for wanted in requests():
        raw = rows[wanted["id"]]
        assert all(raw[k] == v for k, v in wanted.items())
        assert runner.encode(token, wanted) == raw["input_ids"]
        ids = raw["output_ids"]
        assert 0 < len(ids) <= raw["cap"] and eos not in ids[:-1] and (ids[-1] == eos) == raw["ended"]
        assert token.decode(ids, skip_special_tokens=True).strip() == raw["output"]
    assert json.loads(finals.read_text()) == {FAMILY: {k: row["output"] for k, row in rows.items()}}
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
