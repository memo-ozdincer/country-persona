"""Generate one DRC record for every terminal extract set under the fitted protocol."""
import argparse
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

import private_payload as channel
import private_deliberation_caps as interface

HERE = Path(__file__).resolve().parent
runner = interface.runner
SOURCE_IDS = ("mandate", "review", "reports", "updates")
EVIDENCE = HERE / "payload-policy-evidence"
FAMILY = "drc-terminal-extract"


def passages():
    _, _, decks = next(interface.parent.fixtures())
    terms, = decks["A"].values()
    reporting, = decks["B"].values()
    first, rest = terms.split(" and intended ", 1)
    group, updates = reporting.split(" The Group was to ", 1)
    assert first.endswith("1 August 2024") and rest.startswith("to review it and act")
    return (first + ".", "The Council intended " + rest.replace("review it", "review the Experts mandate", 1),
            group, "The Group was to " + updates)


def episode(generate, token):
    base = interface.archived()["drc/independent"]
    evidence = passages()
    assert all(len(channel.payload_tokens(token, quote)) <= channel.LIMIT for quote in evidence)
    row = {k: base[k] for k in ("cap", "evidence_ids", "messages")}
    requests = []
    for size in range(3):
        for subset in combinations(range(len(evidence)), size):
            tag = ",".join(SOURCE_IDS[i] for i in subset) or "public"
            notes = {SOURCE_IDS[i]: evidence[i] for i in subset}
            requests.append(interface.seen(row | {"id": tag}, notes))
    return [{"family": FAMILY, "final": generate(requests)}]


def locks():
    return interface.locks() | {path.name: runner.digest(path)
                                for path in (Path(__file__), Path(channel.__file__))}


def replay(directory):
    import json

    launch, finish = [interface.parent.read(directory / name) for name in ("launch.json", "complete.json")]
    trace, finals = directory / "transcript.jsonl", directory / "final-records.json"
    assert launch["sha256"] == locks() and runner.digest(trace) == finish["transcript_sha256"]
    assert runner.digest(finals) == finish["final_records_sha256"]
    rows = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    assert len(rows) == finish["records"] == 11
    token = channel.tokenizer(launch["model"])
    eos = token.convert_tokens_to_ids("<|im_end|>")

    def restore(batch):
        assert len(batch) == len(rows)
        for request in batch:
            row = rows[request["id"]]
            assert all(row[key] == value for key, value in request.items())
            assert runner.encode(token, request) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
            assert token.decode(ids, skip_special_tokens=True).strip() == row["output"]
        return rows

    episode(restore, token)
    assert interface.parent.read(finals) == {FAMILY: {key: row["output"] for key, row in rows.items()}}
    return rows, token


if __name__ == "__main__":
    import json
    from functools import partial

    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        setup = partial(episode, token=channel.tokenizer(args.model))
        with patch.multiple(runner, episode=setup, locks=locks):
            runner.run(args.model, args.directory)
    else:
        rows, _ = replay(args.directory)
        print(json.dumps({"exact_records": len(rows)}))
