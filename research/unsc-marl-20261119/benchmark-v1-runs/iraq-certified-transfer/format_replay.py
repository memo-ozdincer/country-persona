"""Replay the same certified writer with the v1 parser's format spelled out."""
import argparse
import copy
import json
from pathlib import Path
from unittest.mock import patch

import transfer

HERE, E, COLLECTOR = transfer.HERE, transfer.E, transfer.COLLECTOR
ORIGINAL = "Put Decision: PACKAGE-ID or Decision: IMPASSE or Decision: UNRESOLVED on its own first line."
CLARIFIED = ("On the first line use Decision: followed by a space and exactly one of A, B, C, D, IMPASSE, or UNRESOLVED. "
             "For a package use the bare letter without a PACKAGE- prefix.")


def requests():
    for line in (HERE / "evidence/episodes.jsonl").read_text().splitlines():
        row = json.loads(line)
        req = copy.deepcopy(row["writers"]["with_certificate"]["request"])
        payload = json.loads(req["messages"][1]["content"])
        assert payload["task"].count(ORIGINAL) == 1
        payload["task"] = payload["task"].replace(ORIGINAL, CLARIFIED)
        req["messages"][1]["content"] = json.dumps(payload, ensure_ascii=False)
        yield row["id"], req


def pins():
    files = (Path(__file__), HERE / "format-protocol.md", HERE / "evidence/complete.json", E.HERE / "release.json")
    return {str(p.relative_to(HERE.parent.parent)): COLLECTOR.sha(p) for p in files}


def collect(generate, directory):
    for key, req in requests():
        COLLECTOR.suite.append(directory / "records.jsonl", {"id": key, "request": req, "response": generate(req)})
    (directory / "format-lock.json").write_text(json.dumps(pins(), indent=2) + "\n")


def verify(directory):
    from transformers import AutoTokenizer

    assert all(COLLECTOR.sha(directory / f) == stamp for f, stamp in E.read(directory / "complete.json").items())
    assert E.read(directory / "format-lock.json") == pins()
    t = AutoTokenizer.from_pretrained(COLLECTOR.MODEL, local_files_only=True)
    eos = t.convert_tokens_to_ids("<|im_end|>")
    rows, trace = [[json.loads(line) for line in (directory / f).read_text().splitlines()]
                   for f in ("records.jsonl", "tokens.jsonl")]
    for (key, req), row, receipt in zip(requests(), rows, trace, strict=True):
        assert row["id"] == key and req == row["request"] and row["response"] == receipt["response"]
        assert COLLECTOR.prompt(t, req) == receipt["input_ids"]
        ids = receipt["output_ids"]
        assert ids and len(ids) <= req["max_output_tokens"] and eos not in ids[:-1]
        assert (ids[-1] == eos) == (row["response"]["termination"] == "complete")
        assert t.decode(ids, skip_special_tokens=True).strip() == row["response"]["text"]
    return {"verified_live_calls": len(rows), "optimizer_updates": 0}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("--directory", type=Path, default=HERE / "format-evidence")
    args = p.parse_args()
    if args.mode == "run":
        with patch.object(COLLECTOR.suite, "collect", collect), patch.object(COLLECTOR, "roster", transfer.cases):
            COLLECTOR.run(args.directory)
    else:
        E.emit(verify(args.directory))
