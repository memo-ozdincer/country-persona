"""Measure the actual reply and record produced by each authorized question action."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import peer_index_transfer as baseline

HERE = baseline.HERE
runner = baseline.runner
SOURCE = HERE / "peer-index-transfer-evidence"
FAMILY = "field-question-actions"
ARMS = ("no_question", "actor", "scope")
ACTIONS = {
    "colombia": {
        "actor": "Who delivered the collective A3 statement, and whom did that speaker represent? Cite [A3].",
        "scope": "What did the three African members pledge about the Ethnic Chapter, and which communities were named? Cite [A3].",
    },
    "unami": {
        "actor": "Who was requested to conduct the strategic review, who was to receive it, and by what date? Cite [REVIEW].",
        "scope": "Who was to be consulted for the independent strategic review? Cite [CONSULT].",
    },
}


def frozen_openings():
    path = SOURCE / "transcript.jsonl"
    assert runner.digest(path) == baseline.read(SOURCE / "complete.json")["transcript_sha256"]
    return {row["id"].split("/")[0]: row for row in map(json.loads, path.read_text().splitlines())
            if row["id"].endswith("/common/open")}


def episode(generate):
    cases = list(baseline.fixtures())
    opening = frozen_openings()
    replies = []
    for family, vote, _, _, sources in cases:
        for arm in ARMS:
            question = ACTIONS[family].get(arm)
            incoming = () if question is None else (
                {"id": f"{family}/authorized_menu/{arm}", "output": question},)
            replies.append(baseline.reply(family, arm, vote, sources, incoming))
    answered = generate(replies)
    finals = [baseline.chair(family, arm, vote, public, opening[family], answered[f"{family}/{arm}/reply"])
              for family, vote, public, *_ in cases for arm in ARMS]
    return [{"family": FAMILY, "replies": answered, "final": generate(finals)}]


def locks():
    files = (Path(__file__), Path(baseline.__file__), Path(baseline.base.__file__), Path(runner.__file__),
             *baseline.CASES.values(), HERE / "peer-index-inventory.json",
             *(SOURCE / name for name in ("complete.json", "launch.json", "transcript.jsonl")))
    return {str(p.resolve().relative_to(HERE.parents[1])): runner.digest(p) for p in files}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = (baseline.read(directory / name) for name in ("launch.json", "complete.json"))
    trace = directory / "transcript.jsonl"
    finals = directory / "final-records.json"
    assert launch["sha256"] == locks()
    assert launch["model"] == baseline.read(SOURCE / "launch.json")["model"]
    assert finish["transcript_sha256"] == runner.digest(trace)
    assert finish["final_records_sha256"] == runner.digest(finals)
    raw = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    unseen = set(raw)

    def restore(batch):
        for expected in batch:
            key = expected["id"]
            unseen.remove(key)
            row = raw[key]
            assert all(row[k] == v for k, v in expected.items())
            assert runner.encode(tok, expected) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= expected["cap"] and eos not in ids[:-1]
            assert row["ended"] == (ids[-1] == eos)
            assert row["output"] == tok.decode(ids, skip_special_tokens=True).strip()
        return {r["id"]: raw[r["id"]] for r in batch}

    episodes, = episode(restore)
    assert not unseen and len(raw) == finish["records"] == 12
    assert baseline.read(finals) == {FAMILY: {k: row["output"] for k, row in episodes["final"].items()}}
    return raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "replay"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        assert args.model.resolve() == Path(baseline.read(SOURCE / "launch.json")["model"]).resolve()
        episode(baseline.base.mock)
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"exact_transcript_rows": len(replay(args.directory))}, indent=2))
