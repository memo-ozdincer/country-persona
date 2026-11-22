"""Run a frozen field-writing transfer and matched whole-packet controls."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "benchmark-kit/validity-audit"))
import source_record_run as runner

CASE = HERE / "case.json"
TASKS = {
    "MANDATE": "Use two short sentences. Start with the Council's Chapter VII authorization to Member States and preserve cooperation with Haiti's Government. State the twelve-month term and separate nine-month review, both from adoption.",
    "SAFEGUARDS": "Use two short sentences. Identify who contributes voluntarily. Name applicable international human rights law and the Council's call for the mission to set up oversight to prevent rights violations or abuse.",
    "CHINA": "Use at most 48 words. Identify China's stated reason for caution on Chapter VII and its demand for consultation with Haiti. Separately retain the agreed political transition, credible timetable and CARICOM and BINUH mediation.",
    "A3": "Use at most 43 words. Name the speaker and the group represented. Preserve the group's support for adoption at Haiti's request, and its call for an inclusive political transition and transparent, credible elections.",
    "overlap": "State the common position and the different recorded stances toward adoption in at most 32 words. Use ordinary diplomatic prose and cite [VOTE, CHINA, A3].",
}
PACKETS = {
    "rights_and_china": ["MANDATE", "SAFEGUARDS", "CHINA"],
    "rights_and_a3": ["MANDATE", "SAFEGUARDS", "A3"],
    "both_statements": ["MANDATE", "CHINA", "A3"],
}
SYS = "You write a retrospective Council record. Use the supplied documentary evidence as the only source of factual claims."


def build():
    case = json.loads(CASE.read_text())
    cards = case["sources"]
    rows = []
    for field, task in TASKS.items():
        if field == "overlap":
            ids = list(case["comparison_projection"])
            evidence = case["comparison_projection"]
        else:
            ids = [field]
            evidence = {field: cards[field]}
            task += f" Cite [{field}]."
        content = {"task": "Write just this record field. The other fields are prepared separately. " + task,
                   "source_material": evidence}
        rows.append(request(field, ids, content, 104, "field"))
    for name, ids in PACKETS.items():
        task = ("Write a concise supplement for a retrospective Council record. The official roll call is already recorded. "
                "Use only the supplied documentary sources and preserve the actors, decisions, dates, reasons and qualifications "
                "of each supplied card. Give exact bracketed source IDs. Compare national positions only when both are present.")
        payload = {"task": task, "source_material": {k: cards[k] for k in ids}}
        if {"CHINA", "A3"} <= set(ids):
            payload["comparison_fields"] = case["comparison_projection"]
        rows.append(request(name, ids, payload, 216, "whole"))
    return rows


def request(name, ids, body, cap, mode):
    return {"id": name, "cap": cap, "mode": mode, "evidence_ids": ids, "messages": [
        {"role": "system", "content": SYS}, {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]}


def locks():
    files = (CASE, Path(__file__), Path(runner.__file__), HERE / "acceptance.json")
    return {f.name: runner.digest(f) for f in files}


def episode(generate):
    bank = build()
    final = {}
    for mode in ("field", "whole"):
        final.update(generate([row for row in bank if row["mode"] == mode]))
    return [{"family": "haiti-writer-transfer", "final": final}]


def replay(directory):
    from transformers import AutoTokenizer

    trace = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    launch, complete = [json.loads((directory / name).read_text()) for name in ("launch.json", "complete.json")]
    assert launch["sha256"] == locks()
    assert complete["transcript_sha256"] == runner.digest(trace)
    assert complete["final_records_sha256"] == runner.digest(final)
    rows = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    archived = json.loads(final.read_text())["haiti-writer-transfer"]
    assert len(rows) == len(archived) == complete["records"] == len(build())
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    for req in build():
        row = rows[req["id"]]
        assert all(row[k] == v for k, v in req.items())
        ids = row["output_ids"]
        assert row["input_ids"] == runner.encode(tok, req)
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert row["output"] == archived[row["id"]] == tok.decode(ids, skip_special_tokens=True).strip()
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({r["id"]: {"sources": r["evidence_ids"], "cap": r["cap"]} for r in build()}))
    elif args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"records": len(replay(args.directory)), "exact_replay": True}))
