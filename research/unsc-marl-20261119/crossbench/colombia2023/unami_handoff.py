"""Factor source verification and explicit actor-recipient binding in the UNAMI handoff."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import field_question_actions as prior

HERE = prior.HERE
baseline = prior.baseline
runner = prior.runner
SOURCE = HERE / "field-question-action-evidence"
FAMILY = "unami-handoff"
REPLIES = ("no_question", "actor")
MODES = ("plain", "bind")
SOURCES = ("notes", "report_card")
BIND = (" Put each distinct recurring reporting obligation and each distinct one-time review in its own sentence. "
        "In each sentence preserve its actor, receiving institution and deadline or reporting frequency, only where "
        "the evidence states them. Retain independence if stated. Official documentary cards govern when they conflict with a working note.")


def archived():
    trace = SOURCE / "transcript.jsonl"
    assert runner.digest(trace) == baseline.read(SOURCE / "complete.json")["transcript_sha256"]
    return {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}


def requests():
    _, vote, public, first, second = next(row for row in baseline.fixtures() if row[0] == "unami")
    open_note = prior.frozen_openings()["unami"]
    prior_rows = archived()
    for incoming in REPLIES:
        reply = prior_rows[f"unami/{incoming}/reply"]
        for mode in MODES:
            for visibility in SOURCES:
                evidence = public if visibility == "notes" else public | {"REPORT": first["REPORT"]}
                row = baseline.chair("unami", f"{incoming}_{mode}_{visibility}", vote, evidence, open_note, reply)
                if mode == "bind":
                    instruction(row, BIND)
                if mode == "plain" and visibility == "notes":
                    original = prior_rows[f"unami/{incoming}/final"]
                    assert all(row[key] == original[key] for key in ("messages", "cap", "evidence_ids", "seen"))
                yield row
    # This upper-information comparator gives the same writer all official cards
    # and the edited instruction in one pass, with no generated working notes.
    pooled = baseline.chair("unami", "pooled_bind", vote, public | first | second, open_note,
                            prior_rows[f"unami/{REPLIES[0]}/reply"])
    pooled["seen"] = []
    user = pooled["messages"][-1]
    prompt = json.loads(user["content"])
    prompt["working_notes"] = []
    user["content"] = json.dumps(prompt, ensure_ascii=False)
    instruction(pooled, BIND)
    yield pooled


def instruction(row, text):
    user = row["messages"][-1]
    prompt = json.loads(user["content"])
    prompt["task"] += text
    user["content"] = json.dumps(prompt, ensure_ascii=False)


def locks():
    paths = (Path(__file__), Path(prior.__file__), Path(baseline.__file__),
             Path(baseline.base.__file__), Path(runner.__file__), baseline.CASES["unami"],
             *(SOURCE / name for name in ("complete.json", "launch.json", "transcript.jsonl")),
             prior.SOURCE / "transcript.jsonl")
    return {str(p.resolve().relative_to(HERE.parents[1])): runner.digest(p) for p in paths}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def replay(directory):
    from transformers import AutoTokenizer

    launch, end = (baseline.read(directory / name) for name in ("launch.json", "complete.json"))
    trace, finals = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == locks() and end["transcript_sha256"] == runner.digest(trace)
    assert end["final_records_sha256"] == runner.digest(finals)
    assert launch["model"] == baseline.read(SOURCE / "launch.json")["model"]
    rows = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    expected = {row["id"]: row for row in requests()}
    assert rows.keys() == expected.keys() and len(rows) == end["records"] == 9
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    for uid, prompt in expected.items():
        row = rows[uid]
        assert all(row[key] == value for key, value in prompt.items())
        assert runner.encode(tok, prompt) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert row["output"] == tok.decode(ids, skip_special_tokens=True).strip()
    assert baseline.read(finals) == {FAMILY: {key: row["output"] for key, row in rows.items()}}
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "replay"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        assert args.model.resolve() == Path(baseline.read(SOURCE / "launch.json")["model"]).resolve()
        assert len(list(requests())) == 9
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"exact_rows": len(replay(args.directory))}, indent=2))
