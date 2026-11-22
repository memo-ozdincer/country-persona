"""Rerun only the three MINURSO final writers with concise drafting instructions."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as runner
from source_record_minurso_review import verified_episode

ARCHIVE = Path(__file__).resolve().parent.parent / "evidence/source-record-minurso"
SYSTEM = (
    "You are a neutral historical record writer. Output exactly five brief factual sentences, in order: "
    "adoption, failed amendments, Algerian reservation, Swiss amendment votes and reason, mandate limits. "
    "Spend no words on a title, introduction, or analysis of your task. Aim for at most 115 words in total. "
    "Use the evidence to check each sentence and cite a short source ID. Drafts are provisional. "
    "Distinguish formal Council acts, proposals, and national positions."
)


def locks():
    files = (Path(__file__), Path(runner.__file__), Path(verified_episode.__code__.co_filename),
             *(ARCHIVE / name for name in ("launch.json", "complete.json", "transcript.jsonl")))
    return {relative.name: sha256(relative.read_bytes()).hexdigest() for relative in files}


def requests(item):
    return [{k: row[k] for k in ("id", "evidence_ids", "seen", "cap")} | {
        "messages": [{"role": "system", "content": SYSTEM}, row["messages"][1]],
    } for row in item["final"].values()]


def run(model, directory):
    item, _ = verified_episode(ARCHIVE)

    def episode(generate):
        return [{"family": item["family"], "final": generate(requests(item))}]

    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(model, directory)


def replay(directory):
    from transformers import AutoTokenizer

    item, _ = verified_episode(ARCHIVE)
    start = json.loads((directory / "launch.json").read_text())
    end = json.loads((directory / "complete.json").read_text())
    path = directory / "transcript.jsonl"
    assert start["sha256"] == locks() and end["transcript_sha256"] == runner.digest(path)
    base = json.loads((ARCHIVE / "launch.json").read_text())
    assert start["model"] == base["model"]
    tokenizer = AutoTokenizer.from_pretrained(start["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    rows = list(map(json.loads, path.read_text().splitlines()))
    assert len(rows) == end["records"] == 3
    for row, req in zip(rows, requests(item), strict=True):
        assert all(row[k] == v for k, v in req.items())
        assert runner.encode(tokenizer, req) == row["input_ids"]
        assert 0 < len(row["output_ids"]) <= row["cap"]
        assert eos not in row["output_ids"][:-1]
        assert tokenizer.decode(row["output_ids"], skip_special_tokens=True).strip() == row["output"]
        assert (row["output_ids"][-1] == eos) == row["ended"]
    finals = directory / "final-records.json"
    assert runner.digest(finals) == end["final_records_sha256"]
    assert json.loads(finals.read_text()) == {item["family"]: {row["id"]: row["output"] for row in rows}}
    return item, rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "replay"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        if args.model is None:
            parser.error("run requires --model")
        run(args.model, args.directory)
    else:
        _, rows = replay(args.directory)
        print(json.dumps({r["id"]: {"ended": r["ended"], "tokens": len(r["output_ids"]),
                                   "words": len(r["output"].split())} for r in rows}, indent=2))
