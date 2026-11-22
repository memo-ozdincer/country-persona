"""Run a matched archive-summary comparison with separated source holdings."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from unittest.mock import patch

import deliberation

HERE = deliberation.HERE
runner = deliberation.runner
DRC = deliberation.writer.CASE
UNAMI = HERE.parent / "unami2023/case.json"
CAPS = {"note": 62, "final": 112}
ARMS = ("pooled_solo", "independent", "interactive", "local_solo")


def read(path):
    return json.loads(path.read_text())


def fixtures():
    drc = read(DRC)
    term, report = drc["sources"]["EXPERTS"]["card"].split(" It requested ", 1)
    yield "drc", drc["public"], {
        "A": {"EXPERTS-TERM": term},
        "B": {"EXPERTS-REPORT": "The Council requested " + report},
    }
    iraq = read(UNAMI)
    yield "unami", iraq["public"]["VOTE"], {
        "A": {"MANDATE": iraq["roles"]["mandate desk"]["TERM"],
              "REPORT": iraq["roles"]["mandate desk"]["REPORT"]},
        "B": {"REVIEW": iraq["roles"]["review desk"]["REVIEW"],
              "CONSULT": iraq["roles"]["review desk"]["CONSULT"]},
    }


def request(key, task, public, sources, notes, stage):
    family, name = key
    return {
        "id": f"{family}/{name}", "cap": CAPS[stage], "evidence_ids": list(sources),
        "seen": [r["id"] for r in notes], "messages": [
            {"role": "system", "content": "Write an accurate historical UN record using the supplied material. "
             "Working notes are evidence from the session and can be incomplete. Omit facts with no evidence."},
            {"role": "user", "content": json.dumps({"task": task, "public_record": public,
                                                   "local_source_cards": sources,
                                                   "working_notes": [r["output"] for r in notes]},
                                                  ensure_ascii=False)},
        ],
    }


def episode(generate):
    cases = list(fixtures())
    memo_a = "Write a short archival memo in at most 40 words on the mandate and its timing. Preserve the actor and force."
    memo_b = "Write a short archival memo in at most 40 words on the reporting or review responsibilities. " \
             "Prioritise the details you can supply from your source cards, including recipients and deadlines. " \
             "Address a material overlap with any other note if it affects the final record."
    finals = "Write only a supplement of at most 73 words. Preserve distinct mandates and review or reporting " \
             "requirements, the responsible institution, recipient and timing. Preserve relevant consultation " \
             "and update conditions when supported. The vote is already written. Do not infer missing facts."
    first = []
    for family, public, decks in cases:
        full = decks["A"] | decks["B"]
        first.extend(request((family, name), memo_a, public, deck, (), "note")
                     for name, deck in (("desk_a", decks["A"]), ("solo_a", full), ("local_a", {})))
    opened = generate(first)

    second = []
    for family, public, decks in cases:
        full = decks["A"] | decks["B"]
        for name, deck, incoming in (
            ("desk_b_independent", decks["B"], ()),
            ("desk_b_interactive", decks["B"], ("desk_a",)),
            ("solo_b", full, ("solo_a",)),
            ("local_b", {}, ("local_a",)),
        ):
            notes = [opened[f"{family}/{key}"] for key in incoming]
            second.append(request((family, name), memo_b, public, deck, notes, "note"))
    working = opened | generate(second)

    final_jobs = []
    for family, public, decks in cases:
        for name, notes, evidence in (
            ("pooled_solo", ("solo_a", "solo_b"), decks["A"] | decks["B"]),
            ("independent", ("desk_a", "desk_b_independent"), {}),
            ("interactive", ("desk_a", "desk_b_interactive"), {}),
            ("local_solo", ("local_a", "local_b"), {}),
        ):
            context = [working[f"{family}/{key}"] for key in notes]
            final_jobs.append(request((family, name), finals, public, evidence, context, "final"))
    output = generate(final_jobs)
    return [{"family": family, "final": {name: output[f"{family}/{name}"] for name in ARMS}}
            for family, _, _ in cases]


def locks():
    return {str(path.relative_to(HERE.parents[1])): runner.digest(path) for path in (
        Path(__file__), Path(runner.__file__), DRC, UNAMI)}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = [read(directory / name) for name in ("launch.json", "complete.json")]
    trace = directory / "transcript.jsonl"
    finals = directory / "final-records.json"
    assert launch["sha256"] == locks() and runner.digest(trace) == finish["transcript_sha256"]
    assert runner.digest(finals) == finish["final_records_sha256"]
    saved = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    assert len(saved) == finish["records"] == 22
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    consumed = set()

    def capture(batch):
        for job in batch:
            key = job["id"]
            row = saved[key]
            assert key not in consumed
            consumed.add(key)
            assert all(row[k] == value for k, value in job.items())
            assert runner.encode(token, job) == row["input_ids"]
            ids = row["output_ids"]
            assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
            assert token.decode(ids, skip_special_tokens=True).strip() == row["output"]
        return {job["id"]: saved[job["id"]] for job in batch}

    episodes = episode(capture)
    assert consumed == saved.keys()
    assert read(finals) == {ep["family"]: {name: rec["output"] for name, rec in ep["final"].items()}
                            for ep in episodes}
    return saved


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
