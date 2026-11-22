"""Generate one separate documentary field and a scoped comparison."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import receipt_chair as parent

HERE = parent.HERE
CAP = 104
TASKS = {
    "OPERATIVE": "Write at most 34 words recording the existing extension and the distinct willingness to work with Colombia's Government on further extension based on agreement between the parties. Cite [OPERATIVE].",
    "ADDITIONAL": "Write at most 57 words. Record the earlier ELN monitoring and verification authority. State the legal stage of possible EMC verification, Secretary-General confirmation with appropriate verification protocols, and taking into account the implementation update on resolution 2694. Cite [ADDITIONAL].",
    "BRAZIL": "Write at most 39 words. Identify the presiding representative speaking nationally for Brazil, the Colombian Government's stated priorities, and Brazil's hope for later Council authorization of EMC verification when sufficiently mature. Cite [BRAZIL].",
    "A3": "Write at most 38 words. State that Ghana spoke for the three African members, the particular EMC verification those members supported under the Secretary-General's conditions, and which communities their Ethnic Chapter commitment concerns. Cite [A3].",
    "overlap": "Write at most 30 words about the limited overlap between Brazil and the African members on a possible future role for EMC verification and whether there was an actual grant of authority. The conditions belong in their separately attributed fields. Cite [BRAZIL, A3, ADDITIONAL].",
}
SOURCES = {"ADDITIONAL", "BRAZIL", "A3"}


def plan():
    rows = list(parent.planned())
    for field, task in TASKS.items():
        keys = SOURCES if field == "overlap" else {field}
        source, = [r for r in rows if set(r["evidence_ids"]) == keys]
        system, user = source["messages"]
        content = json.loads(user["content"])
        content["task"] = ("Write the requested field of a retrospective Council record. Use the documentary cards as evidence. "
                           "Assume the other fields are written separately. End when this requested field is complete. " + task)
        yield {**source, "id": field, "cap": CAP,
               "messages": [system, {**user, "content": json.dumps(content, ensure_ascii=False)}]}


def locks():
    return {**parent.locks(), Path(__file__).name: parent.runner.digest(Path(__file__)),
            "whole_packet_results": parent.runner.digest(HERE / "receipt-evidence/results.json")}


def episode(generate):
    return [{"family": "colombia-documentary-fields", "final": generate(list(plan()))}]


def replay(directory):
    from transformers import AutoTokenizer

    read = lambda path: json.loads(path.read_text())
    launch = read(directory / "launch.json")
    end = read(directory / "complete.json")
    file = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    assert launch["sha256"] == locks() and end["transcript_sha256"] == parent.runner.digest(file)
    assert end["final_records_sha256"] == parent.runner.digest(final)
    rows = {r["id"]: r for r in map(json.loads, file.read_text().splitlines())}
    outputs = read(final)["colombia-documentary-fields"]
    assert len(rows) == len(outputs) == end["records"] == len(TASKS)
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    for request in plan():
        row = rows[request["id"]]
        assert all(row[key] == value for key, value in request.items())
        assert row["input_ids"] == parent.runner.encode(tok, request)
        ids = row["output_ids"]
        assert 0 < len(ids) <= CAP and eos not in ids[:-1] and row["ended"] == (ids[-1] == eos)
        assert outputs[row["id"]] == row["output"] == tok.decode(ids, skip_special_tokens=True).strip()
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({row["id"]: row["evidence_ids"] for row in plan()}, indent=2))
    elif args.mode == "run":
        with patch.multiple(parent.runner, episode=episode, locks=locks):
            parent.runner.run(args.model, args.directory)
    else:
        print(json.dumps({"records": len(replay(args.directory)), "exact_replay": True}, indent=2))
