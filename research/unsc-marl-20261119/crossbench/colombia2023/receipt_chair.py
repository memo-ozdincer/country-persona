"""Generate a Colombia record body for each reachable source packet."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from unittest.mock import patch

import provenance_chair as provenance
from verified_bank import ANCHORS, CASE, HERE, compile_bank, runner

CAP = 216
SOURCE = provenance.SOURCE
PARENT = provenance.PARENT / "transcript.jsonl"
TASK = ("Write a retrospective supplement for the Council record in at most 155 words. The roll call is already "
        "recorded. Use only the documentary sources supplied here. Treat provisional notes as unverified advice and "
        "keep the documented speaker, represented party, legal stage and every material qualification. Give one short "
        "paragraph per received source with its exact bracketed source ID. Preserve distinct responsibilities and conditions. "
        "Only when the official authority paragraph and both delegation statements are present, add one sentence on the "
        "limited overlap and whether the resolution granted new EMC authority. Give no introduction or closing summary.")


def planned():
    ids, _ = compile_bank()
    case = json.loads(CASE.read_text())
    docs = {**case["public"], **{k: v for group in case["roles"].values() for k, v in group.items()}}
    ledger = provenance.ledger(docs)
    notes = {r["id"].split("/", 1)[-1]: r for r in map(json.loads, PARENT.read_text().splitlines())}
    linked = {"BRAZIL": notes["interactive/revision_0"], "A3": notes["interactive/revision_1"]}
    for width in (1, 2, 3):
        for subset in combinations(ids, width):
            nonce = sha256(("colombia-receipt-v1/" + "/".join(subset)).encode()).hexdigest()[:10]
            optional = [linked[k] for k in subset if k in linked]
            content = {"task": TASK, "documentary_sources": {k: docs[k] for k in subset},
                       "documentary_fields": {k: ledger[k] for k in subset},
                       "provisional_notes": [r["output"] for r in optional]}
            yield {"id": nonce, "cap": CAP, "evidence_ids": list(subset), "seen": [r["id"] for r in optional],
                   "messages": [{"role": "system", "content": "You are the archival chair. The dated documentary "
                                 "sources define the factual scope of the supplement."},
                                {"role": "user", "content": json.dumps(content, ensure_ascii=False)}]}


def locks():
    files = (CASE, SOURCE, PARENT, ANCHORS, Path(__file__), Path(runner.__file__),
             HERE / "specialist-fit-results.json", HERE / "specialist-script-results.json")
    return {f.name: runner.digest(f) for f in files}


def episode(generate):
    return [{"family": "colombia-receipt-chair", "final": generate(list(planned()))}]


def replay(directory):
    from transformers import AutoTokenizer

    read = lambda path: json.loads(path.read_text())
    launch = read(directory / "launch.json")
    finish = read(directory / "complete.json")
    trace = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    assert launch["sha256"] == locks() and finish["transcript_sha256"] == runner.digest(trace)
    assert finish["final_records_sha256"] == runner.digest(final)
    records = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    texts = read(final)["colombia-receipt-chair"]
    assert len(records) == len(texts) == finish["records"] == 14
    enc = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = enc.convert_tokens_to_ids("<|im_end|>")
    for request in planned():
        row = records[request["id"]]
        assert all(row[k] == v for k, v in request.items())
        ids = row["output_ids"]
        assert len(ids) <= CAP and ids and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert row["input_ids"] == runner.encode(enc, request)
        assert texts[row["id"]] == row["output"] == enc.decode(ids, skip_special_tokens=True).strip()
    return records


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    rows = list(planned())
    assert len(rows) == len({r["id"] for r in rows}) == 14
    if args.mode == "check":
        print(json.dumps({"calls": len(rows), "cap": CAP, "seen_sets": [r["evidence_ids"] for r in rows]}, indent=2))
    elif args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"records": len(replay(args.directory)), "exact_replay": True}, indent=2))
