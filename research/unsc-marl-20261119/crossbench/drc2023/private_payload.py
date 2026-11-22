"""Compare model-written notes with exact extracts on a bounded source channel."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import private_deliberation_caps as prior

parent = prior.parent
runner = prior.runner
HERE = parent.HERE
LIMIT = 48
ARMS = ("prefix", "sentences", "independent", "interactive")
DIRECTIONS = ("Send only factual content that the chair needs from your own cards. Omit the public roll call and "
              "any preamble. Use terse clauses with the actor, timing and qualification intact. ")


def payload_tokens(token, text):
    return token.encode(text, add_special_tokens=False)


def limited(token, text):
    ids = payload_tokens(token, text)
    if len(ids) <= LIMIT:
        return text
    for end in range(LIMIT, -1, -1):
        trimmed = token.decode(ids[:end], skip_special_tokens=True).rstrip()
        if "\ufffd" not in trimmed and len(payload_tokens(token, trimmed)) <= LIMIT:
            return trimmed
    raise AssertionError("Empty payload must fit")


def exact_messages(token, deck):
    passages = [line.split(". ", 2)[-1] if line.startswith("Resolution ") else line
                for line in deck.values()]
    text = " ".join(passages)
    # The sentence control is deterministic and uses no case outcomes or rubric.
    units = re.split(r"(?<=\.)\s+(?=[A-Z])", text)
    selected = []
    for unit in units:
        if len(payload_tokens(token, " ".join([*selected, unit]))) <= LIMIT:
            selected.append(unit)
    # A long single sentence may leave no complete excerpt. In that case
    # provide the same available prefix as the truncation control.
    return {"prefix": limited(token, text),
            "sentences": " ".join(selected) if selected else limited(token, text)}


def note_job(family, name, public, cards, notes, original):
    base = json.loads(original["messages"][1]["content"])
    return parent.request((family, name), DIRECTIONS + base["task"], public, cards, notes, "note") | {"cap": LIMIT + 1}


def episode(generate, token):
    case_rows = list(parent.fixtures())
    old = prior.archived()
    first = generate([note_job(f, "new_a", public, cards["A"], (), old[f"{f}/desk_a"])
                      for f, public, cards in case_rows])

    def transport(row):
        visible = limited(token, row["output"])
        return {"id": row["id"], "output": visible}

    reports = []
    for family, public, cards in case_rows:
        for arm in ("independent", "interactive"):
            notes = [transport(first[f"{family}/new_a"])] if arm == "interactive" else []
            reports.append(note_job(family, "new_b_" + arm, public, cards["B"], notes,
                                    old[f"{family}/desk_b_{arm}"]))
    second = generate(reports)
    chairs = []
    for family, public, cards in case_rows:
        base = old[f"{family}/independent"]
        job = {key: base[key] for key in ("cap", "evidence_ids", "messages")}
        exact = {desk: exact_messages(token, deck) for desk, deck in cards.items()}
        a = transport(first[f"{family}/new_a"])
        for arm in ARMS:
            if arm in {"independent", "interactive"}:
                b = transport(second[f"{family}/new_b_{arm}"])
                notes = {a["id"]: a["output"], b["id"]: b["output"]}
            else:
                notes = {f"{family}/{desk}_{arm}": alternatives[arm] for desk, alternatives in exact.items()}
            assert all(len(payload_tokens(token, text)) <= LIMIT for text in notes.values())
            chairs.append(prior.seen(job | {"id": f"{family}/{arm}"}, notes))
    final = generate(chairs)
    return [{"family": f, "final": {arm: final[f"{f}/{arm}"] for arm in ARMS}} for f, _, _ in case_rows]


def locks():
    return prior.locks() | {Path(__file__).name: runner.digest(Path(__file__))}


def tokenizer(model):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model, local_files_only=True)


def replay(directory):
    launch, finish = [parent.read(directory / name) for name in ("launch.json", "complete.json")]
    trace, final = directory / "transcript.jsonl", directory / "final-records.json"
    assert launch["sha256"] == locks() and runner.digest(trace) == finish["transcript_sha256"]
    assert runner.digest(final) == finish["final_records_sha256"]
    rows = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    assert len(rows) == finish["records"] == 14
    tok = tokenizer(launch["model"])
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    used = set()

    def restore(batch):
        for job in batch:
            identifier = job["id"]
            assert identifier not in used
            used.add(identifier)
            row = rows[identifier]
            assert all(row[k] == v for k, v in job.items())
            assert runner.encode(tok, job) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= job["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
            assert tok.decode(ids, skip_special_tokens=True).strip() == row["output"]
        return {job["id"]: rows[job["id"]] for job in batch}

    summarized = episode(restore, tok)
    assert used == rows.keys()
    assert parent.read(final) == {e["family"]: {name: r["output"] for name, r in e["final"].items()}
                                 for e in summarized}
    return rows, tok


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        from functools import partial
        rerun = partial(episode, token=tokenizer(args.model))
        with patch.multiple(runner, episode=rerun, locks=locks):
            runner.run(args.model, args.directory)
    else:
        rows, _ = replay(args.directory)
        print(json.dumps({"exact_records": len(rows)}))
