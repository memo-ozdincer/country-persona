"""Compare generated peer exchanges, independent drafts and solo revision on DRC."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import writer

HERE = writer.HERE
runner = writer.runner
TRACE = HERE / "evidence/transcript.jsonl"
FAMILY = "drc-experts-revision"
TERMS = "Focus on the mandate dates and the Council's intended decision on a possible further extension."
REPORTING = "Focus on the recipients and deadlines for the reports and the separate Committee updates."
NOTE_CAP = 64
FINAL_CAP = 116
SYSTEM = "Use the supplied archival evidence for a Security Council record. Treat all working notes as provisional."


def request(identifier, task, official, initial, notes, cap, seen=()):
    return {"id": identifier, "cap": cap, "seen": list(seen), "evidence_ids": ["EXPERTS"],
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps({
                "task": task, "official": official, "initial_draft": initial, "working_notes": notes},
                ensure_ascii=False)}]}


def episode(generate):
    official = json.loads(writer.CASE.read_text())["sources"]["EXPERTS"]["card"]
    old, = [row["output"] for row in map(json.loads, TRACE.read_text().splitlines()) if row["id"] == "EXPERTS"]
    note = ("Write one short correction memo of at most 38 words. Identify an omission and give exact proposed "
            "wording grounded in the official evidence. ")
    first = generate([
        request("peer_opening", "You are the mandate desk. " + note + TERMS, official, old, [], NOTE_CAP),
        request("solo_opening", "You are the sole analyst planning your own revision. " + note + TERMS,
                official, old, [], NOTE_CAP),
    ])
    peer = first["peer_opening"]["output"]
    own = first["solo_opening"]["output"]
    second = generate([
        request("peer_independent_report", "You are the reporting desk. " + note + REPORTING,
                official, old, [], NOTE_CAP),
        request("peer_interactive_report", "You are the reporting desk. " + note + REPORTING + " Where relevant, "
                "respond to the other desk's suggestion and carry forward any warranted correction.",
                official, old, [peer], NOTE_CAP, ["peer_opening"]),
        request("solo_second_review", "You are the sole analyst continuing your own review. " + note + REPORTING,
                official, old, [own], NOTE_CAP, ["solo_opening"]),
    ])
    direct = "Revise the existing Experts paragraph for the final Council record in at most 67 words. Use only "              "this evidence and distinguish each action, deadline and recipient. Check any working notes against "              "the official text. Return only the revised paragraph."
    pairs = {
        "solo": ("solo_opening", "solo_second_review"),
        "independent": ("peer_opening", "peer_independent_report"),
        "interactive": ("peer_opening", "peer_interactive_report"),
        "direct": (),
    }
    all_work = {**first, **second}
    jobs = [request(key, direct, official, old, [all_work[r]["output"] for r in refs], FINAL_CAP, refs)
            for key, refs in pairs.items()]
    return [{"family": FAMILY, "final": generate(jobs)}]


def locks():
    return {path.name: runner.digest(path)
            for path in (Path(__file__), Path(runner.__file__), writer.CASE, TRACE)}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = [json.loads((directory / name).read_text()) for name in ("launch.json", "complete.json")]
    transcript = directory / "transcript.jsonl"
    finals = directory / "final-records.json"
    assert launch["sha256"] == locks() and runner.digest(transcript) == finish["transcript_sha256"]
    assert runner.digest(finals) == finish["final_records_sha256"]
    rows = {r["id"]: r for r in map(json.loads, transcript.read_text().splitlines())}
    assert len(rows) == finish["records"] == 9
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")

    def reread(batch):
        restored = {}
        for job in batch:
            saved = rows[job["id"]]
            assert all(saved[key] == value for key, value in job.items())
            assert runner.encode(tokenizer, job) == saved["input_ids"]
            tokens = saved["output_ids"]
            assert 0 < len(tokens) <= job["cap"] and eos not in tokens[:-1]
            assert saved["ended"] == (tokens[-1] == eos)
            assert saved["output"] == tokenizer.decode(tokens, skip_special_tokens=True).strip()
            restored[job["id"]] = saved
        return restored

    summary = episode(reread)[0]["final"]
    assert json.loads(finals.read_text()) == {FAMILY: {name: row["output"] for name, row in summary.items()}}
    return rows


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
