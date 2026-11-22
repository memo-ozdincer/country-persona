"""Replay a fixed opening with a constraint-only peer message and unchanged writer."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "syria-baseline"
sys.path.insert(0, str(BASE))
import collect as baseline
import review

E = baseline.suite.e
STUDY_FILES = (Path(__file__), HERE / "protocol.md", BASE / "notes-marks.json", BASE / "evidence/complete.json")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def contexts():
    marks = E.read(BASE / "notes-marks.json")
    for key, case, arm, order, calls in review.episodes():
        if arm != "peer":
            continue
        note_key = "notes-" + E.checksum([case["id"], [r["text"] for r in calls[:2]]])[:16]
        projected, = [r for r in marks[note_key] if r["turn"] == 0 and r["field"] != "id"]
        role, span = projected["role"], projected["span"]
        assert role == calls[0]["speaker"] and span in calls[0]["text"]
        replacement = f'Fictional workshop constraint stated by {role}: {projected["field"]} = {projected["value"]}.'
        assert projected["field"] in {"duration", "checkpoint"}
        local_card = case["membership"][order]
        assert projected["value"] == local_card[projected["field"]]
        opening = dict(calls[0], text=replacement)
        yield key, case, order, calls, opening, projected


def requests(case, order, calls, opening, reply=None):
    original = E.build_request(case, "peer", order, calls[:1 if reply is None else 2])
    changed = E.build_request(case, "peer", order, [opening] if reply is None else [opening, reply])
    assert original["max_output_tokens"] == changed["max_output_tokens"]
    assert original["messages"][0] == changed["messages"][0]
    before, after = (json.loads(r["messages"][1]["content"]) for r in (original, changed))
    assert before.pop("notes") != after.pop("notes") and before == after
    return changed


def collect(generate, directory):
    rows = []
    for key, case, order, calls, opening, projected in contexts():
        note = requests(case, order, calls, opening)
        note_reply = generate(note)
        second = dict(calls[1], **note_reply)
        final = requests(case, order, calls, opening, second)
        final_reply = generate(final)
        rows.append({"episode": key, "opening_projection": projected, "projected_text": opening["text"],
                     "note": {"request": note, "response": note_reply},
                     "final": {"request": final, "response": final_reply}})
    (directory / "episodes.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    pins = {p.name: digest(p) for p in STUDY_FILES}
    (directory / "projection-lock.json").write_text(json.dumps(pins, indent=2) + "\n")


def verify(directory):
    from transformers import AutoTokenizer

    manifest = E.read(directory / "complete.json")
    assert all(digest(directory / filename) == stamp for filename, stamp in manifest.items())
    assert E.read(directory / "projection-lock.json") == {p.name: digest(p) for p in STUDY_FILES}
    tokenizer = AutoTokenizer.from_pretrained(baseline.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    rows = E.read(directory / "episodes.json")
    raw = iter(json.loads(line) for line in (directory / "tokens.jsonl").read_text().splitlines())
    for row, (key, case, order, calls, opening, projected) in zip(rows, contexts(), strict=True):
        assert row["episode"] == key and row["opening_projection"] == projected
        assert row["projected_text"] == opening["text"]
        expected = (
            requests(case, order, calls, opening),
            requests(case, order, calls, opening, dict(calls[1], **row["note"]["response"])),
        )
        for name, request in zip(("note", "final"), expected, strict=True):
            record, token = row[name], next(raw)
            assert record["request"] == request and record["response"] == token["response"]
            assert token["input_ids"] == baseline.prompt(tokenizer, request)
            ids = token["output_ids"]
            assert len(ids) <= request["max_output_tokens"] and eos not in ids[:-1]
            assert bool(ids and ids[-1] == eos) == (record["response"]["termination"] == "complete")
            assert tokenizer.decode(ids, skip_special_tokens=True).strip() == record["response"]["text"]
    assert next(raw, None) is None
    return {"verified_episodes": len(rows), "replayed_fresh_calls": len(rows) * 2,
            "reused_openings": len(rows), "optimizer_updates": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.object(baseline.suite, "collect", collect):
            baseline.run(args.directory)
    else:
        E.emit(verify(args.directory))
