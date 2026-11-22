"""Write local national accounts and keep the official public record fixed."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from mali_request_writer import MALI, ROOT, locks as source_locks, runner
from mali_request_writer_review import DOCKET

FAMILY = "mali-protected-record-components"
CAP = 70
SYSTEM = (
    "Write one factual sentence, at most 22 words, for the historical record. Use only your source block. "
    "Do not give any vote tally, formal outcome or Council authorization. Keep the speaker and the actor described distinct. "
    "Give no title, notes or commentary. End with the source ID in square brackets."
)
TASKS = {
    "french-uae": "Who explained what the co-penholders sought to achieve, including both the peace agreement and drawdown objectives?",
    "russia": "What concern did Russia raise about how the previous sanctions approach treated Mali's transitional Government?",
    "france-after": "What objection did France raise about discussion of the separate Russian proposal?",
}
PUBLIC_PARTS = {
    "primary-disposition": ["status-638"],
    "alternative-disposition": ["status-639"],
    "primary-text": ["status-638"],
    "alternative-text": ["status-639"],
    "overlap": ["status-638", "status-639"],
    "disagreement": ["status-638", "status-639"],
    "distinct-acts": ["status-638", "status-639"],
    "authority": ["status-638", "status-639"],
}
PUBLIC = (
    "On 30 August 2023 [docket], France and the UAE's S/2023/638 proposed renewing sanctions and extending the Panel of Experts. "
    "It failed 13–1–1 owing to Russia's permanent-member veto. France voted in favour [status-638].\n\n"
    "Russia's separate draft S/2023/639 proposed a final extension and immediate dissolution of the Panel. "
    "It failed 1–1–13 for insufficient votes in favour. Russia voted yes, Japan voted no, and France abstained [status-639].\n\n"
    "Both drafts proposed a temporary sanctions extension. They differed over the Panel's continuation and whether the extension "
    "would be final. Neither draft was adopted or created authority [status-638, status-639]."
)


def blocks():
    return {r["id"]: r["text"] for r in json.loads(MALI.read_text())["evidence"]}


def requests():
    source = blocks()
    for name, action in TASKS.items():
        body = {"task": action, "evidence": {name: source[name]}}
        yield {"id": name, "evidence_ids": [name], "seen": [], "cap": CAP,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]}


def locks():
    return {**source_locks(), str(Path(__file__).resolve().relative_to(ROOT)): runner.digest(Path(__file__))}


def check():
    assert DOCKET.startswith("The Council voted on S/2023/638 and S/2023/639 on 30 August 2023")
    rubric = {r["id"]: r for r in json.loads(MALI.read_text())["rubric"]}
    assert sum(rubric[k]["weight"] for k in PUBLIC_PARTS) == 56
    assert 3 * 22 + len(PUBLIC.split()) <= 165
    outputs = list(requests())
    assert len(outputs) == 3 and all(len(r["evidence_ids"]) == 1 for r in outputs)
    return {"calls": len(outputs), "public_words": len(PUBLIC.split()), "public_points": 56}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def replay(directory, verify_tokens=False):
    launch = json.loads((directory / "launch.json").read_text())
    end = json.loads((directory / "complete.json").read_text())
    trace = directory / "transcript.jsonl"
    assert launch["sha256"] == locks() and end["transcript_sha256"] == runner.digest(trace)
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == end["records"] == 3
    tokenizer = None
    if verify_tokens:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
        eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    for row, request in zip(rows, requests(), strict=True):
        assert all(row[k] == v for k, v in request.items())
        if tokenizer is not None:
            ids = row["output_ids"]
            assert runner.encode(tokenizer, request) == row["input_ids"]
            assert 0 < len(ids) <= CAP and eos not in ids[:-1]
            assert (ids[-1] == eos) == row["ended"]
            assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["output"]
    finals = directory / "final-records.json"
    assert end["final_records_sha256"] == runner.digest(finals)
    assert json.loads(finals.read_text()) == {FAMILY: {r["id"]: r["output"] for r in rows}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps(check(), indent=2))
    elif args.mode == "run":
        if args.directory is None or args.model is None:
            cli.error("run requires directory and model")
        check()
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory, verify_tokens=True), indent=2, ensure_ascii=False))
