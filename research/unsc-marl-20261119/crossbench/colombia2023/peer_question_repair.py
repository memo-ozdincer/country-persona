"""Intervene on the question shown to the receiver, using frozen openings."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import peer_question as base

HERE = base.HERE
runner = base.runner
SOURCE = HERE / "peer-question-evidence"
FAMILY = "peer-question-repair"
ARMS = ("original", "no_question", "answerable")
QUESTIONS = {
    "unifil": ("What qualification did Brazil give about the extent to which the French text addressed "
               "Lebanon's concerns, and what did Brazil say about UNIFIL's freedom to operate?"),
    "haiti": ("In what capacity did Mozambique's representative speak, and whose request did that statement "
              "cite when supporting Chapter VII adoption?"),
}


def read(path):
    return json.loads(path.read_text())


def archived():
    transcript = SOURCE / "transcript.jsonl"
    assert runner.digest(transcript) == read(SOURCE / "complete.json")["transcript_sha256"]
    return {r["id"]: r for r in map(json.loads, transcript.read_text().splitlines())}


def openings(rows, case):
    first = rows[f"{case}/shared/open"]
    review = read(SOURCE / "annotations.json")
    assert review["transcript_sha256"] == runner.digest(SOURCE / "transcript.jsonl")
    old = review["families"][case]["question"]["span"]
    text = first["output"]
    assert text.count("Question: " + old) == 1
    return first, {
        "original": text,
        "no_question": text.replace("Question: " + old, "", 1),
        "answerable": text.replace(old, QUESTIONS[case], 1),
    }


def payload(row, key, notes, seen):
    system, user = row["messages"]
    previous = json.loads(user["content"])
    previous["working_notes"] = notes
    return {"id": key, "cap": row["cap"], "evidence_ids": row["evidence_ids"], "seen": seen,
            "messages": [system, {**user, "content": json.dumps(previous, ensure_ascii=False)}]}


def episode(generate):
    before = archived()
    reply_requests = []
    for case in QUESTIONS:
        first, variants = openings(before, case)
        original = before[f"{case}/interactive/reply"]
        for arm, text in variants.items():
            reply_requests.append(payload(original, f"{case}/{arm}/reply", [text], [first["id"]]))
        baseline = payload(original, original["id"], [variants["original"]], original["seen"])
        assert all(original[k] == v for k, v in baseline.items())
    replies = generate(reply_requests)
    finals = []
    for case in QUESTIONS:
        first = before[f"{case}/shared/open"]
        original = before[f"{case}/interactive/final"]
        for arm in ARMS:
            answer = replies[f"{case}/{arm}/reply"]
            # The chair receives the exact same historical opening in all arms.
            finals.append(payload(original, f"{case}/{arm}/final", [first["output"], answer["output"]],
                                  [first["id"], answer["id"]]))
    return [{"family": FAMILY, "reply": replies, "final": generate(finals)}]


def locks():
    files = (Path(__file__), Path(base.__file__), Path(runner.__file__), base.UNIFIL, base.HAITI,
             *(SOURCE / name for name in ("annotations.json", "launch.json", "complete.json", "transcript.jsonl")))
    return {str(p.resolve().relative_to(HERE.parents[1])): runner.digest(p) for p in files}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = (read(directory / name) for name in ("launch.json", "complete.json"))
    trace, finals = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == locks() and finish["transcript_sha256"] == runner.digest(trace)
    assert finish["final_records_sha256"] == runner.digest(finals)
    assert launch["model"] == read(SOURCE / "launch.json")["model"]
    raw = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    used = set()
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")

    def restore(requests):
        for request in requests:
            key = request["id"]
            row = raw[key]
            assert key not in used and all(row[k] == v for k, v in request.items())
            used.add(key)
            assert runner.encode(tok, request) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= request["cap"] and eos not in ids[:-1]
            assert row["ended"] == (ids[-1] == eos) and tok.decode(ids, skip_special_tokens=True).strip() == row["output"]
        return {r["id"]: raw[r["id"]] for r in requests}

    expected, = episode(restore)
    assert set(raw) == used and len(used) == finish["records"] == 12
    assert read(finals) == {FAMILY: {key: row["output"] for key, row in expected["final"].items()}}
    return raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "replay"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        episode(base.mock)
        assert args.model.resolve() == Path(read(SOURCE / "launch.json")["model"]).resolve()
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"exact_transcript_rows": len(replay(args.directory))}, indent=2))
